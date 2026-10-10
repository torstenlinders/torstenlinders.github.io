#!/usr/bin/env python3
"""Build Swedish and English SVG charts from the language-neutral survey CSV."""
from __future__ import annotations

import argparse
import csv
import re
import textwrap
import tomllib
from collections import Counter
from pathlib import Path

import yaml

BLUE = "#2e3192"
RED = "#8f0040"
TEXT = "#202332"
MUTED = "#646878"
BORDER = "#dedee8"
FONT = "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"

QUESTION_IDS = {"1": "viktigast", "2": "omraden", "3": "pastaende", "4": "sjalvbild"}


def parse_front_matter(path: Path) -> dict:
    raw = path.read_text(encoding="utf-8")
    match = re.match(r"^---\s*\n(.*?)\n---", raw, flags=re.S)
    if not match:
        raise ValueError(f"Ingen YAML-front matter i {path}")
    return yaml.safe_load(match.group(1))


def load_i18n(path: Path) -> dict[str, str]:
    with path.open("rb") as f:
        data = tomllib.load(f)
    out: dict[str, str] = {}
    for key, value in data.items():
        if isinstance(value, dict) and "other" in value:
            out[key] = str(value["other"])
    return out


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    required = {"id", "viktigast", "omraden", "pastaende", "sjalvbild"}
    missing = required - set(rows[0]) if rows else required
    if missing:
        raise ValueError(f"CSV saknar kolumner: {', '.join(sorted(missing))}")
    return rows


def normalize_multi(value: str) -> list[str]:
    if not value:
        return []
    # New worker export: a;b;c. Also accept comma as a harmless fallback.
    parts = re.split(r"\s*[;,]\s*", value.strip())
    return [p for p in parts if p]


def labels_from_focus(front_matter: dict, i18n: dict[str, str]) -> dict[str, dict[str, list[tuple[str, str]] | str]]:
    result = {}
    for q in front_matter["questions"]:
        qid = q["id"]
        if "i18n" not in q:
            continue
        result[qid] = {
            "question": i18n[q["i18n"]],
            "options": [(opt["id"], i18n[opt["i18n"]]) for opt in q.get("options", [])],
        }
    return result


def xhtml_text(text: str) -> str:
    return (text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;"))


def wrap(text: str, width: int) -> list[str]:
    return textwrap.wrap(text, width=width, break_long_words=False, break_on_hyphens=False) or [""]


def svg_start(title: str, desc: str, width: int, height: int) -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        f'<title id="title">{xhtml_text(title)}</title>',
        f'<desc id="desc">{xhtml_text(desc)}</desc>',
        f'<rect width="{width}" height="{height}" fill="#ffffff"/>',
    ]


def finish(lines: list[str]) -> str:
    return "\n".join(lines + ["</svg>", ""])


