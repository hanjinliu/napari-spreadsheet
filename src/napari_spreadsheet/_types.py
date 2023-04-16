from __future__ import annotations

from typing import TYPE_CHECKING, Any, NewType

from magicgui import register_type

if TYPE_CHECKING:  # pragma: no cover
    import pandas as pd
    from magicgui.widgets import Widget
    from napari.layers import Layer
    from napari.layers.utils.text_manager import TextManager

    class LayerWithFeatures(Layer):
        @property
        def features(self) -> pd.DataFrame:
            ...

    class LayerWithText(LayerWithFeatures):
        @property
        def text(self) -> TextManager:
            ...

else:
    LayerWithFeatures = NewType("LayerWithFeatures", Any)
    LayerWithText = NewType("LayerWithFeatures", Any)


def get_layers_with_features(gui: Widget) -> list[Layer]:
    from napari.utils._magicgui import find_viewer_ancestor

    viewer = find_viewer_ancestor(gui.native)
    if not viewer:
        return []
    return [x for x in viewer.layers if len(getattr(x, "features", [])) > 0]


def get_layers_with_text(gui: Widget) -> list[Layer]:
    from napari.utils._magicgui import find_viewer_ancestor

    viewer = find_viewer_ancestor(gui.native)
    if not viewer:
        return []
    return [x for x in viewer.layers if hasattr(x, "text") > 0]


register_type(LayerWithFeatures, choices=get_layers_with_features)
register_type(LayerWithText, choices=get_layers_with_features)
