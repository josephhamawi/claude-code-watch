# Example: one reel, two skills

A worked example of what `/watch` actually produces, using the first real
run of the plugin.

**Input**: a 57-second Instagram reel — an indie developer showing how they
made their SwiftUI finance app feel premium, day 10 of a 14-day build.

```
/watch https://www.instagram.com/reel/Dd9unmGyVmp/
```

## What the pack contained

```
watch-reel/
├── MANIFEST.md        what was produced
├── transcript.txt     239 words  (faster-whisper, no site captions)
├── caption.txt        340 words  ← more than was spoken
├── frames/            14 stills at scene changes
├── meta.json          title, uploader, duration, description
└── video.mp4
```

## What each source gave

**The transcript** carried four techniques and the reasoning behind them:
roll numbers instead of swapping them, keep animations near 0.2s, use
skeleton loaders rather than spinners, add a slow moving background.

**The frames** carried the specifics that were never said: the actual
before/after values ($300 → $1,250), a spinner-versus-skeleton comparison,
and a "normal vs Reduce Motion on" split screen that the narration skipped
entirely.

**The caption** carried the rest of the list — five further techniques, a
correction, and an entirely separate workflow:

- haptics via `.sensoryFeedback`, matched to meaning
- buttons that shrink slightly when pressed
- a launch screen matching the app, to kill the white flash
- every screen checked at the largest Dynamic Type sizes
- Face ID plus a one-tap privacy lock

It also **corrected** the video. The narration described a skeleton loader
in general terms; the caption named the actual API, SwiftUI's built-in
`.redacted(reason: .placeholder)`. A transcript-only tool would have
produced a hand-rolled implementation of something the framework already
provides.

And it described a complete **app icon workflow** that the video never
mentioned, which became a second skill.

## What was produced

### `swiftui-motion-polish`

Eleven points across motion and touch detail: rolling numbers, the 0.2s
default with one reserved celebration moment, redacted skeleton loaders,
the gated living background, haptics, press feedback, the launch screen,
Dynamic Type checks, and an eight-question audit for reviewing an existing
app.

### `ios-app-icon`

The icon workflow, plus two scripts that were worth writing because the
work is mechanical and repeated:

- `preview_sizes.py` renders an icon at all eight sizes iOS actually uses,
  as one contact sheet — the shrink test that decides whether a concept
  survives
- `check_icon.py` catches what App Store Connect rejects after upload:
  wrong dimensions, a real alpha channel, a non-grayscale tinted variant

## How claims were handled

The platform APIs are Apple's and verifiable, so they went in as fact.

The judgement calls — "about ten concepts", "0.2 seconds", "0.96 press
scale", "reserve one celebration" — are one developer's taste, stated on
camera without measurement. Both skills record that explicitly:

> The specific judgements — the 0.2s figure, reserving one celebration, the
> 0.96 press scale — are that developer's taste, presented without
> measurement. Good defaults, not established thresholds.

Both skills link back to the source URL and creator.

## Cost

Nothing. One download, one local transcription, fourteen JPEG frames.
