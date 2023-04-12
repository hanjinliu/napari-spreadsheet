from __future__ import annotations

import weakref
from typing import TYPE_CHECKING, TypeVar

from qtpy import QtWidgets as QtW
from tabulous import TableViewerWidget as _TableViewerWidget
from tabulous import __version__ as tabulous_version

from . import _utils
from ._types import LayerWithFeatures, get_layers_with_features

if TYPE_CHECKING:
    import napari
    from napari.layers import Layer
    from tabulous.widgets import SpreadSheet
    from ._linker import _LayerLinker

    _L = TypeVar("_L", bound=Layer)


class TableViewerWidget(_TableViewerWidget):
    """The tabulous table viewer widget for napari."""

    @property
    def console(self):
        raise AttributeError("console is not available in this widget.")


_void = object()


class LayerSource:
    """A weak reference to a napari layer."""

    def __init__(self, layer: Layer):
        self._layer = weakref.ref(layer)
        self._linker: weakref.ReferenceType[_LayerLinker] | None = None

    def __repr__(self) -> str:
        layer = self.layer
        clsname = type(self).__name__
        if layer is None:
            return f"{clsname}(<deleted>)"
        return f"{clsname}({layer})"

    @property
    def layer(self) -> Layer:
        return self._layer()

    @property
    def linker(self) -> _LayerLinker | None:
        if self._linker is None:
            return None
        return self._linker()

    @linker.setter
    def linker(self, linker: _LayerLinker | None):
        if linker is None:
            if linker := self.linker:
                linker.unlink()
            self._linker = None
        else:
            self._linker = weakref.ref(linker)


_SOURCE = "spreadsheet-source"