def add_multiline_text(lines: list[str], x: float, y: float, text: str, width: int, font_size: int = 17, weight: int = 500, fill: str = TEXT, line_gap: int = 22) -> int:
    wrapped = wrap(text, width)
    lines.append(f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{font_size}" font-weight="{weight}" fill="{fill}">')
    for i, part in enumerate(wrapped):
        dy = 0 if i == 0 else line_gap
        lines.append(f'<tspan x="{x}" dy="{dy}">{xhtml_text(part)}</tspan>')
    lines.append('</text>')
    return len(wrapped)


def build_pie(path: Path, title: str, data: list[tuple[str, int]], total: int, colors: list[str], labels: dict[str, str], answer_word: str) -> None:
    width, height = 900, 560
    lines = svg_start(title, f"{total} {answer_word}.", width, height)
    lines.append(f'<text x="40" y="42" font-family="{FONT}" font-size="26" font-weight="750" fill="{BLUE}">{xhtml_text(title)}</text>')
    cx, cy, radius = 245, 315, 155
    current = -90.0
    import math

    if total == 0:
        lines.append(f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="{BORDER}"/>')
    else:
        for index, (key, value) in enumerate(data):
            if value <= 0:
                continue
            angle = value / total * 360.0
            end = current + angle
            large = 1 if angle > 180 else 0
            x1 = cx + radius * math.cos(math.radians(current))
            y1 = cy + radius * math.sin(math.radians(current))
            x2 = cx + radius * math.cos(math.radians(end))
            y2 = cy + radius * math.sin(math.radians(end))
            d = f"M {cx} {cy} L {x1:.2f} {y1:.2f} A {radius} {radius} 0 {large} 1 {x2:.2f} {y2:.2f} Z"
            lines.append(f'<path d="{d}" fill="{colors[index % len(colors)]}"/>')
            current = end

    lines.append(f'<circle cx="{cx}" cy="{cy}" r="52" fill="#ffffff"/>')
    lines.append(f'<text x="{cx}" y="{cy + 8}" text-anchor="middle" font-family="{FONT}" font-size="38" font-weight="800" fill="{BLUE}">{total}</text>')
    lines.append(f'<text x="{cx}" y="{cy + 35}" text-anchor="middle" font-family="{FONT}" font-size="15" fill="{MUTED}">{xhtml_text(answer_word)}</text>')

    x0 = 475
    y = 175
    for index, (key, value) in enumerate(data):
        lines.append(f'<rect x="{x0}" y="{y - 15}" width="18" height="18" rx="3" fill="{colors[index % len(colors)]}"/>')
        label = labels[key]
        text_lines = wrap(f"{label} — {value} ({value / total * 100:.0f}%)" if total else f"{label} — 0", 34)
        add_multiline_text(lines, x0 + 30, y, "\n".join(text_lines), 34, 17, 550, TEXT, 22)
        y += max(56, len(text_lines) * 22 + 18)

    path.write_text(finish(lines), encoding="utf-8")


def build_bar(path: Path, title: str, data: list[tuple[str, int]], total: int, colors: list[str], value_label: str, answer_word: str) -> None:
    row_h = 70
    width, height = 1000, max(720, 120 + len(data) * row_h)
    lines = svg_start(title, f"{total} {answer_word}.", width, height)
    lines.append(f'<text x="20" y="42" font-family="{FONT}" font-size="26" font-weight="750" fill="{BLUE}">{xhtml_text(title)}</text>')
    left, right = 410, 920
    top = 80
    max_value = max([v for _, v in data] + [1])
    scale_max = max(total, max_value, 1)
    # 0, 25, 50, 75, 100 % style guides where sensible; keep integer count axis.
    x_axis_y = top + len(data) * row_h + 5
    lines.append(f'<text x="{left}" y="{x_axis_y + 36}" font-family="{FONT}" font-size="13" fill="{MUTED}">0</text>')
    lines.append(f'<text x="{left + (right-left)/2:.1f}" y="{x_axis_y + 36}" text-anchor="middle" font-family="{FONT}" font-size="13" fill="{MUTED}">{scale_max/2:g}</text>')
    lines.append(f'<text x="{right}" y="{x_axis_y + 36}" text-anchor="end" font-family="{FONT}" font-size="13" fill="{MUTED}">{scale_max}</text>')

    for i, (key, value) in enumerate(data):
        y = top + i * row_h
        lines.append(f'<line x1="{left}" y1="{y + 25}" x2="{right}" y2="{y + 25}" stroke="{BORDER}" stroke-width="1"/>')
        label_y = y + 18
        wrapped = wrap(key, 47)
        lines.append(f'<text x="20" y="{label_y}" font-family="{FONT}" font-size="16" font-weight="550" fill="{TEXT}">')
        for j, part in enumerate(wrapped[:2]):
            lines.append(f'<tspan x="20" dy="{0 if j == 0 else 20}">{xhtml_text(part)}</tspan>')
        lines.append('</text>')
        bar_width = (right-left) * value / scale_max
        color = colors[i % len(colors)]
        lines.append(f'<rect x="{left}" y="{y + 5}" width="{bar_width:.2f}" height="30" rx="4" fill="{color}"/>')
        lines.append(f'<text x="{min(left + bar_width + 10, right - 5):.2f}" y="{y + 27}" font-family="{FONT}" font-size="16" font-weight="700" fill="{TEXT}">{value}</text>')

    path.write_text(finish(lines), encoding="utf-8")


def get_option_labels(focus: dict, qid: str) -> dict[str, str]:
    return {k: v for k, v in focus[qid]["options"]}


def build_charts(csv_path: Path, focus_sv: Path, focus_en: Path, sv_toml: Path, en_toml: Path, out_dir: Path) -> None:
    rows = load_csv(csv_path)
    front_sv = parse_front_matter(focus_sv)
    front_en = parse_front_matter(focus_en)
    i18n_sv = load_i18n(sv_toml)
    i18n_en = load_i18n(en_toml)
    labels_sv = labels_from_focus(front_sv, i18n_sv)
    labels_en = labels_from_focus(front_en, i18n_en)

    q1 = Counter(r["viktigast"] for r in rows)
    q2 = Counter(v for r in rows for v in normalize_multi(r["omraden"]))
    q3 = Counter(v for r in rows for v in normalize_multi(r["pastaende"]))
    q4 = Counter(r["sjalvbild"] for r in rows)

    for lang, i18n, labels in [("sv", i18n_sv, labels_sv), ("en", i18n_en, labels_en)]:
        out = out_dir / lang
        out.mkdir(parents=True, exist_ok=True)

        for number, qid, counts in [("1", "viktigast", q1), ("2", "omraden", q2), ("3", "pastaende", q3), ("4", "sjalvbild", q4)]:
            title = i18n[f"fokus_q{number}"]
            option_labels = get_option_labels(labels, qid)
            ordered = [(oid, counts.get(oid, 0)) for oid in option_labels]
            chart_path = out / f"q{number}.svg"
            if qid in {"viktigast", "sjalvbild"}:
                build_pie(chart_path, title, ordered, len(rows), [BLUE, RED], option_labels, i18n["fokus_results_answer"])
            else:
                data = [(option_labels[oid], count) for oid, count in ordered]
                build_bar(chart_path, title, data, len(rows), [BLUE, RED], i18n["fokus_results_responses"], i18n["fokus_results_answer"])

    (out_dir / "results.json").write_text(
        '{"response_count": %d}\n' % len(rows), encoding="utf-8"
    )

    # Also write a Hugo-friendly data file outside static/.
    data_dir = csv_path.parent
    (data_dir / "fokus_results.json").write_text(
        '{"response_count": %d}\n' % len(rows), encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=Path, default=Path("data/fokus-svar.csv"))
    parser.add_argument("--sv-md", type=Path, default=Path("content/fokus/_index.md"))
    parser.add_argument("--en-md", type=Path, default=Path("content/en/focus/_index.md"))
    parser.add_argument("--sv-toml", type=Path, default=Path("i18n/sv.toml"))
    parser.add_argument("--en-toml", type=Path, default=Path("i18n/en.toml"))
    parser.add_argument("--out", type=Path, default=Path("static/fokus-results"))
    args = parser.parse_args()
    build_charts(args.csv, args.sv_md, args.en_md, args.sv_toml, args.en_toml, args.out)
    print(f"Skapade svenska och engelska diagram i {args.out}")


if __name__ == "__main__":
    main()
