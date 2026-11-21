"""main.py - Republic of Auralis passport spread (make.fun bounty, session D).

Original stdlib-only composition built on pngcore.Canvas, font.draw_text /
draw_text_wrapped and the art.py helpers. Deterministic: no randomness, no
timestamps, no network. Saves a 1024x724 spread to /output/entry.png.
"""

import hashlib
import math
import os

from pngcore import Canvas, save_png
from font import draw_text, draw_text_wrapped, text_width
from art import (guilloche, draw_emblem, draw_portrait, mrz_lines,
                 draw_stamp, draw_stamp_rect)

# --- palette ---------------------------------------------------------------
PAPER = (247, 240, 222)
TEAL = (13, 74, 74)
GOLD = (232, 196, 106)
LABEL = (70, 100, 100)
VALUE = (25, 25, 25)
PALE = (238, 232, 214)
GUIL_L = (225, 218, 196)
GUIL_R = (235, 228, 208)
RED_BROWN = (150, 60, 50)
BLUE = (40, 70, 140)
GREEN = (40, 110, 70)
GREY = (110, 110, 105)

W, H = 1024, 724
OUT = "/output/entry.png"


def field(cv, label, value, x, y, stacked=False, xmax=500,
          lsp=-0.5, vsp=-1.0):
    """One data field: small-caps label + near-black value.

    Inline puts the value right of the label on the same row; stacked puts
    the value 18px below the label. If an inline field would overflow xmax
    it is right-aligned to xmax instead. lsp/vsp are font spacing tweaks
    used only to keep long strings inside the page.
    """
    if stacked:
        draw_text(cv, label, x, y, 1.4, LABEL, spacing=lsp)
        draw_text(cv, value, x, y + 17, 1.8, VALUE, spacing=vsp)
        return
    lw = text_width(label, 1.4, spacing=lsp)
    vw = text_width(value, 2.0, spacing=vsp)
    total = lw + 6 + vw
    x0 = x if x + total <= xmax else xmax - total
    draw_text(cv, label, x0, y + 4, 1.4, LABEL, spacing=lsp)
    draw_text(cv, value, x0 + lw + 6, y, 2.0, VALUE, spacing=vsp)


def signature(cv, x, y):
    """Wavy ink line with the holder's name beneath it."""
    pts = []
    for i in range(0, 183, 3):
        pts.append((x + i, y + 3.0 * math.sin(i / 14.0) + 1.5 * math.sin(i / 5.0)))
    for i in range(len(pts) - 1):
        cv.line(int(round(pts[i][0])), int(round(pts[i][1])),
                int(round(pts[i + 1][0])), int(round(pts[i + 1][1])),
                (40, 55, 60), 1)
    draw_text(cv, "FREYA A. SOLBERG", x, y + 8, 1.2, (30, 35, 40), spacing=-1.0)


