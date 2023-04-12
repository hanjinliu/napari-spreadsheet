from pathlib import Path
from typing import Sequence, Union

PathLike = str
PathOrPaths = Union[PathLike, Sequence[PathLike]]


def get_reader(path: PathOrPaths):
    if isinstance(path, (str, Path)):
        if Path(path).suffix in (".txt", ".dat", ".csv", ".xlsx"):
            return open_table_data

    return None


def open_table_data(path: PathOrPaths):
    """Open a table data file in a docked tabulous widget."""

    from ._widget import MainWidget

    if not isinstance(path, list):
        path = [path]
    for p in path:
        MainWidget.open_table_data(p)
    return [(None,)]
