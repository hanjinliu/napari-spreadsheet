from __future__ import annotations

from typing import TYPE_CHECKING

from qtpy.QtWidgets import QVBoxLayout, QWidget
from tabulous import TableViewerWidget as _TableViewerWidget

if TYPE_CHECKING:
    pass


class TableViewerWidget(_TableViewerWidget):
    """The tabulous table viewer widget for napari."""

    @property
    def console(self):
        raise AttributeError("console is not available in this widget.")


class MainWidget(QWidget):
    _current_widget: TableViewerWidget | None = None

    def __init__(self, napari_viewer, *, new_sheet: bool = True):
        super().__init__()
        self.viewer = napari_viewer

        self._table_viewer = TableViewerWidget(show=False)
        if new_sheet:
            self._table_viewer.add_spreadsheet()

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self._table_viewer.native)
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
