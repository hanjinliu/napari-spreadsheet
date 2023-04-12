"""Points layer specific functions."""

from __future__ import annotations

from typing import Sequence
from functools import singledispatch
import pandas as pd
import napari
from napari.layers import Points, Shapes, Vectors, Layer
from tabulous import TableViewerWidget
from tabulous.color import normalize_color
from tabulous.widgets import SpreadSheet


@singledispatch
def layer_to_dataframe(layer: Layer, axis_labels) -> pd.DataFrame:
    """Convert layer state to a pandas DataFrame."""
    raise NotImplementedError


@singledispatch
def layer_to_spreadsheet(
    layer: Layer, table_viewer: TableViewerWidget
) -> SpreadSheet:
    """Convert layer state to a tabulous SpreadSheet widget."""
    raise NotImplementedError


@singledispatch
def spreadsheet_to_layer(
    layer: Layer,
    spreadsheet: SpreadSheet,
):
    """Convert a tabulous SpreadSheet widget to a napari layer."""
    raise NotImplementedError


@layer_to_dataframe.register
def points_to_dataframe(
    layer: Points,
    axis_labels: Sequence[str] = None,
) -> pd.DataFrame:
    data = layer.data
    if axis_labels is None:
        viewer = napari.current_viewer()
        axis_labels = [
            f"data_{a}"
            for a in viewer.dims.axis_labels[-layer.ndim :]  # noqa: E203
        ]
    dict_ = {}
    for i, axis_label in enumerate(axis_labels):
        dict_[axis_label] = data[:, i]
    dict_["face_color"] = [
        normalize_color(x * 255).html for x in layer.face_color
    ]
    dict_["edge_color"] = [
        normalize_color(x * 255).html for x in layer.edge_color
    ]
    dict_["edge_width"] = layer.edge_width
    dict_["size"] = layer.size[:, 0]
    return pd.DataFrame(dict_)


@layer_to_dataframe.register
def shapes_to_dataframe(
    layer: Shapes,
    axis_labels: Sequence[str] = None,
) -> pd.DataFrame:
    dict_ = {}
    dict_["face_color"] = [
        normalize_color(x * 255).html for x in layer.face_color
    ]
    dict_["edge_color"] = [
        normalize_color(x * 255).html for x in layer.edge_color
    ]
    dict_["edge_width"] = layer.edge_width
    return pd.DataFrame(dict_)


@layer_to_dataframe.register
def vectors_to_dataframe(
    layer: Vectors,
    axis_labels: Sequence[str] = None,
) -> pd.DataFrame:
    data = layer.data
    if axis_labels is None:
        viewer = napari.current_viewer()
        axis_labels = [
            f"data_{a}"
            for a in viewer.dims.axis_labels[-layer.ndim :]  # noqa: E203
        ]
    vec_labels = [f"{a}_vec" for a in axis_labels]
    dict_ = {}
    for i, axis_label in enumerate(axis_labels):
        dict_[axis_label] = data[:, 0, i]
    for i, vec_label in enumerate(vec_labels):
        dict_[vec_label] = data[:, 1, i]
    dict_["edge_color"] = [
        normalize_color(x * 255).html for x in layer.edge_color
    ]
    return pd.DataFrame(dict_)


def _set_background_color(
    table: SpreadSheet, name: Sequence[str] = ("face_color", "edge_color")
):
    for n in name:
        table[n].background_color.set(lambda x: x)
        table[n].background_color.set_opacity(0.5)


@layer_to_spreadsheet.register
def points_to_spreadsheet(
    layer: Points,
    table_viewer: TableViewerWidget,
):
    """Convert a points layer to a tabulous table."""
    df = layer_to_dataframe(layer)
    table = table_viewer.add_spreadsheet(df, name=layer.name, dtyped=True)
    _set_background_color(table)
    table.undo_manager.clear()
    return table


@layer_to_spreadsheet.register
def shapes_to_spreadsheet(
    layer: Shapes,
    table_viewer: TableViewerWidget,
):
    """Convert a shapes layer to a tabulous table."""
    df = layer_to_dataframe(layer)
    table = table_viewer.add_spreadsheet(df, name=layer.name, dtyped=True)
    _set_background_color(table)
    table.undo_manager.clear()
    return table


@layer_to_spreadsheet.register
def vectors_to_spreadsheet(
    layer: Vectors,
    table_viewer: TableViewerWidget,
):
    """Convert a vector layer to a tabulous table."""
    df = layer_to_dataframe(layer)
    table = table_viewer.add_spreadsheet(df, name=layer.name, dtyped=True)
    _set_background_color(table, name=("edge_color",))
    table.undo_manager.clear()
    return table


@spreadsheet_to_layer.register
def spreadsheet_to_points(
    layer: Points,
    table: SpreadSheet,
):
    df = table.data
    cols = df.columns[: layer.ndim]
    layer.data = df[cols].to_numpy()
    layer.face_color = df["face_color"].to_list()
    layer.edge_color = df["edge_color"].to_list()
    layer.size = df["size"].to_numpy()


@spreadsheet_to_layer.register
def spreadsheet_to_shapes(
    layer: Shapes,
    table: SpreadSheet,
):
    df = table.data
    layer.face_color = df["face_color"].to_list()
    layer.edge_color = df["edge_color"].to_list()


@spreadsheet_to_layer.register
def spreadsheet_to_vectors(
    layer: Vectors,
    table: SpreadSheet,
):
    df = table.data
    cols = df.columns[: layer.ndim * 2]
    layer.data = df[cols].to_numpy().reshape(-1, 2, layer.ndim)
    layer.edge_color = df["edge_color"].to_list()
