import napari

from napari_spreadsheet import MainWidget
from numpy.testing import assert_allclose


def test_points_conversion(make_napari_viewer):
    viewer: napari.Viewer = make_napari_viewer()
    wdt = MainWidget(viewer)

    layer = viewer.add_points([[0, 0], [0, 1], [1, 0]])
    wdt.layer_to_spreadsheet(layer)
    wdt.spreadsheet_to_layer()


def test_shapes_conversion(make_napari_viewer):
    viewer: napari.Viewer = make_napari_viewer()
    wdt = MainWidget(viewer)

    layer = viewer.add_shapes([[0, 0], [0, 1], [1, 0], [1, 1]])
    wdt.layer_to_spreadsheet(layer)
    wdt.spreadsheet_to_layer()


def test_vectors_conversion(make_napari_viewer):
    viewer: napari.Viewer = make_napari_viewer()
    wdt = MainWidget(viewer)

    layer = viewer.add_vectors([[[1, 1], [1, 1]]])
    wdt.layer_to_spreadsheet(layer)
    wdt.spreadsheet_to_layer()


def test_points_link_unlink(make_napari_viewer):
    viewer: napari.Viewer = make_napari_viewer()
    wdt = MainWidget(viewer)

    layer = viewer.add_points([[0, 0], [0, 1], [1, 0]])
    wdt.layer_to_spreadsheet(layer)
    table = wdt._table_viewer.current_table
    wdt.link_spreadsheet_and_layer()
    table.cell[0, 0] = -1
    assert layer.data[0, 0] == -1
    wdt.unlink_spreadsheet_and_layer()
    assert layer.data[0, 0] == -1
    table.cell[0, 0] = -2
    assert layer.data[0, 0] == -1


def test_shapes_link_unlink(make_napari_viewer):
    viewer: napari.Viewer = make_napari_viewer()
    wdt = MainWidget(viewer)

    layer = viewer.add_shapes([[0, 0], [0, 1], [1, 0], [1, 1]])
    wdt.layer_to_spreadsheet(layer)
    table = wdt._table_viewer.current_table
    wdt.link_spreadsheet_and_layer()
    table.cell[0, 0] = "#FF0000"
    assert_allclose(layer.face_color[0], [1, 0, 0, 1])
    wdt.unlink_spreadsheet_and_layer()
    assert_allclose(layer.face_color[0], [1, 0, 0, 1])
    table.cell[0, 0] = "#00FF00"
    assert_allclose(layer.face_color[0], [1, 0, 0, 1])


def test_vectors_link_unlink(make_napari_viewer):
    viewer: napari.Viewer = make_napari_viewer()
    wdt = MainWidget(viewer)

    layer = viewer.add_vectors([[[1, 1], [1, 1]]])
    wdt.layer_to_spreadsheet(layer)
    table = wdt._table_viewer.current_table
    wdt.link_spreadsheet_and_layer()
    table.cell[0, 0] = -1
    assert layer.data[0, 0, 0] == -1
    wdt.unlink_spreadsheet_and_layer()
    assert layer.data[0, 0, 0] == -1
    table.cell[0, 0] = -2
    assert layer.data[0, 0, 0] == -1
