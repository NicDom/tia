"""Some utility functions for TIA."""
from typing import Any
from typing import List
from typing import Optional
from typing import Type
from typing import Union

import os
import pathlib

import orjson
from pydantic.types import DirectoryPath
from pydantic.types import FilePath


def create_directory(path: Union[pathlib.Path, str]) -> DirectoryPath:
    """Creates recursively the given directory under `path`.

    Args:
        path (str): Path of the directory, we want to create.

    Returns:
        DirectoryPath: The path.
    """
    path = pathlib.Path(path)
    if not path.is_dir():
        path.mkdir(parents=True, exist_ok=False)
    return path


def orjson_load(filename: FilePath) -> Any:
    """Returns data of the file under `filename` using `orjson.loads`.

    Args:
        filename (FilePath): Path to the file, whose data we want to load

    Returns:
        Any: A dictionary with the data of the file.
    """
    # want to load class from file immediately
    with open(filename) as f:
        data = f.read()
    return orjson.loads(data)


def file2class(cls: Type[Any], file: FilePath) -> Any:
    """Returns an instance of `cls` using the data in `file`.

    Args:
        cls (AnyObject): The class, of which we want to create an instance.
        file (FilePath): The FilePath of the file.

    Returns:
        Any: An instance of cls.
    """
    return cls(**orjson_load(file))


def columns(table: List[List[Any]]) -> List[List[Any]]:
    """Returns a list with the columns of a table.

    Args:
        table (List[List[Any]]): The table. Needs to be a n x m matrix.

    Returns:
        List[List[Any]]: The columns of the table.

    Raises:
        ValueError: if `table` is no n x m matrix.
    """
    for i in range(len(table)):
        if len(table[0]) != len(table[i]):
            raise (ValueError("Table needs to be a n x m matrix."))
    row_iter = range(len(table))
    col_iter = range(len(table[0]))
    return [[table[row][col] for row in row_iter] for col in col_iter]


def delete_file(filepath: Union[pathlib.Path, str]) -> Optional[str]:
    """Deletes the file given by `filepath`.

    Args:
        filepath (Union[pathlib.Path, str]): Path to the file to be deleted.

    Returns:
        str: The error message, if the file could not be deleted.
    """
    # Try to delete the file
    try:
        os.remove(filepath)
        return None
    except OSError as e:  # catch exception
        # print("Error: %s - %s." % (e.filepath, e.strerror))
        return str(f"Error: {e.filename} - {e.strerror}.")
