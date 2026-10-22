#!/usr/bin/env python3
"""
Generate the README images. Committed so the visuals can be regenerated
rather than re-drawn by hand when the wording changes.

    python3 assets/make_assets.py
"""

import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))

BG = (13, 17, 23)          # GitHub dark
PANEL = (22, 27, 34)
LINE = (48, 54, 61)
TEXT = (230, 237, 243)
MUTED = (125, 133, 144)
ACCENT = (236, 116, 68)    # warm, reads on dark
ACCENT_2 = (88, 166, 255)
GREEN = (63, 185, 80)

SF = "/System/Library/Fonts/SFNS.ttf"
MONO = "/System/Library/Fonts/SFNSMono.ttf"
FALLBACK = "/System/Library/Fonts/Supplemental/Arial.ttf"


def font(size, mono=False, weight=None):
    path = MONO if mono else SF
    try:
        f = ImageFont.truetype(path, size)
        if weight is not None and not mono:
            try:
                f.set_variation_by_axes([weight])
            except Exception:
                pass
        return f
    except OSError:
        return ImageFont.truetype(FALLBACK, size)


def rounded_panel(d, box, radius=14, fill=PANEL, outline=LINE, width=1):
    d.rounded_rectangle(box, radius=radius, fill=fill, outline=outline,
                        width=width)


# ---------------------------------------------------------------- banner
def banner():
    W, H = 1280, 640
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    # Soft glow behind the title. Drawn then blurred - a hard-edged ellipse
    # reads as a rendering artefact rather than light.
    glow = Image.new("RGB", (W, H), BG)
    gd = ImageDraw.Draw(glow)
    gd.ellipse([-260, -340, 700, 380], fill=(28, 38, 54))
    glow = glow.filter(ImageFilter.GaussianBlur(90))
    img = Image.blend(img, glow, 0.9)
    d = ImageDraw.Draw(img)

    d.text((80, 120), "/watch", font=font(104, weight=800), fill=ACCENT)
    d.text((80, 256),
           "Turn any social video\ninto a Claude Code skill.",
           font=font(40, weight=600), fill=TEXT, spacing=10)
    d.text((80, 376),
           "Downloads it, transcribes it, reads the\n"
           "frames and the caption, then writes a\n"
           "skill you can actually reuse.",
           font=font(22), fill=MUTED, spacing=10)

    chips = ["TikTok", "Reels", "YouTube", "X", "LinkedIn"]
    x = 80
    for c in chips:
        w = d.textlength(c, font=font(18)) + 30
        rounded_panel(d, [x, 492, x + w, 532], radius=20)
        d.text((x + w / 2, 512), c, font=font(18), fill=MUTED, anchor="mm")
        x += w + 10

    d.text((80, 560), "100% local  ·  no API keys  ·  no billing",
           font=font(21, weight=600), fill=GREEN)

    # terminal card on the right
    rounded_panel(d, [800, 150, 1216, 490], radius=16)
    for i, (dot, col) in enumerate(zip(range(3),
                                       [(255, 95, 86), (255, 189, 46),
                                        (39, 201, 63)])):
        d.ellipse([824 + i * 22, 174, 836 + i * 22, 186], fill=col)
    lines = [
        ("> /watch https://tiktok.com/...", TEXT),
        ("", TEXT),
        ("[watch] downloading", MUTED),
        ("[watch] 57s video", MUTED),
        ("[watch] transcribing", MUTED),
        ("[watch] sampling frames", MUTED),
        ("[watch] done", MUTED),
        ("  239 words, 340 caption words", MUTED),
        ("  14 frames (scene-change)", MUTED),
        ("", TEXT),
        ("skill written ->", GREEN),
        ("  swiftui-motion-polish", ACCENT_2),
    ]
    y = 208
    for text, col in lines:
        d.text((826, y), text, font=font(16, mono=True), fill=col)
        y += 23

    img.save(os.path.join(HERE, "banner.png"))
    print("banner.png")


# -------------------------------------------------------------- pipeline
def pipeline():
    W, H = 1280, 420
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    steps = [
        ("1", "Download", "yt-dlp", "video + caption\n+ site captions"),
        ("2", "Transcribe", "whisper", "local, offline\nor site captions"),
        ("3", "Sample", "ffmpeg", "frames at\nscene cuts"),
        ("4", "Read", "Claude", "transcript +\ncaption + frames"),
        ("5", "Classify", "—", "procedure?\nor just opinion?"),
        ("6", "Write", "skill-creator", "a skill you\ncan reuse"),
    ]

    pad, gap = 44, 16
    bw = (W - pad * 2 - gap * (len(steps) - 1)) / len(steps)
    top, bh = 112, 196

    d.text((pad, 50), "How it works", font=font(32, weight=700), fill=TEXT)

    for i, (num, title, tool, desc) in enumerate(steps):
        x = pad + i * (bw + gap)
        rounded_panel(d, [x, top, x + bw, top + bh], radius=14)

        d.ellipse([x + 18, top + 18, x + 44, top + 44], fill=ACCENT)
        d.text((x + 31, top + 30), num, font=font(15, weight=700),
               fill=BG, anchor="mm")

        d.text((x + 18, top + 58), title, font=font(23, weight=700), fill=TEXT)
        d.text((x + 18, top + 90), tool, font=font(15, mono=True),
               fill=ACCENT_2)
        d.text((x + 18, top + 120), desc, font=font(15), fill=MUTED,
               spacing=7)

        if i < len(steps) - 1:
            ax = x + bw + gap / 2
            d.line([ax - 5, top + bh / 2, ax + 5, top + bh / 2],
                   fill=LINE, width=2)

    d.text((pad, 352),
           "Claude cannot watch video. It reads a transcript, the post "
           "caption, and stills sampled at scene changes —",
           font=font(19), fill=MUTED)
    d.text((pad, 380),
           "which is enough for tutorials, walkthroughs and advice.",
           font=font(19), fill=MUTED)

    img.save(os.path.join(HERE, "pipeline.png"))
    print("pipeline.png")


# ------------------------------------------------------------ three inputs
def sources():
    W, H = 1280, 430
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    d.text((44, 44), "Three sources, because each carries something the "
                     "others do not",
           font=font(29, weight=700), fill=TEXT)

    cards = [
        ("Speech", ACCENT_2,
         "The narrative and the\nreasoning. What the\ncreator chose to say\nout loud."),
        ("Caption", ACCENT,
         "The rest of the list.\n\"Top 4 in the video,\nfull list in the caption\"\n"
         "is a standard move."),
        ("Frames", GREEN,
         "On-screen text, UI\nstate, before/after\ncomparisons, numbers\nin overlays."),
    ]

    pad, gap = 44, 20
    cw = (W - pad * 2 - gap * 2) / 3
    top, ch = 118, 212

    for i, (title, col, body) in enumerate(cards):
        x = pad + i * (cw + gap)
        rounded_panel(d, [x, top, x + cw, top + ch], radius=16)
        d.rounded_rectangle([x, top, x + 5, top + ch], radius=3, fill=col)
        d.text((x + 28, top + 26), title, font=font(26, weight=700), fill=col)
        d.text((x + 28, top + 76), body, font=font(18), fill=MUTED, spacing=9)

    d.text((44, 364),
           "Skipping the caption cost 340 words on the first real run — more "
           "content than the 239 spoken.",
           font=font(19), fill=TEXT)

    img.save(os.path.join(HERE, "sources.png"))
    print("sources.png")


if __name__ == "__main__":
    banner()
    pipeline()
    sources()