def left_page(cv):
    # Faint guilloche behind the emblem / upper data area.
    guilloche(cv, 20, 84, 470, 128, GUIL_L, step=7)

    # Header band.
    cv.fill_rect(0, 0, 508, 64, TEAL)
    draw_text(cv, "REPUBLIC OF AURALIS", 254, 8, 3.0, (255, 255, 255),
              align="center", spacing=-1.7)
    cv.fill_rect(0, 64, 508, 2, GOLD)          # thin gold rule under band
    draw_text(cv, "PASSPORT", 254, 72, 2.2, GOLD, align="center")

    # Coat of arms and portrait.
    draw_emblem(cv, 110, 150, 58, TEAL, GOLD)
    draw_portrait(cv, 28, 215, 165, 205)
    cv.rect(28, 215, 165, 205, TEAL, lw=1)     # thin teal frame

    # Data fields (pitch 34 for inline rows, 48 where a value stacks).
    field(cv, "TYPE", "P", 215, 222)
    field(cv, "CODE", "AUR", 311, 222)
    field(cv, "SEX", "F", 443, 222)
    field(cv, "PASSPORT NO.", "AU-4829137", 215, 254, stacked=True)
    field(cv, "SURNAME", "SOLBERG", 215, 302)
    field(cv, "GIVEN NAMES", "FREYA ANETTE", 215, 336, stacked=True)
    field(cv, "NATIONALITY", "AURALIC", 215, 384)
    field(cv, "DATE OF BIRTH", "12 MAY 1990", 215, 418, stacked=True)
    field(cv, "PLACE OF BIRTH", "LIORAN, AURALIS", 215, 466, stacked=True)
    field(cv, "DATE OF ISSUE", "14 MAR 2024", 215, 514, lsp=-3.0, vsp=-3.0)
    field(cv, "DATE OF EXPIRY", "13 MAR 2034", 215, 548, lsp=-3.0, vsp=-3.0)
    # Thin column divider: keeps the portrait-column block (authority
    # + signature) visually separate from the data column rows.
    cv.line(206, 424, 206, 560, (140, 165, 165), 1)

    # Authority: two short lines inside the portrait column (x < 215)
    # so it never collides with the data column at x >= 215.
    draw_text(cv, "AUTHORITY", 28, 500, 1.4, LABEL, spacing=-0.5)
    draw_text(cv, "PASSPORT OFFICE", 28, 517, 1.3, VALUE, spacing=-1.0)
    draw_text(cv, "LIORAN", 28, 539, 1.3, VALUE, spacing=-1.0)

    signature(cv, 28, 566)

    # MRZ on a pale strip.
    cv.fill_rect(16, 606, 476, 84, PALE)
    l1, l2 = mrz_lines("SOLBERG", "FREYA ANETTE", "AU4829137", "AUR",
                       "900512", "F", "340313")
    draw_text(cv, l1, 28, 620, 1.6, VALUE, spacing=-3.4)
    draw_text(cv, l2, 28, 648, 1.6, VALUE, spacing=-3.4)
    return l1, l2


def right_page(cv):
    # Faint security background across the whole visa page.
    guilloche(cv, 516, 0, 508, 724, GUIL_R, step=7)

    draw_text(cv, "VISAS", 540, 24, 2.6, TEAL)
    cv.line(540, 66, 980, 66, TEAL, 1)

    # Border-control stamps (all dated after the 14 MAR 2024 issue).
    draw_stamp_rect(cv, 540, 90, 200, 92,
                    ["ENTRY", "VESTMARK", "02 JUN 2024"], RED_BROWN)
    draw_stamp_rect(cv, 760, 90, 200, 92,
                    ["EXIT", "VESTMARK", "18 JUN 2024"], BLUE)
    draw_stamp(cv, 640, 300, 46,
               ["THALASSA", "ENTRY", "09 SEP 2025"], GREEN, angle_deg=-8)
    draw_stamp(cv, 850, 300, 46,
               ["THALASSA", "EXIT", "21 SEP 2025"], RED_BROWN, angle_deg=7)
    draw_stamp_rect(cv, 620, 420, 220, 92,
                    ["ARRIVAL", "PORT LIORAN", "22 SEP 2025"], BLUE)

    # Telling-detail box: Outer Isles permit + ferry levy.
    cv.fill_rect(540, 540, 440, 120, PALE)
    cv.rect(540, 540, 440, 120, TEAL, lw=1)
    draw_text_wrapped(
        cv,
        "OUTER ISLES PERMIT - landings only 01 NOV to 28 FEB. "
        "Mainland transit prohibited.",
        552, 542, 416, 1.5, (30, 50, 50), line_gap=0.2, spacing=-2.0)
    draw_text(cv, "FERRY LEVY PAID 12 KOR", 552, 634, 1.8, RED_BROWN,
              spacing=-1.0)

    draw_text(cv, "AURALIS - NORTHERN LIGHTS, NORTHERN SEAS", 540, 690,
              1.3, GREY, spacing=-1.5)


def gutter(cv):
    """Subtle vertical fold shadow around x=508..516."""
    for x in range(506, 519):
        a = 0.20 * max(0.0, 1.0 - abs(x - 512) / 6.5)
        if a <= 0:
            continue
        for y in range(H):
            cv.blend(x, y, (70, 58, 44), a)


def main():
    os.makedirs("/output", exist_ok=True)
    cv = Canvas(W, H, bg=PAPER)
    l1, l2 = left_page(cv)
    right_page(cv)
    gutter(cv)
    save_png(OUT, cv.w, cv.h, cv.px)

    data = open(OUT, "rb").read()
    print("size:", len(data))
    print("sha256:", hashlib.sha256(data).hexdigest())
    print(l1)
    print(l2)


if __name__ == "__main__":
    main()
