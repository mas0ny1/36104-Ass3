"""Tab 1 - Builders: who is producing notable and frontier AI models?"""

from core.page import Page

from .src.views import render

PAGE = Page(
    label="1 · Mason",
    question="Who is innovating on cuttting-edge AI?",
    owner="Mason",
    render=render,
)
