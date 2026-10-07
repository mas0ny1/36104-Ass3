"""The contract between the base app and each dashboard folder.

Every folder in dashboards/ exposes one `PAGE` object in its __init__.py.
The base app (app.py) shows each PAGE as a tab, and each folder's own app.py
can run its PAGE alone with `run_standalone`.

A dashboard that fails, whether on import or while drawing, shows its error
in its own tab and leaves the other tabs working.
"""

from dataclasses import dataclass
from importlib import import_module
from typing import Callable

import streamlit as st


@dataclass(frozen=True)
class Page:
    label: str                   # tab label, e.g. "1 · Builders"
    question: str                # the sub-question the tab answers
    render: Callable[[], None]   # draws the tab body (no set_page_config)
    owner: str = "To be confirmed"


def load_page(module_name):
    """Import a dashboard package and return its PAGE, or an error page."""
    try:
        return import_module(module_name).PAGE
    except Exception as err:   # a teammate's bug must not take down every tab
        folder = module_name.rsplit(".", 1)[-1]

        def show_error(err=err):
            st.error(f"`{module_name}` could not be imported. Fix the error "
                     "below; the other tabs are unaffected.")
            st.exception(err)

        return Page(label=folder, question=f"{folder} failed to load",
                    render=show_error)


def render_page(page):
    """Draw the shared header, then the dashboard's own content."""
    st.header(page.question)
    try:
        page.render()
    except Exception as err:   # Streamlit's stop/rerun signals are not Exceptions
        st.error("This tab hit an error. The other tabs are unaffected.")
        st.exception(err)


def run_standalone(page):
    """Run one dashboard on its own, for working on a single tab."""
    st.set_page_config(page_title=page.question, layout="wide")
    st.caption("Running this tab on its own. For the full dashboard, run "
               "`streamlit run app.py` from the project root.")
    render_page(page)
