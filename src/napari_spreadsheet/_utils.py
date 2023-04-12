from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from magicgui.widgets import ComboBox, Dialog, LineEdit
from qtpy import QtWidgets as QtW

if TYPE_CHECKING:
    from napari.layers import Layer


def get_str_by_dialog(
    label: str = "string",
    value: str = "",
    parent: QtW.QWidget | None = None,
) -> str | None:
    dlg = Dialog(widgets=[LineEdit(label=label, value=value)])
    dlg.native.setParent(parent, dlg.native.windowFlags())
    if dlg.exec():
        out = dlg[0].value
    else:
        out = None
    return out


def get_layer_by_dialog(
    parent: QtW.QWidget | None = None,
    choices=None,
) -> Layer | None:
    cbox = ComboBox(choices=choices, label="Layer", nullable=False)
    dlg = Dialog(widgets=[cbox])
    dlg.native.setParent(parent, dlg.native.windowFlags())
    dlg.reset_choices()
    if dlg.exec():
        out = dlg[0].value
    else:
        out = None
    return out


def get_layers(w):
    from napari.utils._magicgui import find_viewer_ancestor

    viewer = find_viewer_ancestor(w)
    if viewer is None:
        return []
    return list(viewer.layers)


def create_button(
    slot: Callable,
    *,
    name: str | None = None,
    tooltip: str | None = None,
) -> QtW.QPushButton:
    """Create a QPushButton from a function."""
    if name is None:
        name = slot.__name__
    if tooltip is None and slot.__doc__ is not None:
        tooltip = slot.__doc__.strip()
    btn = QtW.QPushButton(name)
    btn.clicked.connect(lambda: slot())
    btn.setToolTip(tooltip)
    return btn


def create_menubutton(
    name: str,
    slots: list[tuple[str, Callable]],
) -> QtW.QPushButton:
    btn = QtW.QPushButton()
    btn.setText(name)
    menu = QtW.QMenu(btn)
    for slot_name, slot in slots:
        action = menu.addAction(slot_name, slot)
        action.setToolTip(slot.__doc__)
    btn.setMenu(menu)
    return btn
