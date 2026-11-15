"""Extract FAO-56 Table 12 (Kc ini / mid / end, max crop height) and Table 22
(max root depth, depletion fraction p) to YAML.

Downloads the FAO-56 HTML pages and writes data/fao56_table12_22.yaml. Re-run
to reproduce the file; values are never typed by hand. A test checks the
`fao56` blocks in data/crops.yaml against this file.

Conventions kept from the tables:
* An empty Kc ini cell means the crop-group value applies (Table 12 footnote
  convention); stored with `kc_ini_from_group: true`.
* Footnote markers (^2) are removed; ranges "a-b" become [low, high] (sorted).
* Sub-rows ("Onions" / "- dry") are named "Onions - dry".

Run: backend/.venv/Scripts/python scripts/extract_fao56_table12_22.py
"""

from __future__ import annotations

import html
import re
from pathlib import Path

import httpx
import yaml

URL_T12 = "https://www.fao.org/4/X0490E/x0490e0b.htm"
URL_T22 = "https://www.fao.org/4/X0490E/x0490e0e.htm"
OUT = Path(__file__).resolve().parents[1] / "data" / "fao56_table12_22.yaml"


def cells(row_html: str) -> list[str]:
    raw = re.findall(r"(?is)<t[dh][^>]*>(.*?)</t[dh]>", row_html)
    return [html.unescape(re.sub(r"\s+", " ", re.sub(r"(?s)<[^>]+>", "", c))).strip() for c in raw]


def value(s: str):
    """'1.15^2' -> 1.15, '0.70-0.90' -> [0.7, 0.9], '0.60-0.35^6' -> [0.35, 0.6], '' -> None."""
    s = re.sub(r"\^\d+", "", s).strip()
    if not s:
        return None
    try:
        nums = sorted(float(p) for p in s.split("-"))
    except ValueError:
        return None
    return nums[0] if len(nums) == 1 else nums


def table(url: str, start: str, end: str) -> list[list[str]]:
    page = httpx.get(url, timeout=60, follow_redirects=True).content.decode("cp1252", errors="replace")
    page = re.sub(r"(?is)<sup>(.*?)</sup>", r"^\1", page)
    i = page.find(start)
    j = page.find(end, i)
    t = page[i:j if j > 0 else None]
    first_close = re.search(r"(?i)</table>", t[t.lower().find("<table"):])
    if first_close:  # stop at the end of the table itself (later examples reuse crop names)
        t = t[:t.lower().find("<table") + first_close.end()]
    return [cells(r) for r in re.findall(r"(?is)<tr[^>]*>(.*?)</tr>", t)]


def named_rows(rows: list[list[str]]):
    """Yield (group, name, values) with sub-rows joined to their parent name."""
    group = parent = None
    for c in rows:
        if not any(c) or c[0] == "Crop":
            continue
        if re.match(r"^[a-p]\. ", c[0]):
            group = c[0]
            yield group, None, c[1:]
            continue
        if c[0] == "" and len(c) > 1 and c[1].startswith("- "):
            yield group, f"{parent} {c[1]}", c[2:]
        else:
            parent = c[0]
            yield group, parent, c[1:]


def main() -> None:
    t12 = []
    group_kc_ini = {}
    for group, name, v in named_rows(table(URL_T12, "<B>TABLE 12", "<B>TABLE 13")):
        v = v + [""] * (4 - len(v))
        if name is None:
            group_kc_ini[group] = value(v[0])
            continue
        if not any(v):
            continue  # parent of sub-rows
        kc_ini = value(v[0])
        t12.append({"group": group, "crop": name,
                    "kc_ini": kc_ini if kc_ini is not None else group_kc_ini.get(group),
                    "kc_ini_from_group": kc_ini is None,
                    "kc_mid": value(v[1]), "kc_end": value(v[2]), "max_height_m": value(v[3]),
                    "raw": " | ".join(v[:4])})
    t22 = []
    for group, name, v in named_rows(table(URL_T22, "<B>TABLE 22", "<B>TABLE 23")):
        v = v + [""] * (2 - len(v))
        if name is None or not any(v):
            continue
        t22.append({"group": group, "crop": name, "root_depth_m": value(v[0]),
                    "depletion_p": value(v[1]), "raw": " | ".join(v[:2])})
    out = {
        "source": {
            "citation": ("Allen, R.G., Pereira, L.S., Raes, D., Smith, M. (1998). FAO Irrigation and "
                         "Drainage Paper 56. Table 12 (single crop coefficients, max crop height) and "
                         "Table 22 (max root depth, depletion fraction p for ETc ~5 mm/day)."),
            "url_table12": URL_T12, "url_table22": URL_T22,
            "generated_by": "scripts/extract_fao56_table12_22.py",
        },
        "table12": t12, "table22": t22,
    }
    OUT.write_text(yaml.safe_dump(out, allow_unicode=True, sort_keys=False, width=110), encoding="utf-8")
    print(f"{OUT.name}: {len(t12)} Table 12 rows, {len(t22)} Table 22 rows")


if __name__ == "__main__":
    main()
