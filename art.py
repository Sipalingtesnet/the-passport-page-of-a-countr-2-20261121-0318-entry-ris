"""art.py - vector artwork for the Republic of Auralis passport page.

Stdlib only, built on pngcore.Canvas and the engraver's font in font.py.
Deterministic: no randomness, no timestamps, no network. All drawing is
clipped to the canvas (and to local boxes where noted).
"""

import math

from pngcore import Canvas
from font import draw_text, text_width


# --- small shared helpers ---------------------------------------------------

def _star(canvas, cx, cy, ro, color, points=5, inner=0.45):
    """Filled n-point star centred on (cx, cy), outer radius ro."""
    pts = []
    for i in range(points * 2):
        r = ro if i % 2 == 0 else ro * inner
        a = math.radians(-90 + i * 180.0 / points)
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    canvas.poly(pts, color)


def _clip_polyline(canvas, pts, box, color, alpha):
    """Draw a polyline clipped to box=(x,y,w,h), blended at alpha.

    Pixels outside the box are skipped; Canvas.blend also guards the
    canvas edge, so nothing can leak past either boundary.
    """
    bx, by, bw, bh = box
    x1, y1 = bx + bw - 1, by + bh - 1
    for i in range(len(pts) - 1):
        ax, ay = int(round(pts[i][0])), int(round(pts[i][1]))
        bx2, by2 = int(round(pts[i + 1][0])), int(round(pts[i + 1][1]))
        for px, py in canvas._bresenham(ax, ay, bx2, by2):
            if bx <= px <= x1 and by <= py <= y1:
                canvas.blend(px, py, color, alpha)


def _wave_pts(x0, x1, y0, amp, period, phase, dx=2.0):
    """Sampled sine-wave polyline from x0 to x1 around baseline y0."""
    pts = []
    x = x0
    while x <= x1:
        pts.append((x, y0 + amp * math.sin(2 * math.pi * (x - x0) / period + phase)))
        x += dx
    pts.append((x1, y0 + amp * math.sin(2 * math.pi * (x1 - x0) / period + phase)))
    return pts


# --- guilloche background ----------------------------------------------------

def guilloche(canvas, x, y, w, h, color, step=7):
    """Fine security-pattern fill: sine rows plus two families of
    concentric arcs, all thin and low-contrast, clipped to the rectangle.
    """
    if w <= 0 or h <= 0:
        return
    step = max(3, int(step))
    box = (x, y, w, h)
    alpha = 0.30

    # Family 1: horizontal sine waves, phase shifted row by row.
    period = max(24.0, w / 3.0)
    amp = step * 0.55
    j = 0
    yy = y + step // 2
    while yy < y + h:
        pts = _wave_pts(x, x + w, yy, amp, period, j * 0.9)
        _clip_polyline(canvas, pts, box, color, alpha)
        yy += step
        j += 1

    # Families 2 and 3: concentric arcs radiating from virtual centres
    # just outside the left and right edges of the rectangle.
    for side in (-1, 1):
        ccx = x - 0.25 * w if side < 0 else x + 1.25 * w
        ccy = y + h / 2.0
        a0, a1 = (-60, 60) if side < 0 else (120, 240)
        rr = 0.35 * w
        while rr <= 1.6 * w:
            pts = []
            for k in range(49):
                a = math.radians(a0 + (a1 - a0) * k / 48.0)
                pts.append((ccx + rr * math.cos(a), ccy + rr * math.sin(a)))
            _clip_polyline(canvas, pts, box, color, alpha)
            rr += step * 1.6


# --- coat of arms -------------------------------------------------------------

