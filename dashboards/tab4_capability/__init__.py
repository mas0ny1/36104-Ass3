from core.page import Page

from .src.views import render

PAGE = Page(
    label="4 · Capability",
    question="Is the gap between the leaders and everyone else closing?",
    owner="To be confirmed",
    render=render,
)
