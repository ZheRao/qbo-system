from __future__ import annotations

from typing import TypedDict, Literal, Iterator, Any, Dict, List, Tuple, Optional
import orjson

import logging

logger = logging.get_logger(__name__)



# ---------------------------------------------------------------------------------
# 1) TypedDicts / types
# ---------------------------------------------------------------------------------


class col_MetaData(TypedDict):
    Name: str
    Value: str 

class col_types(TypedDict):
    ColTitle: str 
    ColType: Literal["Date", "String", "Money"]
    MetaData: list[col_MetaData]




# ---------------------------------------------------------------------------------
# 2) core logic: report_col, crawler, flatten_report
# ---------------------------------------------------------------------------------



def report_col(col_meta:list[col_types], col_map:dict[str,str]) -> list[str]:
    """ 
        Extract and standardize all columns from a given report, prevent positional drift.

        args:    
            col_meta is the json_file["Columns"]["Column"] - list of meta data on report columns at the beginning of each QBO report
            col_map is the mapping dictionary from configuration file - "raw_name" : "standardized_name" pair

        If mapping is missing, presesrves raw_name and logs a warning

    """
    standardized_columns: list[str] = []
    missing_mappings = 0

    # iterate through all columns' meta data
    for i, meta in enumerate(col_meta):
        # extract raw column name from column meta data
        try:
            raw_name = meta["MetaData"][0]["Value"]
        except (KeyError, IndexError) as e:
            logger.error("report_col: malformed col_meta at index %d: %s", 
                         i, e, exc_info=True)
            # fall back raw_name
            raw_name = f"UNKNOWN_{i}"

        # find standardized mapping - if no match found, log it and fall back to raw_name as standardized_name
        standardized_name = col_map.get(raw_name)
        if standardized_name is None:
            missing_mappings += 1
            standardized_name = raw_name
            logger.warning("report_col: missing col_map entry for raw_name='%s' -> using raw_name",
                           raw_name)

        # append standardized column name into column list
        standardized_columns.append(standardized_name)

    # log entire column mapping process
    logger.info("report_col: extracted %d columns (%d missing mappings)",
                len(standardized_columns), missing_mappings)
    logger.debug("report_col: columns = %s", standardized_columns)

    return standardized_columns

def crawler(json_level:dict, cols:list[str], company:str, acc_info:tuple[str]=None) -> Iterator[dict]:
    """ 
        this recursive function crawls into each node, yield/return leaf nodes extracted values

        args:
            json_level  - current node level in the json object - next level = json_level["Rows"]["Row"]
            cols        - the top level column names extraction at the report-level
            company     - the company code for current report
            acc_info    - (acc_ID, acc_fullname) information from last layer
    """

    node_type = json_level.get("type")

    # ---------------------------------------------------------------------------------
    # leaf node case
    # ---------------------------------------------------------------------------------

    if node_type == "Data":
        rows = dict.fromkeys(cols)  # initialize all columns as None

        col_data_list = json_level.get("ColData")
        # length of data_list should match length of column names
        if len(col_data_list) != len(cols):
            logger.warning("crawler: ColData length mismatch. cols=%d, colData=%d company=%s",
                           len(cols), len(col_data_list), company)

        for i, col_name in enumerate(cols):
            # if there's a mismatch between length of col_names and col_list, break at end of col_list
            if i >= len(col_data_list):
                break
            
            value = col_data_list[i]    # i-th column value pairs - may contain 'id', 'value'
            val = value.get("value")    # actual column value of i-th column

            # non-empty values
            if val != '':
                if col_name == "DocNumber":     # DocNumber column requires adding company code at the beginning
                    rows[col_name] = "-".join([company, val])
                    continue
                else:
                    rows[col_name] = val

            # extract ID if present
            value_id = value.get("id", "")
            if value_id:
                if col_name == "TransactionType":
                    rows["TransactionID"] = company + value_id
                else:
                    rows[col_name+"ID"] = company + value_id
        
        # account info
        if acc_info:
            rows["AccID"] = company + acc_info[0]

            acc = acc_info[1]
            if len(acc) >= 7:   # assuming acc = account number (6 digits) + actual account name
                rows["AccNum"] = company + acc[:6]
                rows["AccName"] = acc[7:]    # 6-th position is white space
            else:
                logger.warning("unexpected account_info[1] format='%s' company='%s'",
                               acc, company)
                rows["AccNum"] = company + acc
                rows["AccName"] = "UNEXPECTED"
        else:
            logger.warning("crawler: leaf node with type='Data' but no acc_info present - records: %s - company %s",
                           col_data_list, company)

        # yield records
        logger.debug("crawler: yielded rows=%s", rows)
        yield rows
        return  # important: stop here for leaf


    # ---------------------------------------------------------------------------------
    # non-leaf case: update acc_info when available and recurse 
    # ---------------------------------------------------------------------------------


    # determine whether the account information should be recorded 
    header = json_level.get("Header")
    if isinstance(header, dict):
        coldata = header.get("ColData", [])
        if coldata:
            coldata = coldata[0]
            if "id" in coldata and "value" in coldata:
                acc_info = (coldata["id"], coldata["value"])

    # keep crawling forward if the next level exists
    data = json_level.get("Rows", {})
    if "Row" in data:
        for node_path in data["Row"]:
            yield from crawler(json_level=node_path,cols=cols,company=company,acc_info=acc_info)


