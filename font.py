"""font.py - single-stroke (engraver's) vector font and text drawing.

Stdlib only. Glyphs live in a 10 x 14 unit box: x in 0..10, y in 0..14
with y=0 at the cap top and y=14 at the baseline. Every glyph is a list
of strokes; a stroke is a list of (x, y) points drawn as an open polyline.
Curves are short-segment arc approximations, no filled shapes.

Lowercase is not stored separately: draw_text maps a-z onto A-Z because
passport lettering is printed in capitals.
"""

import math

from pngcore import Canvas  # noqa: F401  (re-exported for convenience)


def _arc(cx, cy, rx, ry, a0, a1, n=8):
    """Ellipse arc as n+1 points. Angles in degrees, y-down convention:
    0 = +x (right), 90 = +y (down), so -90 is the top of the ellipse.
    Sweeps from a0 to a1 (either direction)."""
    pts = []
    for i in range(n + 1):
        a = math.radians(a0 + (a1 - a0) * i / n)
        pts.append((round(cx + rx * math.cos(a), 3),
                    round(cy + ry * math.sin(a), 3)))
    return pts


# --- glyph table -----------------------------------------------------------
# Strokes keep at least ~1.5 units between parallel runs so lettering stays
# legible at small sizes. Corners may of course meet at a point.

FONT = {
    " ": [],
    "A": [[(1, 14), (5, 0), (9, 14)], [(3.5, 9), (6.5, 9)]],
    "B": [[(1, 14), (1, 0), (5, 0)] + _arc(5, 3.5, 4, 3.5, -90, 90) + [(1, 7)],
          [(1, 7), (5.5, 7)] + _arc(5.5, 10.5, 3.5, 3.5, -90, 90) + [(1, 14)]],
    "C": [_arc(5, 7, 4, 7, -45, -315, 12)],
    "D": [[(1, 14), (1, 0), (4.5, 0)] + _arc(4.5, 7, 4.5, 7, -90, 90) + [(1, 14)]],
    "E": [[(9, 0), (1, 0), (1, 14), (9, 14)], [(1, 7), (7, 7)]],
    "F": [[(9, 0), (1, 0), (1, 14)], [(1, 7), (7, 7)]],
    "G": [_arc(5, 7, 4, 7, -45, -360, 12), [(9, 7), (5.5, 7)]],
    "H": [[(1, 0), (1, 14)], [(9, 0), (9, 14)], [(1, 7), (9, 7)]],
    "I": [[(2.5, 0), (7.5, 0)], [(5, 0), (5, 14)], [(2.5, 14), (7.5, 14)]],
    "J": [[(7, 0), (7, 11)] + _arc(4.5, 11, 2.5, 3, 0, 180, 6)],
    "K": [[(1, 0), (1, 14)], [(9, 0), (1, 7.5)], [(4, 4.7), (9, 14)]],
    "L": [[(1, 0), (1, 14), (9, 14)]],
    "M": [[(1, 14), (1, 0), (5, 8), (9, 0), (9, 14)]],
    "N": [[(1, 14), (1, 0), (9, 14), (9, 0)]],
    "O": [_arc(5, 7, 4, 7, 0, 360, 16)],
    "P": [[(1, 14), (1, 0), (5, 0)] + _arc(5, 3.5, 4, 3.5, -90, 90) + [(1, 7)]],
    "Q": [_arc(5, 7, 4, 7, 0, 360, 16), [(6.5, 10.5), (9.5, 14)]],
    "R": [[(1, 14), (1, 0), (5, 0)] + _arc(5, 3.5, 4, 3.5, -90, 90) + [(1, 7)],
          [(4.5, 7), (9, 14)]],
    "S": [_arc(5, 3.5, 4, 3.5, -20, -270, 8) + _arc(5, 10.5, 4, 3.5, -90, 160, 8)],
    "T": [[(1, 0), (9, 0)], [(5, 0), (5, 14)]],
    "U": [[(1, 0), (1, 10)] + _arc(5, 10, 4, 4, 180, 0, 8) + [(9, 0)]],
    "V": [[(1, 0), (5, 14), (9, 0)]],
    "W": [[(0.5, 0), (2.5, 14), (5, 4), (7.5, 14), (9.5, 0)]],
    "X": [[(1, 0), (9, 14)], [(9, 0), (1, 14)]],
    "Y": [[(1, 0), (5, 7), (9, 0)], [(5, 7), (5, 14)]],
    "Z": [[(1, 0), (9, 0), (1, 14), (9, 14)]],
    "0": [_arc(5, 7, 4, 7, 0, 360, 16), [(6.8, 3.5), (3.2, 10.5)]],
    "1": [[(3, 2.5), (5.5, 0), (5.5, 14)], [(2.5, 14), (8.5, 14)]],
    "2": [_arc(5, 4, 4, 4, 180, 420, 10) + [(1, 14), (9, 14)]],
    "3": [_arc(5, 3.5, 4, 3.5, 200, 450, 8) + _arc(5, 10.5, 4, 3.5, -90, 150, 8)],
    "4": [[(7, 14), (7, 0), (1, 10), (9, 10)]],
    "5": [[(8.5, 0), (1.5, 0), (1.5, 6.5), (5, 6.5)]
          + _arc(5, 10.25, 4, 3.75, -90, 150, 8)],
    "6": [_arc(5.5, 7, 4.5, 7, -50, -200, 8) + _arc(5, 10.25, 4, 3.75, 200, 560, 12)],
    "7": [[(1, 0), (9, 0), (3.5, 14)]],
    "8": [_arc(5, 3.5, 3.5, 3.5, 0, 360, 12), _arc(5, 10.5, 4, 3.5, 0, 360, 12)],
    "9": [_arc(5, 3.75, 4, 3.75, 0, 360, 12),
          [(9, 3.75), (9, 10)] + _arc(5, 10, 4, 4, 0, 150, 6)],
    ".": [[(4.5, 13.5), (5.5, 13.5)]],
    ",": [[(5.6, 12.2), (4.4, 14)]],
    "-": [[(2.5, 7), (7.5, 7)]],
    "/": [[(8.5, 0), (1.5, 14)]],
    "<": [[(8, 0), (1.5, 7), (8, 14)]],
    ">": [[(2, 0), (8.5, 7), (2, 14)]],
    ":": [[(4.5, 4), (5.5, 4)], [(4.5, 10), (5.5, 10)]],
    "(": [_arc(7.5, 7, 4, 7, 100, 260, 8)],
    ")": [_arc(2.5, 7, 4, 7, 80, -80, 8)],
    "'": [[(5.4, 0), (4.6, 3.5)]],
    "&": [_arc(5, 3.5, 3.3, 3.5, -40, -270, 8) + [(1.5, 10.8)]
          + _arc(5, 10.5, 3.5, 3.5, 180, -60, 8) + [(8.8, 5.6)]],
    "+": [[(5, 3.5), (5, 10.5)], [(1.5, 7), (8.5, 7)]],
    "%": [[(8.5, 0), (1.5, 14)],
          _arc(2.8, 2.8, 1.8, 1.8, 0, 360, 8),
          _arc(7.2, 11.2, 1.8, 1.8, 0, 360, 8)],
    "!": [[(5, 0), (5, 9.5)], [(4.5, 13.5), (5.5, 13.5)]],
    "?": [_arc(5, 4, 4, 4, 180, 450, 10) + [(5, 10.5)],
          [(4.5, 13.5), (5.5, 13.5)]],
    "=": [[(2, 5), (8, 5)], [(2, 9), (8, 9)]],
}


