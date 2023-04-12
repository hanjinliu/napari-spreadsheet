from __future__ import annotations

from typing import TYPE_CHECKING, Any, NewType

from magicgui import register_type

if TYPE_CHECKING:
    import pandas as pd
    from magicgui.widgets import Widget
    from napari.layers import Layer

    class LayerWithFeatures(Layer):
        @property
        def features(self) -> pd.DataFrame:
            ...

else:
    LayerWithFeatures = NewType("LayerWithFeatures", Any)


def get_layers_with_features(gui: Widget) -> list[Layer]:
    from napari.utils._magicgui import find_viewer_ancestor

    viewer = find_viewer_ancestor(gui.native)
    if not viewer:
        return []
    return [x for x in viewer.layers if len(getattr(x, "features", [])) > 0]


register_type(LayerWithFeatures, choices=get_layers_with_features)
