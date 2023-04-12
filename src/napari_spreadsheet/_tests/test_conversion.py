import napari

from napari_spreadsheet import MainWidget


def test_points_conversion(make_napari_viewer):
    viewer: napari.Viewer = make_napari_viewer()
    wdt = MainWidget(viewer)

    layer = viewer.add_points([[0, 0], [0, 1], [1, 0]])
    wdt.layer_to_spreadsheet(layer)
    wdt.spreadsheet_to_layer(layer)


def test_shapes_conversion(make_napari_viewer):
    viewer: napari.Viewer = make_napari_viewer()
    wdt = MainWidget(viewer)

    layer = viewer.add_shapes([[0, 0], [0, 1], [1, 0], [1, 1]])
    wdt.layer_to_spreadsheet(layer)
    wdt.spreadsheet_to_layer(layer)


def test_vectors_conversion(make_napari_viewer):
    viewer: napari.Viewer = make_napari_viewer()
    wdt = MainWidget(viewer)

    layer = viewer.add_vectors([[[1, 1], [1, 1]]])
    wdt.layer_to_spreadsheet(layer)
    wdt.spreadsheet_to_layer(layer)
