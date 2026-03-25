"""
src.data_platform.core.engine.spark

Purpose:
    - standardized Spark operations

Exposed API:
    - `start_spark()` - spin up spark session
    - `generate_default_schema()` - create a default schema (`StructType`) with column list
"""

from __future__ import annotations 
from typing import Mapping 
from pyspark.sql import SparkSession 
from pyspark.sql.types import StructType, StructField, StringType

from data_platform.core.utils.filesystem import read_configs

DEFAULT_SPARK_CONFIG: dict[str, str] = read_configs(source_system="core", config_type="system", name="spark.json")["default"]

def start_spark(
        app_name: str = "qbo-etl-local",
        master: str = "local[*]",
        extra_conf: Mapping[str, str] | None = None,
        log_level: str = "INFO"
) -> SparkSession:
    """
    Purpose:
        - create or retrieve a SparkSession using standardized project defaults

    Inputs:
        - `app_name`: Name shown in Spark UI / logs
        - `master`: Spark master URL, e.g., `local[*]` for all local cores
        - `extra_conf`: Optional config overrides/additions
        - `log_level`: SparkContext log level, e.g., INFO, WARN, ERROR
    
    Output:
        - SparkSession
    """
    conf = dict(DEFAULT_SPARK_CONFIG)
    if extra_conf:
        conf.update({k: str(v) for k, v in extra_conf.items()})

    builder = (
        SparkSession.builder
        .appName(app_name)
        .master(master)
    )
    for key, value in conf.items():
        builder = builder.config(key, value)
    
    spark = builder.getOrCreate()
    spark.sparkContext.setLogLevel(log_level)

    return spark

def generate_default_schema(columns: list[str]) -> StructType:
    """
    Purpose:
        - given a column list, generate default schema for StringType(), nullable=True
    """
    schema = StructType([
        StructField(x, StringType(), True) 
        for x in columns
    ])
    return schema