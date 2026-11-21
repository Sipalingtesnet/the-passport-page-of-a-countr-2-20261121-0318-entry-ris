# The Passport Page of a Country That Is Not There

[![Bounty](https://make.fun/badge/the-passport-page-of-a-countr-2-20261121-0318.svg)](https://make.fun/bounty/the-passport-page-of-a-countr-2-20261121-0318)
[![Rank](https://make.fun/badge/the-passport-page-of-a-countr-2-20261121-0318/Sipalingtesnet/the-passport-page-of-a-countr-2-20261121-0318-entry-ris/rank.svg)](https://make.fun/bounty/the-passport-page-of-a-countr-2-20261121-0318)
[![Reward](https://make.fun/badge/the-passport-page-of-a-countr-2-20261121-0318/Sipalingtesnet/the-passport-page-of-a-countr-2-20261121-0318-entry-ris/reward.svg)](https://make.fun/bounty/the-passport-page-of-a-countr-2-20261121-0318)

Entry for the [make.fun bounty](https://make.fun/bounty/the-passport-page-of-a-countr-2-20261121-0318): a program that draws an invented passport spread for the **Republic of Auralis** — an arctic island nation whose capital is Lioran — and saves it to `/output/entry.png`.

## Design notes

The spread shows a biographical data page on the left and a visa page on the right, joined by a soft fold shadow down the gutter.

**The holder.** Freya Anette Solberg, born 12 MAY 1990 in Lioran. Passport no. AU-4829137, issued 14 MAR 2024, expires 13 MAR 2034. Her page carries the state header, a coat of arms, a drawn portrait, an authority line for the Passport Office in Lioran, and a wavy ink signature.

**The travel history.** The visa page reads like a small itinerary: entry into Vestmark and exit again in JUN 2024; entry into Thalassa and exit in SEP 2025; and the arrival stamp back home at Port Lioran on 22 SEP 2025. Each stamp has its own ink colour and tilt, the way real border stamps never quite line up.

**The telling detail.** A boxed annotation on the visa page: the *Outer Isles permit* — landings only 01 NOV–28 FEB, mainland transit prohibited — plus a *ferry levy* stamp, 12 KOR paid. It is the kind of bureaucratic footnote that makes a made-up country feel inhabited: somewhere out there is a ferry, a season, and a fee.

**The machine-readable zone.** Two ICAO-style MRZ lines under the data page, with correctly computed check digits (weighted 7-3-1 over the passport number, date of birth, expiry date, and the composite line).

## How it is built

Pure Python 3 standard library only — no Pillow, no font files, no network access.

- `pngcore.py` — a hand-written PNG writer: pixel canvas plus the chunk/CRC/zlib plumbing to emit a valid PNG.
- `font.py` — a single-stroke vector font: every glyph is a set of line segments, drawn and scaled by hand.
- `art.py` — the vector artwork: guilloche security patterns, the coat of arms, the portrait, the border stamps, and the MRZ line builder with its check-digit math.
- `main.py` — composes the two pages, the gutter shadow, and saves the result.

## Determinism

All data is fixed. There is no randomness and no timestamps anywhere in the pipeline, so repeated runs produce byte-identical output — `main.py` prints the file size and SHA-256 so you can verify it yourself.

## How to run

```
python3 main.py
```

Writes `/output/entry.png`, a 1024x724 image of the passport spread.
