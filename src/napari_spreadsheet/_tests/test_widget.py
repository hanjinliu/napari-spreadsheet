import napari

from napari_spreadsheet import MainWidget


def test_layer_features(make_napari_viewer):
    viewer: napari.Viewer = make_napari_viewer()
    layer = viewer.add_points(
        [[0, 0], [0, 1], [1, 0]],
        features={"a": [0, 0, 1], "b": ["x", "y", "z"]},
    )

    wdt = MainWidget(viewer)
    wdt.load_layer_features(layer)
    assert wdt._table_viewer.current_table.data.shape == (3, 2)
    wdt._table_viewer.current_table.cell[0, 0] = -1
    wdt.update_layer_features(layer)
    assert layer.features.iloc[0, 0] == -1


def test_popup(make_napari_viewer):
    viewer: napari.Viewer = make_napari_viewer()
    wdt = MainWidget(viewer)
    wdt.popup_current_table()


def test_open_new_widget(make_napari_viewer):
    viewer: napari.Viewer = make_napari_viewer()
    wdt = MainWidget(viewer)
    wdt.open_new_widget()
