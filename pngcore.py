"""pngcore.py - tiny dependency-free RGB PNG writer and raster canvas.

Stdlib only (struct, zlib, math). Deterministic output: no randomness,
no timestamps. All drawing is clipped to the canvas bounds.
"""

import math
import struct
import zlib


def clamp(v, lo, hi):
    """Clamp v into [lo, hi]."""
    return lo if v < lo else hi if v > hi else v


def lerp(a, b, t):
    """Linear interpolation between a and b by t."""
    return a + (b - a) * t


def _chunk(tag, data):
    """One PNG chunk: length, tag, data, CRC32."""
    return (struct.pack(">I", len(data)) + tag + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))


def save_png(path, w, h, px):
    """Write a truecolour RGB PNG (type 2, depth 8, no interlace).

    px is a flat row-major RGB bytearray of length w*h*3.
    Every scanline uses filter byte 0; zlib level 9. Deterministic.
    """
    if len(px) != w * h * 3:
        raise ValueError("px length must be w*h*3")
    stride = w * 3
    raw = bytearray()
    for y in range(h):
        raw.append(0)  # filter type 0 (None) per scanline
        raw += px[y * stride:(y + 1) * stride]
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    blob = (b"\x89PNG\r\n\x1a\n"
            + _chunk(b"IHDR", ihdr)
            + _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + _chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(blob)


class Canvas:
    """Row-major RGB byte buffer with simple clipped drawing primitives."""

    def __init__(self, w, h, bg=(255, 255, 255)):
        self.w = int(w)
        self.h = int(h)
        self.px = bytearray(bytes(bg) * (self.w * self.h))

    def set(self, x, y, c):
        """Set one pixel if inside bounds."""
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i] = c[0]
            self.px[i + 1] = c[1]
            self.px[i + 2] = c[2]

    def get(self, x, y):
        """Return (r,g,b), or (0,0,0) outside bounds."""
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            return (self.px[i], self.px[i + 1], self.px[i + 2])
        return (0, 0, 0)

    def fill_rect(self, x, y, w, h, c):
        """Filled rectangle, clipped to the canvas."""
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(c) * (x1 - x0)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.px[i:i + len(row)] = row

    def rect(self, x, y, w, h, c, lw=1):
        """Rectangle outline of line width lw, via four filled bars."""
        if lw <= 0 or w <= 0 or h <= 0:
            return
        self.fill_rect(x, y, w, lw, c)                 # top
        self.fill_rect(x, y + h - lw, w, lw, c)        # bottom
        self.fill_rect(x, y, lw, h, c)                 # left
        self.fill_rect(x + w - lw, y, lw, h, c)        # right

    def _bresenham(self, x0, y0, x1, y1):
        """Yield integer points along a straight line."""
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            yield x0, y0
            if x0 == x1 and y0 == y1:
                return
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def line(self, x0, y0, x1, y1, c, lw=1):
        """Bresenham line; lw>1 stamps filled circles along it."""
        if lw <= 1:
            for x, y in self._bresenham(x0, y0, x1, y1):
                self.set(x, y, c)
        else:
            r = lw * 0.5
            for x, y in self._bresenham(x0, y0, x1, y1):
                self.circle(x, y, r, c, fill=True)

    def circle(self, cx, cy, r, c, fill=True):
        """Filled disc, or a ~1px ring of pixels when fill=False."""
        if r < 0:
            return
        if r == 0:
            self.set(cx, cy, c)
            return
        r2 = r * r
        for y in range(max(0, int(cy - r) - 1), min(self.h, int(cy + r) + 2)):
            for x in range(max(0, int(cx - r) - 1), min(self.w, int(cx + r) + 2)):
                d2 = (x - cx) ** 2 + (y - cy) ** 2
                if fill:
                    if d2 <= r2:
                        self.set(x, y, c)
                elif abs(math.sqrt(d2) - r) <= 0.5:
                    self.set(x, y, c)

    def ellipse(self, cx, cy, rx, ry, c, fill=True):
        """Filled ellipse, or outline when fill=False."""
        if rx <= 0 or ry <= 0:
            return
        # outline band thickness in normalized units (~1px at narrow axis)
        band = 0.5 / min(rx, ry)
        for y in range(max(0, int(cy - ry) - 1), min(self.h, int(cy + ry) + 2)):
            for x in range(max(0, int(cx - rx) - 1), min(self.w, int(cx + rx) + 2)):
                q = math.sqrt(((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2)
                if (q <= 1.0) if fill else (abs(q - 1.0) <= band):
                    self.set(x, y, c)

    def poly(self, points, c):
        """Scanline (even-odd) fill; handles convex and concave polygons."""
        if len(points) < 3:
            return
        ys = [p[1] for p in points]
        y0 = max(0, int(math.floor(min(ys))))
        y1 = min(self.h - 1, int(math.ceil(max(ys))))
        n = len(points)
        for y in range(y0, y1 + 1):
            sy = y + 0.5  # sample at pixel centre to avoid vertex ambiguity
            xs = []
            for i in range(n):
                ax, ay = points[i]
                bx, by = points[(i + 1) % n]
                if (ay <= sy < by) or (by <= sy < ay):
                    xs.append(ax + (sy - ay) * (bx - ax) / (by - ay))
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                xa = int(math.ceil(xs[k] - 0.5))
                xb = int(math.floor(xs[k + 1] - 0.5))
                if xb >= xa:
                    self.fill_rect(xa, y, xb - xa + 1, 1, c)

    def blend(self, x, y, c, a):
        """Alpha-blend colour c over pixel (x,y); a in 0..1."""
        if not (0 <= x < self.w and 0 <= y < self.h):
            return
        a = clamp(a, 0.0, 1.0)
        i = (y * self.w + x) * 3
        for k in range(3):
            self.px[i + k] = int(round(c[k] * a + self.px[i + k] * (1.0 - a)))

    def save(self, path):
        save_png(path, self.w, self.h, self.px)


if __name__ == "__main__":
    # Self-test: draw each primitive, save, verify signature, report hash.
    import hashlib

    cv = Canvas(200, 120, bg=(255, 255, 255))
    cv.fill_rect(10, 10, 50, 30, (220, 40, 40))
    cv.rect(70, 10, 50, 30, (30, 90, 200), lw=2)
    cv.line(5, 115, 195, 45, (20, 160, 60), lw=4)
    cv.circle(160, 85, 22, (250, 170, 0), fill=True)
    cv.ellipse(45, 85, 30, 18, (120, 40, 180), fill=False)
    cv.poly([(100, 110), (130, 55), (145, 108)], (0, 0, 0))
    # exercise clipping / out-of-bounds safety
    cv.set(-5, 999, (1, 2, 3))
    cv.fill_rect(-20, -20, 30, 30, (0, 200, 200))
    cv.circle(198, 2, 15, (90, 90, 90))
    cv.blend(100, 60, (255, 0, 0), 0.5)
    out = "/tmp/pngcore-test.png"
    cv.save(out)
    data = open(out, "rb").read()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", "bad PNG signature"
    assert cv.get(-1, 0) == (0, 0, 0)
    # determinism check: re-save and compare bytes
    cv.save(out)
    assert open(out, "rb").read() == data, "output not deterministic"
    print("size:", len(data))
    print("sha256:", hashlib.sha256(data).hexdigest())
    print("signature OK, deterministic OK")