def draw_emblem(canvas, cx, cy, r, ink, accent):
    """Round seal of the Republic of Auralis: double outer ring, tick
    marks, inner ring, and a scene of aurora bands over a mountain with
    a wave line at the base and a star above. Centred on (cx, cy).
    """
    if r <= 0:
        return
    # Rings and radial ticks (the engraved seal border).
    canvas.circle(cx, cy, r, ink, fill=False)
    canvas.circle(cx, cy, r * 0.93, ink, fill=False)
    canvas.circle(cx, cy, r * 0.78, ink, fill=False)
    for k in range(24):
        a = math.radians(k * 15.0)
        canvas.line(int(round(cx + r * 0.80 * math.cos(a))),
                    int(round(cy + r * 0.80 * math.sin(a))),
                    int(round(cx + r * 0.91 * math.cos(a))),
                    int(round(cy + r * 0.91 * math.sin(a))), ink, 1)

    # Scene inside the inner ring.
    ri = r * 0.74
    lw_band = max(1, int(round(r * 0.03)))
    lw_fine = max(1, int(round(r * 0.02)))

    # Star above.
    _star(canvas, cx, cy - ri * 0.68, ri * 0.12, accent)

    # Aurora: three wavy bands, kept inside the inner disc.
    for i, yf in enumerate((-0.42, -0.28, -0.14)):
        pts = _wave_pts(cx - ri * 0.68, cx + ri * 0.68, cy + ri * yf,
                        ri * 0.06, ri * 0.9, i * 1.1, dx=max(1.0, ri / 24))
        for k in range(len(pts) - 1):
            canvas.line(int(round(pts[k][0])), int(round(pts[k][1])),
                        int(round(pts[k + 1][0])), int(round(pts[k + 1][1])),
                        accent, lw_band)

    # Mountain triangle.
    canvas.poly([(cx - ri * 0.66, cy + ri * 0.52),
                 (cx, cy - ri * 0.05),
                 (cx + ri * 0.66, cy + ri * 0.52)], ink)

    # Wave lines at the base (water under the mountain).
    for yf, span in ((0.66, 0.55), (0.78, 0.42)):
        pts = _wave_pts(cx - ri * span, cx + ri * span, cy + ri * yf,
                        ri * 0.04, ri * 0.5, 0.0, dx=max(1.0, ri / 24))
        for k in range(len(pts) - 1):
            canvas.line(int(round(pts[k][0])), int(round(pts[k][1])),
                        int(round(pts[k + 1][0])), int(round(pts[k + 1][1])),
                        ink, lw_fine)


# --- portrait ------------------------------------------------------------------

def draw_portrait(canvas, x, y, w, h):
    """Flat engraved-style passport portrait of Freya Anette Solberg:
    blue-grey guilloche background, head-and-shoulders figure with an
    ash-blonde bob, calm thin-stroke features, navy jacket, light collar.
    Everything stays inside (x, y, w, h).
    """
    if w <= 0 or h <= 0:
        return
    cx = x + w / 2.0

    bg = (172, 182, 192)
    bg_line = (150, 161, 173)
    skin = (226, 190, 164)
    skin_shade = (196, 150, 122)
    hair = (112, 98, 76)
    hair_dark = (86, 74, 58)
    jacket = (34, 44, 66)
    jacket_dark = (24, 32, 50)
    collar = (228, 230, 232)
    ink = (66, 52, 46)
    mouth = (162, 96, 88)

    # Background with faint guilloche arcs.
    canvas.fill_rect(x, y, w, h, bg)
    guilloche(canvas, x, y, w, h, bg_line, step=6)

    # Hair back (crown of the bob).
    canvas.ellipse(cx, y + h * 0.33, w * 0.27, h * 0.27, hair, fill=True)

    # Neck, then jacket over its lower part.
    canvas.ellipse(cx, y + h * 0.62, w * 0.085, h * 0.08, skin, fill=True)
    canvas.poly([(x + w * 0.05, y + h),
                 (x + w * 0.13, y + h * 0.79),
                 (x + w * 0.34, y + h * 0.705),
                 (cx - w * 0.09, y + h * 0.68),
                 (cx + w * 0.09, y + h * 0.68),
                 (x + w * 0.66, y + h * 0.705),
                 (x + w * 0.87, y + h * 0.79),
                 (x + w * 0.95, y + h)], jacket)
    # Lapel seams for the engraved look.
    canvas.line(int(cx - w * 0.14), int(y + h * 0.73),
                int(cx - w * 0.04), int(y + h * 0.99), jacket_dark, 1)
    canvas.line(int(cx + w * 0.14), int(y + h * 0.73),
                int(cx + w * 0.04), int(y + h * 0.99), jacket_dark, 1)

    # Light collar: two flaps meeting in a V.
    canvas.poly([(cx - w * 0.15, y + h * 0.695),
                 (cx - w * 0.01, y + h * 0.715),
                 (cx - w * 0.09, y + h * 0.83)], collar)
    canvas.poly([(cx + w * 0.15, y + h * 0.695),
                 (cx + w * 0.01, y + h * 0.715),
                 (cx + w * 0.09, y + h * 0.83)], collar)

    # Face oval.
    canvas.ellipse(cx, y + h * 0.40, w * 0.185, h * 0.24, skin, fill=True)

    # Bob side panels framing the face, with rounded ends.
    for s in (-1, 1):
        left = min(cx + s * w * 0.16, cx + s * w * 0.28)
        canvas.fill_rect(int(left), int(y + h * 0.33),
                         int(w * 0.12), int(h * 0.29), hair)
        canvas.ellipse(cx + s * w * 0.22, y + h * 0.62,
                       w * 0.06, h * 0.035, hair, fill=True)
    # Fringe across the forehead.
    canvas.ellipse(cx, y + h * 0.205, w * 0.19, h * 0.08, hair, fill=True)

    # Features: thin, calm strokes.
    for s in (-1, 1):
        ex = cx + s * w * 0.078
        ey = y + h * 0.40
        canvas.ellipse(ex, ey, w * 0.034, h * 0.016, ink, fill=False)
        canvas.circle(ex, ey, max(1.0, w * 0.011), ink, fill=True)
        # Brow: a gentle three-point arch.
        canvas.line(int(cx + s * w * 0.045), int(y + h * 0.358),
                    int(cx + s * w * 0.080), int(y + h * 0.346), hair_dark, 1)
        canvas.line(int(cx + s * w * 0.080), int(y + h * 0.346),
                    int(cx + s * w * 0.115), int(y + h * 0.356), hair_dark, 1)
    # Nose: one soft L-shaped stroke.
    canvas.line(int(cx + w * 0.004), int(y + h * 0.415),
                int(cx - w * 0.014), int(y + h * 0.50), skin_shade, 1)
    canvas.line(int(cx - w * 0.014), int(y + h * 0.50),
                int(cx + w * 0.020), int(y + h * 0.508), skin_shade, 1)
    # Closed-lip mouth.
    canvas.line(int(cx - w * 0.045), int(y + h * 0.556),
                int(cx), int(y + h * 0.562), mouth, 1)
    canvas.line(int(cx), int(y + h * 0.562),
                int(cx + w * 0.045), int(y + h * 0.556), mouth, 1)

    # Thin frame so the portrait reads as an engraved plate.
    canvas.rect(x, y, w, h, (120, 130, 142), lw=1)


