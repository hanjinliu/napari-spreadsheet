from __future__ import annotations

from typing import Callable, TypeVar

from magicgui.widgets import Dialog
from qtpy import QtWidgets as QtW

_F = TypeVar("_F", bound=Callable)


def dialog_factory(function: _F) -> _F:
    from magicgui.signature import magic_signature

    def _runner(parent=None, **param_options):
        widgets = list(
            magic_signature(function, gui_options=param_options)
            .widgets()
            .values()
        )
        dlg = Dialog(widgets=widgets)
        dlg.native.setParent(parent, dlg.native.windowFlags())
        if dlg.exec():
            out = function(**dlg.asdict())
        else:
            out = None
        return out

    return _runner


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
    btn.clicked.connect(slot)
    btn.setToolTip(tooltip)
    return btn
