import tempfile
from pathlib import Path

import napari
from napari_spreadsheet import MainWidget
from napari_spreadsheet._reader import get_reader
import pandas as pd


def test_reader(make_napari_viewer):
    viewer: napari.Viewer = make_napari_viewer()
    wdt = MainWidget(viewer)
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        path = tmpdir / "test.csv"
        df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        df.to_csv(path)
        reader = get_reader(path)
        assert reader is not None
        reader(path)

        wdt._table_viewer.current_table.data.shape == (3, 2)
