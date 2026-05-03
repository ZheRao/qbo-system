"""
src.data_platform.core.utils.filesystem

Purpose:
    - common file read and write operations across all source systems

Exposed API:
    - `read_configs()` - given `source_system`, `config_type` and `name`, read and return the config file
    - `ensure_dir()` - ensures path exists, create if not
    - `atomic_write_bytes()` - generic atomic method for bytes
"""


from importlib.resources import files
import json
import os
import uuid 
from pathlib import Path
from typing import Any


def _validate_required_keys(
    config: dict[str,Any],
    required_shape: dict[str, Any],
    *,
    config_name: str,
    path: str=""
) -> None:
    """
    Input:
        - `config`: current config file being read and preparing for return for downstream programs' consumption
        - `required_shape`: documented expected shape of the config file (dictionary that includes all the keys, and placeholder values, usually 'true')
        - `config_name`: config type + config file name, used to provide context for error messages
        - `path`: the navigation path inside nested `config` and `required_shape` dictionaries
    Purpose:
        - validates that `config` contains all keys required by `required_shape`
    Note:
        - nested dictionaries in `required_shape` indicate nested required keys
        - non-dict values in `required_shape` mean: key must exist, but value shape is not checked yet
    """
    missing_keys = []

    # check every (key, value) pair inside required_shape template
    for key,expected_value in required_shape.items():
        current_path = f"{path}.{key}" if path else key

        if key not in config:
            missing_keys.append(current_path)
            continue 
        
        # if value of the current (key, value) pair in `required_shape` is nested dictionary, then drill inside it
        if isinstance(expected_value, dict):
            actual_value = config[key]

            # if the equivalent level from `config` is not nested dictionary (as `required_shape`), error
            if not isinstance(actual_value, dict):
                raise TypeError(
                    f"Invalid config structure for '{config_name}'.\n\n"
                    f"Expected '{current_path}' to be a nested object/dict,\n"
                    f"but got: {type(actual_value).__name__}"
                )
            
            # validate nested values inside the current key, value pair
            _validate_required_keys(
                config = actual_value,
                required_shape = expected_value,
                config_name = config_name,
                path=current_path
            )
    # if there are any missing keys in the traversal, error
    if missing_keys:
        raise ValueError(
            (
                f"Missing required config keys for '{config_name}'.\n\n"
                f"Missing keys:\n"
                + "\n".join(f"  - {key}" for key in missing_keys)
            )
        )


def read_configs(source_system: str, config_type: str, name: str) -> dict:
    """
    Purpose:
        - standardized methods for reading config files

    Input:
        - `source_system`: the data source system e.g., "qbo"
        - `config_type`: the config type e.g., "contracts"
        - `name`: the name of the config file e.g., "facts.json"

    Returns:
        - parsed JSON config as dictionary
    
    Raises:
        - FileNotFoundError:
            - if the config file does not exist
        - ValueError:
            - if the JSON is invalid
        - validation errors:
            - if the JSON file is not the expected shape
    """
    # define config file path and load it
    package = (
        f"data_platform.sources.{source_system}.json_configs" 
        if source_system.lower() != "core" 
        else "data_platform.core.json_configs"
    )
    relative_path = f"{config_type}/{name}"
    path = files(package).joinpath(relative_path)
    # error if file not exist
    if not path.is_file():
        raise FileNotFoundError(
            (
                f"Missing config file.\n\n"
                f"Expected config:\n"
                f"  source_system = '{source_system}'\n"
                f"  config_type  = '{config_type}'\n"
                f"  name         = '{name}'\n\n"
                f"Expected location:\n"
                f"  {package.replace('.', '/')}/{relative_path}\n\n"
                f"Please create the JSON config file at the expected location."
            )
        )
    # error if file cannot be loaded
    try:
        config = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        raise ValueError(
            (
                f"Invalid JSON config file.\n\n"
                f"Config location:\n"
                f"  {package.replace('.', '/')}/{relative_path}\n\n"
                f"JSON parsing error:\n"
                f"  {str(e)}"
            )
        ) from e
    
    # validate config shape
    schema_path = files(package).joinpath("config_schema.json")
    if not schema_path.is_file():
        raise FileNotFoundError("Missing config_schema.json file, required to validate the shape of config file being read")
    schema = json.loads(schema_path.read_text())
    if relative_path in schema:
        _validate_required_keys(
            config = config,
            required_shape = schema[relative_path],
            config_name = relative_path
        )
    else:
        print(f"WARNING: schema for {relative_path} is not defined in expected config schema file: 'config_schema.json'")
    return config

def ensure_dir(path: Path|str) -> None:
    """
    Purpose:
        - ensure the path exists
    """
    if isinstance(path, str): path=Path(path)
    path.mkdir(parents=True, exist_ok=True)

def _atomic_replace(src: Path, dst: Path) -> None:
    """
    Purpose:
        - atomically replace temporary file to actual file
    """
    os.replace(src, dst)

def atomic_write_bytes(dst: Path, data: bytes) -> None:
    """
    Purpose:
        - atomically write bytes to `dst`
        - write a temp file in the same directory, fsyncing it, then replacing the destination
    Input:
        - `dst`: destination path (including the filename at the end)
        - `data`: serialized bytes
    """
    ensure_dir(dst.parent)
    tmp = dst.with_name(f".{dst.name}.{uuid.uuid4().hex}.tmp")

    try:
        with open(tmp, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        _atomic_replace(src=tmp, dst=dst)
    except Exception as e:
        raise RuntimeError(f"Atomic writes failed for {dst}") from e 
    finally:    # clean up
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass    # silent clean up error


# for testing purposes
if __name__ == "__main__":
    print(read_configs(source_system="qbo", config_type="io", name="path.json"))