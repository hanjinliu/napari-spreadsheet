"""Points layer specific functions."""

from __future__ import annotations
from contextlib import contextmanager

from typing import Callable, Sequence, TypeVar
from functools import singledispatch
import pandas as pd
import napari
from napari.layers import Points, Shapes, Vectors, Layer
from tabulous import TableViewerWidget
from tabulous.color import normalize_color
from tabulous.widgets import SpreadSheet


_F = TypeVar("_F", bound=Callable)


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
    axis_labels: Sequence[str] | None = None,
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
    axis_labels: Sequence[str] | None = None,
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
    axis_labels: Sequence[str] | None = None,
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


class PointsLinker:
    def __init__(self, layer: Points, sheet: SpreadSheet):
        self._layer = layer
        self._sheet = sheet
        self._is_blocked = False

    @classmethod
    def prepare(cls, layer: Points, sheet: SpreadSheet):
        self = cls(layer, sheet)
        self.link()
        return self

    def link(self):
        self._layer.events.data.connect(self._on_data_change)
        self._layer.events.size.connect(self._on_size_change)
        self._layer.events.face_color.connect(self._on_face_color_change)
        self._layer.events.edge_color.connect(self._on_edge_color_change)
        self._sheet.events.data.connect(self._on_sheet_data_change)
        self._sheet.events.selections.connect(self._on_sheet_selected)

    def unlink(self):
        self._layer.events.data.disconnect(self._on_data_change)
        self._layer.events.size.disconnect(self._on_size_change)
        self._layer.events.face_color.disconnect(self._on_face_color_change)
        self._layer.events.edge_color.disconnect(self._on_edge_color_change)
        self._sheet.events.data.disconnect(self._on_sheet_data_change)
        self._sheet.events.selections.disconnect(self._on_sheet_selected)

    @contextmanager
    def blocked(self):
        _was_blocked = self._is_blocked
        self._is_blocked = True
        try:
            yield
        finally:
            self._is_blocked = _was_blocked

    def _check_if_blocked(func: _F) -> _F:
        def fn(self: PointsLinker, *args, **kwargs):
            if self._is_blocked:
                return
            with self.blocked():
                return func(self, *args, **kwargs)

        return fn

    @_check_if_blocked
    def _on_data_change(self, *_):
        data = self._layer.data
        if data.shape[0] != self._sheet.index.size:
            df = layer_to_dataframe(self._layer)
            self._sheet.data = df
        else:
            cols = self._sheet.columns[: self._layer.ndim]
            val = {}
            for i, col in enumerate(cols):
                val[col] = data[:, i].copy()
            with self._sheet.events.data.blocked():
                self._sheet.assign(val)

    @_check_if_blocked
    def _on_size_change(self, *_):
        with self._sheet.events.data.blocked():
            self._sheet.assign(size=self._layer.size[:, 0])

    @_check_if_blocked
    def _on_face_color_change(self, *_):
        with self._sheet.events.data.blocked():
            self._sheet.assign(
                face_color=[
                    normalize_color(x * 255).html
                    for x in self._layer.face_color
                ]
            )

    @_check_if_blocked
    def _on_edge_color_change(self, *_):
        with self._sheet.events.data.blocked():
            self._sheet.assign(
                edge_color=[
                    normalize_color(x * 255).html
                    for x in self._layer.edge_color
                ]
            )

    @_check_if_blocked
    def _on_sheet_data_change(self, *_):
        with self._sheet.events.data.blocked():
            spreadsheet_to_points(self._sheet, self._layer)

    @_check_if_blocked
    def _on_points_selected(self, *_):
        self._sheet.index.selected = self._layer.selected_data

    @_check_if_blocked
    def _on_sheet_selected(self, *_):
        selected_indices: set[int] = set()
        for sl in self._sheet.index.selected:
            selected_indices.update(range(sl.start, sl.stop))
        self._layer.selected_data = selected_indices
