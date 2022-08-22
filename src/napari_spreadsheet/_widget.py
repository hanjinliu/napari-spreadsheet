import weakref
from typing import TYPE_CHECKING, Optional

from qtpy import QtWidgets as QtW
from tabulous import TableViewerWidget as _TableViewerWidget

from . import _utils
from ._types import LayerWithFeatures, get_layers_with_features

if TYPE_CHECKING:
    import napari
    import pandas as pd


class TableViewerWidget(_TableViewerWidget):
    """The tabulous table viewer widget for napari."""

    @property
    def console(self):
        raise AttributeError("console is not available in this widget.")


class LayerSource:
    """A weak reference to a napari layer."""

    def __init__(self, layer: LayerWithFeatures):
        self._layer = weakref.ref(layer)

    def __repr__(self) -> str:
        layer = self.layer
        clsname = type(self).__name__
        if layer is None:
            return f"{clsname}(<deleted>)"
        return f"{clsname}({layer})"

    @property
    def layer(self) -> LayerWithFeatures:
        return self._layer()

    @property
    def features(self) -> "pd.DataFrame":
        layer = self.layer
        if layer is not None:
            return layer.features


_SOURCE = "source"


class MainWidget(QtW.QWidget):
    _current_widget: Optional[TableViewerWidget] = None

    def __init__(
        self, napari_viewer: "napari.Viewer", *, new_sheet: bool = True
    ):
        super().__init__()
        self._viewer = napari_viewer

        self._table_viewer = TableViewerWidget(show=False)
        if new_sheet:
            self._table_viewer.add_spreadsheet()

        self._init_ui()

        self.__class__._current_widget = self._table_viewer

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

    def load_layer_features(self):
        """Load layer features from the napari viewer."""
        table = self._table_viewer.current_table
        if table is None:
            return
        layer: LayerWithFeatures = get_layer(
            layer={"nullable": False}, parent=self
        )
        if layer is not None:
            self._table_viewer.add_table(
                layer.features,
                name=layer.name,
                metadata={_SOURCE: LayerSource(layer)},
            )

    def update_layer_features(self):
        """Update napari layer features with the current table."""
        table = self._table_viewer.current_table
        if table is None:
            return
        # try getting the source layer.
        layer_source = table.metadata.get(_SOURCE, None)
        choices = get_layers_with_features(table)
        layer_params = {"choices": choices}
        if layer_source is not None:
            layer_source: LayerSource
            layer_default = layer_source.layer
            if layer_default is not None and layer_default in choices:
                layer_params.update(value=layer_default)
        layer: LayerWithFeatures = get_layer(layer=layer_params, parent=self)
        if layer is not None:
            layer.features = table.data
            layer.refresh()
        return None

    def open_new_widget(self):
        """Open a new widget."""
        table_viewer = TableViewerWidget(show=False)
        self._viewer.window.add_dock_widget(table_viewer, name="Spreadsheet")
        return None

    def _init_ui(self):
        # buttons
        _header = QtW.QWidget()
        _layout = QtW.QHBoxLayout()
        _layout.setContentsMargins(0, 0, 0, 0)
        # fmt: off
        buttons = [
            _utils.create_button(self.load_layer_features, name="From\nFeatures"),  # noqa
            _utils.create_button(self.update_layer_features, name="Update\nFeatures"),  # noqa
            _utils.create_button(self.popup_current_table, name="Popup"),  # noqa
            _utils.create_button(self.open_new_widget, name="New Widget"),  # noqa
        ]
        # fmt: on
        for btn in buttons:
            _layout.addWidget(btn)
        max_height = max(btn.sizeHint().height() for btn in buttons)
        for btn in buttons:
            btn.setFixedHeight(max_height)
        _header.setLayout(_layout)

        _main_layout = QtW.QVBoxLayout()
        _main_layout.addWidget(_header)
        _main_layout.addWidget(self._table_viewer.native)
        self.setLayout(_main_layout)
        return None


@_utils.dialog_factory
def get_layer(layer: LayerWithFeatures) -> LayerWithFeatures:
    return layer
