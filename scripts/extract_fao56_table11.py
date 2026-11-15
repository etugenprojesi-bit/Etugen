"""Extract FAO-56 Table 11 (lengths of crop development stages) to YAML.

Downloads the FAO-56 chapter 6 HTML page, parses Table 11 and writes
data/fao56_table11.yaml. Re-run to reproduce the file; values are never
typed by hand.

Run: backend/.venv/Scripts/python scripts/extract_fao56_table11.py
"""

from __future__ import annotations

import html
import re
from pathlib import Path

import httpx
import yaml

URL = "https://www.fao.org/4/X0490E/x0490e0b.htm"
OUT = Path(__file__).resolve().parents[1] / "data" / "fao56_table11.yaml"


def cells(row_html: str) -> list[str]:
    raw = re.findall(r"(?is)<t[dh][^>]*>(.*?)</t[dh]>", row_html)
    return [html.unescape(re.sub(r"\s+", " ", re.sub(r"(?s)<[^>]+>", "", c))).strip() for c in raw]


def parse_days(s: str) -> list[float] | float | None:
    """'30' -> 30, '30/45' -> [30, 45], '20^2' -> 20, '30.' -> 30, 'var.' -> None."""
    s = re.sub(r"\^\d+", "", s).strip().rstrip(".")
    parts = [p for p in s.split("/") if p.strip()]
    try:
        nums = [float(p) for p in parts]
    except ValueError:
        return None
    if not nums:
        return None
    return nums[0] if len(nums) == 1 else nums


def main() -> None:
    page = httpx.get(URL, timeout=60, follow_redirects=True).content.decode("cp1252", errors="replace")
    page = re.sub(r"(?is)<sup>(.*?)</sup>", r"^\1", page)
    start = page.find("<B>TABLE 11")
    end = page.find("<B>TABLE 12")
    table = page[start:end]

    rows_out: list[dict] = []
    group = crop = None
    for r in re.findall(r"(?is)<tr[^>]*>(.*?)</tr>", table):
        c = cells(r)
        if not any(c) or c[0].startswith("Crop"):
            continue
        if re.match(r"^[a-p]\. ", c[0]):
            group = c[0]
            continue
        if c[0] == "" and len(c) > 1 and c[1].startswith("- "):  # sub-variety row
            name, vals = f"{crop} {c[1]}", c[2:]
        elif parse_days(c[0]) is not None:  # continuation row (crop cell spans rows)
            name, vals = crop, c
        elif c[0].startswith("year ") and crop and crop.startswith("Cassava"):
            name, vals = f"Cassava: {c[0]}", c[1:]
        else:
            # drop footnote markers ("Alfalfa ^4, other cutting cycles") but keep "1^st"
            crop = re.sub(r"\s*\^\d+(?=[\s,]|$)", "", c[0]).rstrip(":").strip()
            name, vals = crop, c[1:]
        vals = vals + [""] * (7 - len(vals))
        rows_out.append({
            "group": group,
            "crop": name,
            "init": parse_days(vals[0]),
            "dev": parse_days(vals[1]),
            "mid": parse_days(vals[2]),
            "late": parse_days(vals[3]),
            "total": parse_days(vals[4]),
            "planting": vals[5] or None,
            "region": vals[6] or None,
            "raw": " | ".join(vals[:7]),
        })

    doc = {
        "source": {
            "citation": "Allen, R.G., Pereira, L.S., Raes, D., Smith, M. (1998). FAO Irrigation "
                        "and Drainage Paper 56, Table 11: Lengths of crop development stages (days).",
            "url": URL,
            "generated_by": "scripts/extract_fao56_table11.py",
            "note": "Day counts are indicative for the listed planting date and region; "
                    "'a/b' values are stored as [a, b]. Planting/region text may wrap "
                    "across rows in the original table.",
        },
        "rows": rows_out,
    }
    OUT.write_text(yaml.safe_dump(doc, allow_unicode=True, sort_keys=False, width=100), encoding="utf-8")
    print(f"wrote {len(rows_out)} rows to {OUT}")


if __name__ == "__main__":
    main()
