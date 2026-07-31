"""Shared text cleanup helpers. No em-dashes in outputs."""
from __future__ import annotations


def clean_text(t: str) -> str:
    return (
        t.replace("\u2014", "-")
        .replace("\u2013", "-")
        .replace("\u2019", "'")
        .replace("\u2018", "'")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
        .strip()
    )