# --- MRZ (ICAO 9303, TD3) ------------------------------------------------------

def mrz_check(s):
    """ICAO 9303 check digit: '<'=0, digits face value, A-Z = 10..35,
    weights 7,3,1 repeating, result is str(sum % 10)."""
    total = 0
    for i, ch in enumerate(s):
        if ch == '<':
            v = 0
        elif '0' <= ch <= '9':
            v = ord(ch) - ord('0')
        elif 'A' <= ch <= 'Z':
            v = ord(ch) - ord('A') + 10
        else:
            raise ValueError("invalid MRZ character: %r" % ch)
        total += v * (7, 3, 1)[i % 3]
    return str(total % 10)


def _mrz_clean(s):
    """Uppercase, spaces to '<', drop anything outside A-Z 0-9 '<'."""
    return ''.join(c for c in s.upper().replace(' ', '<')
                   if c == '<' or 'A' <= c <= 'Z' or '0' <= c <= '9')


def mrz_lines(surname, given, number, nationality, birth, sex, expiry):
    """Two 44-character TD3 MRZ lines with every check digit computed.

    Line 2 layout (ICAO 9303): number(9)+check, nationality(3),
    birth(6)+check, sex(1), expiry(6)+check, personal number(14 '<'),
    its check ('0'), then the composite check over
    number+check + birth+check + expiry+check + personal number+check.
    """
    surname = _mrz_clean(surname)
    given = _mrz_clean(given)
    nat = _mrz_clean(nationality)[:3].ljust(3, '<')
    num = _mrz_clean(number)[:9].ljust(9, '<')
    birth = _mrz_clean(birth)[:6].ljust(6, '<')
    expiry = _mrz_clean(expiry)[:6].ljust(6, '<')
    sex = _mrz_clean(sex)[:1]
    if sex not in ('M', 'F'):
        sex = '<'

    line1 = ('P<' + nat + surname + '<<' + given).ljust(44, '<')[:44]

    personal = '<' * 14
    body = (num + mrz_check(num) + nat + birth + mrz_check(birth)
            + sex + expiry + mrz_check(expiry) + personal + mrz_check(personal))
    # Composite check: ICAO positions 1-10, 14-20, 22-43 of line 2
    # (doc number+check, birth+check, expiry+check+personal+check).
    composite = body[0:10] + body[13:20] + body[21:43]
    line2 = body + mrz_check(composite)

    assert len(line1) == 44, "MRZ line 1 must be 44 chars"
    assert len(line2) == 44, "MRZ line 2 must be 44 chars"
    return line1, line2


# --- border-control stamps ------------------------------------------------------

# Sentinel background for the offscreen stamp buffer; any pixel still equal
# to this after drawing is treated as transparent during the rotated blit.
_STAMP_KEY = (255, 0, 255)


