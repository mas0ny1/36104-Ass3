from core.page import Page

from .src.views import render

PAGE = Page(
    label="3 · Capital",
    question="Where is the money going?",
    owner="To be confirmed",
    render=render,
)
