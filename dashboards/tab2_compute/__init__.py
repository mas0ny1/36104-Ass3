from core.page import Page

from .src.views import render

PAGE = Page(
    label="2 · Compute",
    question="Who owns the chips and the clusters?",
    owner="Duc Vu",
    render=render,
)