def draw_stamp(canvas, cx, cy, r, lines, color, angle_deg=0):
    """Round border-control stamp: two concentric circles, stacked centred
    text (base scale ~1.1, shrunk to fit), and a small star below. Rendered
    upright on an offscreen buffer, then blit-rotated by angle_deg with a
    slight fade for an inked feel. Legible at r = 34..46.
    """
    if r <= 0:
        return
    lines = [str(t) for t in lines]
    size = int(2 * r + 4)
    c = size / 2.0
    tmp = Canvas(size, size, bg=_STAMP_KEY)

    tmp.circle(c, c, r, color, fill=False)
    tmp.circle(c, c, r * 0.86, color, fill=False)

    inner = r * 0.86
    s = 1.1
    if lines:
        widest = max(text_width(t, s) for t in lines)
        avail_w = 2 * inner * 0.82
        if widest > avail_w:
            s *= avail_w / widest
        gap = max(2.0, 3.0 * s / 1.1)
        total = len(lines) * 14 * s + (len(lines) - 1) * gap
        avail_h = 2 * inner * 0.66
        if total > avail_h:
            s *= avail_h / total
            gap = max(2.0, 3.0 * s / 1.1)
            total = len(lines) * 14 * s + (len(lines) - 1) * gap
        ty = c - total / 2.0 - r * 0.10
        for t in lines:
            draw_text(tmp, t, c, ty, s, color, align="center")
            ty += 14 * s + gap

    # Small star below the text block.
    _star(tmp, c, c + inner * 0.66, max(2.0, r * 0.10), color, points=5)

    # Rotated blit with a faint ink alpha.
    a = math.radians(-angle_deg)
    ca, sa = math.cos(a), math.sin(a)
    ext = int(r + 2)
    for dy in range(-ext, ext + 1):
        for dx in range(-ext, ext + 1):
            sx = int(round(c + dx * ca - dy * sa))
            sy = int(round(c + dx * sa + dy * ca))
            if 0 <= sx < size and 0 <= sy < size:
                px = tmp.get(sx, sy)
                if px != _STAMP_KEY:
                    canvas.blend(cx + dx, cy + dy, px, 0.85)


def draw_stamp_rect(canvas, x, y, w, h, lines, color):
    """Rectangular entry/exit stamp: double border, first line bold and
    larger, remaining lines smaller, all stacked and centred.
    """
    if w <= 8 or h <= 8:
        return
    lines = [str(t) for t in lines]
    canvas.rect(x, y, w, h, color, lw=2)
    canvas.rect(x + 4, y + 4, w - 8, h - 8, color, lw=1)
    if not lines:
        return

    inner_w = w - 16
    inner_h = h - 14
    s1 = min(1.25, inner_w / max(1.0, text_width(lines[0], 1.0)),
             inner_h * 0.34 / 14.0)
    s2 = s1 * 0.72
    for t in lines[1:]:
        tw = text_width(t, s2)
        if tw > inner_w:
            s2 *= inner_w / tw
    gap = max(2.0, 3.0 * s2)
    total = 14 * s1 + (len(lines) - 1) * (14 * s2 + gap)
    if total > inner_h:
        k = inner_h / total
        s1 *= k
        s2 *= k
        gap *= k
        total = 14 * s1 + (len(lines) - 1) * (14 * s2 + gap)

    ty = y + h / 2.0 - total / 2.0
    draw_text(canvas, lines[0], x + w / 2.0, ty, s1, color, align="center",
              lw=max(1, int(round(s1 * 0.32))))
    ty += 14 * s1 + gap
    for t in lines[1:]:
        draw_text(canvas, t, x + w / 2.0, ty, s2, color, align="center")
        ty += 14 * s2 + gap


# --- self-test ------------------------------------------------------------------

if __name__ == "__main__":
    import hashlib

    cv = Canvas(700, 420, bg=(255, 255, 255))

    # Guilloche panel, emblem, portrait, and both stamp kinds.
    guilloche(cv, 20, 300, 380, 100, (150, 160, 175), step=7)
    draw_emblem(cv, 110, 120, 70, (40, 50, 80), (70, 130, 150))
    draw_portrait(cv, 250, 60, 150, 190)
    draw_stamp(cv, 520, 110, 42, ["AURALIS", "PASSPORT CTRL", "21 NOV 2026"],
               (90, 60, 120), angle_deg=-12)
    draw_stamp_rect(cv, 450, 250, 210, 120,
                    ["ENTRY", "REPUBLIC OF AURALIS", "21 NOV 2026", "AU4829137"],
                    (120, 50, 50))

    # Known ICAO 9303 worked example: L898902C3 -> 6.
    assert mrz_check("L898902C3") == "6", "ICAO check-digit example failed"
    assert mrz_check("<<<") == "0"

    l1, l2 = mrz_lines("SOLBERG", "FREYA ANETTE", "AU4829137", "AUR",
                       "900512", "F", "340313")
    assert len(l1) == 44 and len(l2) == 44

    out = "/tmp/art-test.png"
    cv.save(out)
    data = open(out, "rb").read()
    assert data[:8] == b"\x89PNG\r\n\x1a\x0a", "bad PNG signature"
    print("size:", len(data))
    print("sha256:", hashlib.sha256(data).hexdigest())
    print(l1)
    print(l2)
    print("self-test OK")
