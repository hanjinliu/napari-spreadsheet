from typing import Union

from ._widget import MainWidget

__all__ = ["MainWidget", "current_widget"]


def current_widget() -> Union[MainWidget, None]:
    """Return the current widget, if any."""
    return MainWidget._current_widget
