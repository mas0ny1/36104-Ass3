"""Chart colours shared by every tab.

Categorical slots 1-3 come from a colour-blind-checked palette and are used
in this fixed order everywhere. Anything past three series folds into the
neutral grey 'other' colour instead of getting a new hue.
"""

import streamlit as st

LIGHT = {
    "series": ["#2a78d6", "#eb6834", "#1baf7a"],   # blue, orange, aqua
    "other": "#a8a69f",
    "muted": "#898781",
    "surface": "#ffffff",
}
DARK = {
    "series": ["#3987e5", "#d95926", "#199e70"],
    "other": "#6b6a64",
    "muted": "#898781",
    "surface": "#0e1117",
}


def colours():
    """Pick the light or dark steps to match the viewer's Streamlit theme."""
    try:
        dark = st.context.theme.type == "dark"
    except AttributeError:
        dark = False
    return DARK if dark else LIGHT
