from __future__ import annotations

from typing import Callable, Generic, TypeVar
from abc import abstractmethod
from contextlib import contextmanager
from napari.layers import Points, Layer
from tabulous.color import normalize_color
from tabulous.widgets import SpreadSheet
from ._conversion import (
    layer_to_dataframe,
    spreadsheet_to_layer,
)


_F = TypeVar("_F", bound=Callable)
_L = TypeVar("_L", bound=Layer)


def _check_if_blocked(func: _F) -> _F:
    def fn(self: _LayerLinker, *args, **kwargs):
        if self._is_blocked:
            return
        with self.blocked():
            return func(self, *args, **kwargs)

    return fn


def get_linker(layer: Layer, sheet: SpreadSheet) -> _LayerLinker:
    if isinstance(layer, Points):
        return PointsLinker.prepare(layer, sheet)
    else:
        raise NotImplementedError(
            f"Linker not implemented for {type(layer).__name__} layer."
        )


class _LayerLinker(Generic[_L]):
    def __init__(self, layer: _L, sheet: SpreadSheet):
        self._layer = layer
        self._sheet = sheet
        self._is_blocked = False

    @classmethod
    def prepare(cls, layer: _L, sheet: SpreadSheet):
        self = cls(layer, sheet)
        self.sync_sheet()
        self.link()
        return self

    @contextmanager
    def blocked(self):
        _was_blocked = self._is_blocked
        self._is_blocked = True
        try:
            yield
        finally:
            self._is_blocked = _was_blocked

    @abstractmethod
    def link(self):
        """Link the layer and the spreadsheet."""

    @abstractmethod
    def unlink(self):
        """Unlink the layer and the spreadsheet."""

    def sync_sheet(self):
        """Sync the spreadsheet with the layer."""
        df = layer_to_dataframe(self._layer)
        self._sheet.data = df


class PointsLinker(_LayerLinker[Points]):
    def link(self):
        self._layer.events.data.connect(self._on_data_change)
        self._layer.events.size.connect(self._on_size_change)
        self._layer.events.face_color.connect(self._on_face_color_change)
        self._layer.events.edge_color.connect(self._on_edge_color_change)
        self._sheet.events.data.connect(self._on_sheet_data_change)

    def unlink(self):
        self._layer.events.data.disconnect(self._on_data_change)
        self._layer.events.size.disconnect(self._on_size_change)
        self._layer.events.face_color.disconnect(self._on_face_color_change)
        self._layer.events.edge_color.disconnect(self._on_edge_color_change)
        self._sheet.events.data.disconnect(self._on_sheet_data_change)

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
            try:
                spreadsheet_to_layer(self._layer, self._sheet)
            except Exception as e:
                self.sync_sheet()
                raise e
