#!/usr/bin/env python3
"""Static XML, manifest, colour-difference and contrast audit."""

from __future__ import annotations

import json
import math
from pathlib import Path

from lxml import etree


ROOT = Path(__file__).resolve().parents[1]
PAPER = "#FBF3DE"
MARKS = ["#0069A6", "#E24832", "#3A8A5C", "#E2A228", "#8D4B8E"]
TEXT = ["#181A1B", "#004B7A", "#B83326", "#2F6D49", "#905D0B", "#713C73", "#81620B"]
FORBIDDEN = ["#F3E7CF", "#1E1B17", "#194D78", "#C84A3A", "#4E7256", "#B97832", "#755A78", "#C9A64A"]


def rgb(hex_value: str) -> tuple[float, float, float]:
    value = hex_value.lstrip("#")
    return tuple(int(value[i : i + 2], 16) / 255 for i in (0, 2, 4))


def luminance(hex_value: str) -> float:
    channels = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in rgb(hex_value)]
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def contrast(a: str, b: str) -> float:
    high, low = sorted((luminance(a), luminance(b)), reverse=True)
    return round((high + 0.05) / (low + 0.05), 2)


def lab(hex_value: str) -> tuple[float, float, float]:
    linear = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in rgb(hex_value)]
    x = (0.4124564 * linear[0] + 0.3575761 * linear[1] + 0.1804375 * linear[2]) / 0.95047
    y = 0.2126729 * linear[0] + 0.7151522 * linear[1] + 0.0721750 * linear[2]
    z = (0.0193339 * linear[0] + 0.1191920 * linear[1] + 0.9503041 * linear[2]) / 1.08883
    f = lambda t: t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116
    fx, fy, fz = f(x), f(y), f(z)
    return 116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)


def delta(a: str, b: str) -> float:
    return round(math.dist(lab(a), lab(b)), 1)


def main() -> None:
    files = sorted((ROOT / "charts").rglob("*.svg"))
    failures: list[str] = []
    if len(files) != 201:
        failures.append(f"expected 201 SVGs, found {len(files)}")
    for path in files:
        raw = path.read_text(encoding="utf-8")
        try:
            tree = etree.fromstring(raw.encode())
        except etree.XMLSyntaxError as error:
            failures.append(f"invalid XML: {path.relative_to(ROOT)}: {error}")
            continue
        names = {etree.QName(node).localname for node in tree.iter()}
        if not {"title", "desc"}.issubset(names):
            failures.append(f"missing title/desc: {path.relative_to(ROOT)}")
        lowered = raw.lower()
        if any(colour.lower() in lowered for colour in FORBIDDEN):
            failures.append(f"legacy colour: {path.relative_to(ROOT)}")
    manifests = {}
    for name in ("manifest.json", "manifest-en.json", "manifest-ja.json"):
        data = json.loads((ROOT / "charts" / name).read_text(encoding="utf-8"))
        count = sum(len(family["charts"]) for family in data["families"])
        manifests[name] = {"version": data["version"], "families": len(data["families"]), "charts": count}
        if data["version"] != "1.0.0" or len(data["families"]) != 9 or count != 67:
            failures.append(f"manifest contract: {name}")
    pairs = {f"{a}/{b}": delta(a, b) for index, a in enumerate(MARKS) for b in MARKS[index + 1 :]}
    minimum_delta = min(pairs.values())
    contrasts = {colour: contrast(colour, PAPER) for colour in TEXT}
    if minimum_delta < 25:
        failures.append(f"minimum mark DeltaE76 is {minimum_delta}")
    if min(contrasts.values()) < 4.5:
        failures.append(f"minimum small-text contrast is {min(contrasts.values())}")
    result = {"status": "PASS" if not failures else "FAIL", "svgCount": len(files), "manifests": manifests, "minimumMarkDeltaE76": minimum_delta, "markDeltaE76": pairs, "textContrastOnPaper": contrasts, "failures": failures}
    (ROOT / "static-validation.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
