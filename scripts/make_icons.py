"""Generate the PWA icons (compass needle on a field-green tile) with the
standard library only. Writes frontend/public/icon-192.png, icon-512.png and
favicon.svg.

Run: backend/.venv/Scripts/python scripts/make_icons.py
"""

from __future__ import annotations

import struct
import zlib
from pathlib import Path

PUBLIC = Path(__file__).resolve().parents[1] / "frontend" / "public"
GREEN = (47, 107, 58)
WHITE = (246, 244, 238)
RED = (192, 57, 43)


def pixel(x: float, y: float) -> tuple[int, int, int]:
    """x, y in [-1, 1]. Diamond needle: red north half, white south half."""
    w = 0.28  # needle half-width
    if abs(x) / w + abs(y) / 0.78 <= 1.0:
        return RED if y < 0 else WHITE
    if x * x + y * y <= 0.07 ** 2:
        return WHITE
    return GREEN


def png(size: int) -> bytes:
    rows = []
    for j in range(size):
        row = bytearray([0])  # filter type 0
        for i in range(size):
            x = (i + 0.5) / size * 2 - 1
            y = (j + 0.5) / size * 2 - 1
            row += bytes(pixel(x, y))
        rows.append(bytes(row))
    raw = zlib.compress(b"".join(rows), 9)

    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data))

    ihdr = struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0)  # 8-bit RGB
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", raw) + chunk(b"IEND", b"")


SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="-1 -1 2 2">
<rect x="-1" y="-1" width="2" height="2" rx="0.35" fill="rgb(47,107,58)"/>
<polygon points="0,-0.78 0.28,0 -0.28,0" fill="rgb(192,57,43)"/>
<polygon points="0,0.78 0.28,0 -0.28,0" fill="rgb(246,244,238)"/>
</svg>
"""


def main() -> None:
    for size in (192, 512):
        (PUBLIC / f"icon-{size}.png").write_bytes(png(size))
    (PUBLIC / "favicon.svg").write_text(SVG, encoding="utf-8")
    print("icons written to", PUBLIC)


if __name__ == "__main__":
    main()