# --- text metrics and drawing ----------------------------------------------

def text_width(text, scale, spacing=1.0):
    """Advance width of text in pixels: (10 + spacing) * scale per character
    (spaces advance like any other glyph)."""
    return len(text) * (10.0 + spacing) * scale


def draw_text(canvas, text, x, y, scale, color, align="left", spacing=1.0, lw=None):
    """Draw text with its cap top at pixel y. scale = pixels per font unit.
    align left/center/right anchors the whole string at x. Unknown characters
    are skipped but still advance. Returns the total advance width in pixels.
    """
    if not isinstance(text, str):
        text = str(text)
    if lw is None:
        lw = max(1, int(round(scale * 0.22)))
    adv = (10.0 + spacing) * scale
    width = len(text) * adv
    if align == "center":
        x0 = x - width / 2.0
    elif align == "right":
        x0 = x - width
    else:
        x0 = x
    for ch in text:
        key = ch.upper() if "a" <= ch <= "z" else ch
        strokes = FONT.get(key)
        if strokes:
            for stroke in strokes:
                for i in range(len(stroke) - 1):
                    ax, ay = stroke[i]
                    bx, by = stroke[i + 1]
                    canvas.line(int(round(x0 + ax * scale)),
                                int(round(y + ay * scale)),
                                int(round(x0 + bx * scale)),
                                int(round(y + by * scale)), color, lw)
        x0 += adv
    return width


def draw_text_wrapped(canvas, text, x, y, max_w, scale, color, line_gap=0.35,
                      align="left", spacing=1.0):
    """Word-wrap text into max_w pixels and draw each line. Line height is
    14*scale*(1+line_gap). align anchors the text box (left edge at x, width
    max_w). Words wider than max_w are hard-broken. Returns the y coordinate
    just below the last line (the next line's top), or y if nothing drawn.
    """
    adv = (10.0 + spacing) * scale
    line_h = 14.0 * scale * (1.0 + line_gap)

    lines = []
    cur = ""
    for word in text.split():
        # Hard-break words that cannot fit on a line of their own.
        while len(word) > 1 and adv > 0 and len(word) * adv > max_w:
            n = max(1, int(max_w // adv))
            if cur:
                lines.append(cur)
                cur = ""
            lines.append(word[:n])
            word = word[n:]
        if not word:
            continue
        cand = word if not cur else cur + " " + word
        if not cur or len(cand) * adv <= max_w:
            cur = cand
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)

    if align == "center":
        ax = x + max_w / 2.0
    elif align == "right":
        ax = x + max_w
    else:
        ax = x
    cy = y
    for ln in lines:
        draw_text(canvas, ln, ax, cy, scale, color, align=align, spacing=spacing)
        cy += line_h
    return cy
