"""Tests `utils` module of TIA."""

from typing import Any
from typing import Dict

import json
import pathlib

import pytest

from tia.client import Client
from tia.utils import columns
from tia.utils import create_directory
from tia.utils import delete_file
from tia.utils import file2class


def test_create_directory(fake_filesystem: Any) -> None:
    """Creates the directory."""
    dir = pathlib.Path("some/")
    create_directory(dir)
    assert dir.is_dir()
    assert create_directory(dir) == dir
    other_dir = "other/"
    assert create_directory(other_dir) == pathlib.Path(other_dir)
    assert create_directory(other_dir).is_dir()


def test_file2class(fake_filesystem: Any, some_client: Dict[str, str]) -> None:
    """Creates class instance from a file."""
    dir = pathlib.Path("some/")
    filename = dir / "item"
    fake_filesystem.create_dir(dir)
    with open(filename, "w") as f:
        f.write(json.dumps(some_client))
    item = file2class(Client, filename)
    assert item == Client(**some_client)


def test_columns() -> None:
    """Returns columns of a n x m matrix."""
    table = [[1, 2, 3], [4, 5, 6]]
    assert columns(table) == [[1, 4], [2, 5], [3, 6]]


def test_columns_exception() -> None:
    """Raises ValueError if table is no n x m matrix."""
    table = [[1, 2, 3], [4, 5]]
    with pytest.raises(ValueError) as excinfo:
        columns(table)
    assert "n x m" in str(excinfo)


def test_delete_file(fake_filesystem: Any) -> None:
    """Deletes a file and catches exception."""
    assert isinstance(delete_file("does_not_exist"), str)
    path = pathlib.Path("file.txt")
    fake_filesystem.create_file(path)
    delete_file(path)
    assert not path.is_file()
