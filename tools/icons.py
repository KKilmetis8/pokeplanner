"""Write icon-192.png / icon-512.png: a flat Poké Ball on the app background (maskable-safe margin)."""
import struct, zlib, os
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
def png(n, path):
    bg, red, white, black = (23, 24, 26), (214, 48, 49), (240, 240, 240), (20, 20, 20)
    c, R = n / 2, n * 0.34
    rows = []
    for y in range(n):
        row = bytearray([0])
        for x in range(n):
            dx, dy = x + .5 - c, y + .5 - c; d = (dx * dx + dy * dy) ** .5
            p = bg
            if d <= R:
                p = black if d > R * .93 else (black if abs(dy) < R * .08 else (red if dy < 0 else white))
                if d < R * .3: p = black
                if d < R * .2: p = white
            row += bytes(p)
        rows.append(bytes(row))
    raw = zlib.compress(b"".join(rows), 9)
    ch = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d))
    open(path, "wb").write(b"\x89PNG\r\n\x1a\n" + ch(b"IHDR", struct.pack(">IIBBBBB", n, n, 8, 2, 0, 0, 0)) + ch(b"IDAT", raw) + ch(b"IEND", b""))
for n in (192, 512): png(n, os.path.join(ROOT, f"icon-{n}.png"))