class MainWidget(QtW.QWidget):
    _current_widget: TableViewerWidget | None = None

    def __init__(
        self, napari_viewer: napari.Viewer, *, new_sheet: bool = True
    ):
        super().__init__()
        self._viewer = napari_viewer

        from tabulous._utils import init_config

        with init_config() as cfg:
            cfg.window.nonmain_style = True
            col = cfg.window.theme.split("-")[1]
            cfg.window.theme = f"{napari_viewer.theme}-{col}"
            self._table_viewer = TableViewerWidget(show=False)

        self._init_ui()

        self.__class__._current_widget = self._table_viewer

        # some napari specific settings...
        self._table_viewer.toolbar.visible = True
        try:
            tbar = self._table_viewer._qwidget._toolbar
            btn = tbar._child_widgets["Home"]._buttons[4]
            btn.setEnabled(False)
            self._table_viewer.keymap.unregister("Ctrl+Shift+C")
        except Exception:
            pass

        if new_sheet:
            self._table_viewer.add_spreadsheet()

    @classmethod
    def open_table_data(cls, path: str):
        if cls._current_widget is None:
            import napari

            viewer = napari.current_viewer()
            if viewer is None:
                raise RuntimeError("No viewer is available.")
            self = cls(viewer, new_sheet=False)
            viewer.window.add_dock_widget(self, name="Spreadsheet")
            table_viewer = self._table_viewer
        else:
            table_viewer = cls._current_widget
        table_viewer.open(path, type="spreadsheet")
        return None

    def popup_current_table(self):
        """Popup current table."""
        table = self._table_viewer.current_table
        if table is None:
            return
        table.view_mode = "popup"
        return None

    def load_layer_features(self, layer: LayerWithFeatures = _void):
        """Load layer features as a spreadsheet from the napari viewer."""
        table = self._table_viewer.current_table
        if table is None:
            return
        if layer is _void:
            layer = _utils.get_layer_by_dialog(
                parent=self, choices=get_layers_with_features
            )
        if layer is not None:
            self._table_viewer.add_spreadsheet(
                layer.features,
                name=layer.name,
                metadata={_SOURCE: LayerSource(layer)},
                dtyped=True,
            )

    def update_layer_features(self, layer: LayerWithFeatures = _void):
        """Update napari layer features with the current spreadsheet."""
        table = self._table_viewer.current_table
        if table is None:
            return
        if layer is _void:
            layer = _get_source_with_features(table)
            if layer is None:
                layer = _utils.get_layer_by_dialog(
                    parent=self, choices=get_layers_with_features
                )
        if layer is not None:
            layer.features = table.data
            layer.refresh()
        return None

    def open_new_widget(self):
        """Open a new widget."""
        if tabulous_version >= "0.5.0":
            from tabulous._utils import init_config

            with init_config() as cfg:
                cfg.window.nonmain_style = True
                col = cfg.window.theme.split("-")[1]
                cfg.window.theme = f"{self._viewer.theme}-{col}"
                table_viewer = TableViewerWidget(show=False)
        else:
            table_viewer = TableViewerWidget(show=False)

        self._viewer.window.add_dock_widget(table_viewer, name="Spreadsheet")
        return None

    def send_table_to_namespace(self, identifier: str = _void):
        """Send data of the current spreadsheet to napari console."""
        if identifier is _void:
            identifier = _utils.get_str_by_dialog(
                label="identifier", value="df", parent=self
            )

        if identifier is not None:
            data = self._table_viewer.current_table.data
            self._viewer.update_console({identifier: data})
        return None

    def layer_to_spreadsheet(self, layer: Layer = _void):
        from ._conversion import layer_to_spreadsheet

        if layer is _void:
            layer = _utils.get_layer_by_dialog(
                parent=self, choices=_utils.get_layers
            )
            if layer is None:
                return
        sheet = layer_to_spreadsheet(layer, self._table_viewer)
        sheet.metadata[_SOURCE] = LayerSource(layer)

    def spreadsheet_to_layer(self, layer: Layer = _void):
        from ._conversion import spreadsheet_to_layer

        table = self._table_viewer.current_table
        if layer is _void:
            layer = _get_source(table)
            if layer is None:
                layer = _utils.get_layer_by_dialog(
                    parent=self, choices=_utils.get_layers
                )
                if layer is None:
                    return
        spreadsheet_to_layer(layer, table)

    def link_spreadsheet_and_layer(self, layer: Layer = _void):
        from ._linker import get_linker

        table = self._table_viewer.current_table
        if layer is _void:
            layer = _get_source(table)
            if layer is None:
                raise RuntimeError("No layer is available.")
        linker = get_linker(layer, table)
        source: LayerSource = table.metadata[_SOURCE]
        source.linker = linker

    def unlink_spreadsheet_and_layer(self):
        table = self._table_viewer.current_table
        source: LayerSource = table.metadata[_SOURCE]
        source.linker = None

    def _init_ui(self):
        # buttons
        _header = QtW.QWidget()
        _layout = QtW.QHBoxLayout()
        _layout.setContentsMargins(0, 0, 0, 0)
        # fmt: off
        buttons: list[QtW.QPushButton] = [
            _utils.create_menubutton(
                "Layers",
                [
                    ("Layer features -> SpreadSheet", self.load_layer_features),  # noqa
                    ("SpreadSheet -> Layer features", self.update_layer_features),  # noqa
                    ("Layer state -> SpreadSheet", self.layer_to_spreadsheet),  # noqa
                    ("SpreadSheet -> Layer state", self.spreadsheet_to_layer),  # noqa
                    ("Link layer", self.link_spreadsheet_and_layer),
                    ("Unlink layer", self.unlink_spreadsheet_and_layer)
                ]
            ),
            _utils.create_button(self.popup_current_table, name="Popup"),  # noqa
            _utils.create_button(self.send_table_to_namespace, name="Table to\nConsole"),  # noqa
            _utils.create_button(self.open_new_widget, name="New\nWidget"),  # noqa
        ]
        # fmt: on
        for btn in buttons:
            _layout.addWidget(btn)
        max_height = max(btn.sizeHint().height() for btn in buttons)
        for btn in buttons:
            btn.setFixedHeight(max_height)
        _header.setLayout(_layout)

        _main_layout = QtW.QVBoxLayout()
        self._table_viewer._qwidget.insertWidget(0, _header)
        # _main_layout.addWidget(_header)
        _main_layout.addWidget(self._table_viewer.native)
        self.setLayout(_main_layout)
        return None


def _get_source_with_features(table: SpreadSheet) -> LayerWithFeatures | None:
    layer_source = table.metadata.get(_SOURCE, None)
    if layer_source is None:
        return None
    available_layers = get_layers_with_features(table)
    layer_source: LayerSource
    layer_default = layer_source.layer
    if layer_default is not None and layer_default in available_layers:
        return layer_default
    return None


def _get_source(table: SpreadSheet) -> Layer | None:
    layer_source = table.metadata.get(_SOURCE, None)
    if layer_source is None:
        return None
    available_layers = _utils.get_layers(table)
    layer_source: LayerSource
    layer_default = layer_source.layer
    if layer_default is not None and layer_default in available_layers:
        return layer_default
    return None
