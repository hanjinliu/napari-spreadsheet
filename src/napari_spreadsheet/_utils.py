from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from magicgui.widgets import ComboBox, Dialog, LineEdit
from qtpy import QtWidgets as QtW

if TYPE_CHECKING:
    from ._types import LayerWithFeatures


def get_str(
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


def get_layer(
    label: str = "layer",
    value=None,
    parent: QtW.QWidget | None = None,
) -> LayerWithFeatures | None:
    from ._types import get_layers_with_features

    cbox = ComboBox(
        choices=get_layers_with_features, label=label, nullable=False
    )
    dlg = Dialog(widgets=[cbox])
    dlg.native.setParent(parent, dlg.native.windowFlags())
    dlg.reset_choices()
    if dlg.exec():
        out = dlg[0].value
    else:
        out = None
    return out


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