def flatten_report(data:dict, company:str, col_map: dict[str, str]) -> Iterator[dict]:
    """
        crawler starter: faltten one JSON report dict for a single company

        this glues together:
            1. column extraction (report_col)
            2. recursive crawling (crawler) from top-level Rows.Row
    """
    columns_section = data.get("Columns", {})
    col_meta = columns_section.get("Column", [])

    if not col_meta:
        logger.warning("flatten_report: no Columns.Column meta data found, company = %s", company)  # add quarter here to better identify the anomaly 
        return # stop the generator

    cols = report_col(col_meta, col_map)

    row_section = data.get("Rows", {})
    top_rows = row_section.get("Row", [])
    
    if not top_rows:
        logger.info("flatten_report: no data rows (Rows.Row empty). company=%s, cols=%d",
                    company, len(cols))
        return # stop the generator
    
    logger.info("flatten_report: starting flatten. company=%s top_rows=%d cols=%d",
                company, len(top_rows), len(cols))

    # this inner function stops flatten_report from being a generator, instead, it is just a regular function that returns a generator
    def _iter() -> Iterator[dict]:
        for row in top_rows:
            yield from crawler(row, cols, company)
        
    return _iter()

def flatten_partition(it: Iterator[dict], col_map: dict[str, str]) -> Iterator[dict]:
    """
        Iterate through one partition - and act on individual jobs (one JSON file),
        records stats, and initiate flatten_report

        Each 'task' is expected to be a dict like:
            {
                "company": "<company code>",
                "out_path": "<path/to/json/file>",
                "start": "2025-10-01"
            }
    """
    reports_processed = 0
    records_emitted = 0

    for task in it:
        company = task["company"]
        out_path = task["out_path"]
        period = task["start"]

        reports_processed += 1

        try:
            with open(out_path, "rb") as f:
                raw_bytes = f.read()

            data = orjson.loads(raw_bytes)

            if not data:
                logger.info("flatten_partition: empty data for company=%s period=%s",
                            company, period)
                continue

            logger.info("flatten_partition: processing report #%d company=%s period=%s",
                        reports_processed, company, period)

            for row in flatten_report(data, company, col_map):
                records_emitted += 1
                yield row

        except Exception as e:
            logger.error("flatten_partition: error reading JSON file for company=%s period=%s error=%s",
                         company, period, e, exc_info=True)
            continue

    logger.info("flatten_partition: partition complete. reports=%d records=%d",
                reports_processed, records_emitted)
