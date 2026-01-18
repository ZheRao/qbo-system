from __future__ import annotations
import datetime as dt
from typing import TypedDict, Sequence, Optional

# task schedule schema contract
class FlattenTask(TypedDict):
    company: str
    start: str   # ISO date
    end: str     # ISO date
    out_path_pl: str
    out_path_gl: str

## hypter parameters
_LAST_DAY = {3: 31, 6: 30, 9: 30, 12: 31} # mapping exact date of quarter end for exact ending dates
_QUARTER_START_MONTHS = (1, 4, 7, 10)

def flatten_job_scheduler(
    companies: Sequence[str],
    pl_path: str ="",
    gl_path: str ="",
    scope: Optional[Sequence[int]] = None,
) -> list[FlattenTask]:
    """
    Create a list of tasks for partitioned flattening of PL/GL report, converting semi-structured JSON file into tabular format for Parquet storage, example:
        {
            "company": "xxx",
            "start": "2024-10-01",
            "end": "2024-12-31",
            "out_path_pl": "/path/to/silver/pl",
            "out_path_gl": "/path/to/silver/gl"
        }
    """
    # set default scope if not passed
    if not scope:
        scope = [2025, 2026]
    today = dt.date.today()
    tasks: list[FlattenTask] = []
    for company in companies:
        # because FY starts in November of last calender year, include the quarter that begins Oct 1 because the bronze filenames are quarter-based and start in October
        earlist_fy = min(scope)     
        start = dt.date(earlist_fy-1, 10, 1)    
        end = dt.date(earlist_fy-1, 12, 31)
        tasks.append({
            "company": company, 
            "start": start.isoformat(),
            "end": end.isoformat(),
            "out_path_pl": pl_path,
            "out_path_gl": gl_path
        })
        # create task for every quarter in the scope - skip quarters that hasn't come 
        for year in scope:  
            for month in _QUARTER_START_MONTHS:
                if dt.date(year, month, 1) > today: # skip creating this task if the intended quarter start date is after today - avoid extracting empty data
                    continue 
                start = dt.date(year, month, 1)
                end = dt.date(year, month+2, _LAST_DAY[month+2])
                tasks.append({
                    "company": company, 
                    "start": start.isoformat(),
                    "end": end.isoformat(),
                    "out_path_pl": pl_path,
                    "out_path_gl": gl_path
                })
    return tasks