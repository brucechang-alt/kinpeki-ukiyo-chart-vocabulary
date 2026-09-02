#!/usr/bin/env python3
"""Apply the approved new-impression high-chroma palette to authored sources."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

TARGETS = [
    ROOT / "styles.css",
    ROOT / "src" / "poster.css",
    ROOT / "src" / "poster.js",
    ROOT / "scripts" / "generate_trilingual.py",
    ROOT / "scripts" / "transform_svgs.js",
    ROOT / "docs" / "color-usage-guide.md",
    ROOT / "README.md",
    ROOT / "README_EN.md",
    ROOT / "README_JA.md",
]

REPLACEMENTS = {
    "#f3e7cf": "#fbf3de",
    "#fbf4e5": "#fff9ed",
    "#ddc98f": "#ead49a",
    "#1e1b17": "#181a1b",
    "#51483d": "#47433b",
    "#6a5f51": "#655f53",
    "#b8aa91": "#c8b990",
    "#194d78": "#0069a6",
    "#c84a3a": "#e24832",
    "#b53c31": "#b83326",
    "#4e7256": "#3a8a5c",
    "#b97832": "#e2a228",
    "#755a78": "#8d4b8e",
    "#c9a64a": "#e0b53a",
    "#8faec0": "#8cc7df",
    "#d88a73": "#f5a08b",
    "#c6d2c1": "#9ed0ab",
    "#c8b6ca": "#c7a0cf",
    "#a9b7c2": "#84bcd5",
    "#d7b0a5": "#efaa91",
    "#b9c2ae": "#9bc9a4",
    "rgba(243,231,207": "rgba(251,243,222",
    "rgba(30,27,23": "rgba(24,26,27",
}


def replace_case_insensitive(source: str, old: str, new: str) -> str:
    return re.sub(re.escape(old), new, source, flags=re.IGNORECASE)


def main() -> None:
    for path in TARGETS:
        source = path.read_text(encoding="utf-8")
        for old, new in REPLACEMENTS.items():
            source = replace_case_insensitive(source, old, new)
        if path.name == "styles.css":
            source = source.replace("color:var(--aizuri)}.license-grid", "color:var(--aizuri-text)}.license-grid")
        if path.name == "poster.css" and "--aizuri-text" not in source:
            source = source.replace(
                "--aizuri:#0069a6;",
                "--aizuri:#0069a6;--aizuri-text:#004b7a;",
            )
        path.write_text(source, encoding="utf-8")

    print(f"Applied high-chroma palette to {len(TARGETS)} authored source files")


if __name__ == "__main__":
    main()
