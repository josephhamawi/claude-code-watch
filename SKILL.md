---
name: watch
description: Watch a social media video and turn what it teaches into a reusable skill. Use when the user pastes a TikTok, Instagram Reel, YouTube, YouTube Short, X/Twitter, LinkedIn or Facebook video URL and wants it understood, summarised, or converted into a skill — triggers include "/watch", "watch this video", "what does this video say", "turn this video into a skill", "extract the tactic from this", "summarise this reel", "make a skill from this". Also use for a local video file the user wants analysed.
---

# watch

Turn a social video into something reusable. The pipeline is: download →
transcribe → sample frames → read → decide what it is → optionally write a
skill.

## The constraint that shapes everything

**You cannot watch video.** You read a transcript and a set of still frames.
That is enough for advice, tutorials, walkthroughs and demos — the content
worth converting. It is weak on fast motion and dense screen recordings.

When frames are not enough to answer a question, say so and offer to re-run
with more (`--frames 30`) rather than guessing what happened between stills.

## Step 1 — ingest

```bash
python3 ~/.claude/skills/watch/scripts/ingest.py "<URL>" --out /tmp/watch-<slug>
```

Useful flags:

| Flag | When |
|---|---|
| `--frames 30` | dense screen recordings, UI walkthroughs, anything fast |
| `--frames 6` | a talking head where the visuals barely change |
| `--model base.en` | faster, lower quality transcription |
| `--model medium.en` | accented speech, jargon, poor audio |
| `--local` | the argument is a file on disk, not a URL |

Transcription is the slow step: roughly real-time on CPU with `small.en`.
Tell the user a 3-minute video takes a few minutes, then let it run. Sites
that ship creator captions skip whisper entirely and finish in seconds.

If ingest fails, read the error before retrying:

- **403 / "sign in to confirm"** → the site wants cookies. Use the `yt-dlp`
  skill; `--cookies-from-browser chrome` usually fixes it.
- **"requested format is not available"** → yt-dlp is stale. `pipx upgrade
  yt-dlp` or `yt-dlp -U`.
- **No transcriber** → `pip install faster-whisper`.

## Step 2 — read the pack

Read in this order:

1. `MANIFEST.md` — what was produced
2. `transcript.txt` — what was said
3. `caption.txt` — what was written. **Never skip this.**
4. `frames/*.jpg` — **read them with the Read tool, in filename order**

Three sources, because each carries something the others do not:

- **Speech** gives the narrative and the reasoning.
- **The caption** routinely holds the rest of a list. "Those are my top four,
  check the caption for the rest" is a standard move — the video is the hook,
  the caption is the payload. It also carries links, tool names, exact
  settings and credits that are never said out loud.
- **Frames** carry on-screen text, UI state, before/after comparisons and
  numbers in overlays. Creators show the specifics and say something vague.

If `caption.txt` is absent the post had none; `meta.json` holds the raw
metadata either way. `transcript.srt` has timestamps when you need to align
a frame to speech.

## Step 3 — classify before converting

Not every video should become a skill. Decide which this is:

| Kind | What to do |
|---|---|
| **Repeatable procedure** — a workflow, a method, a checklist | Convert to a skill |
| **A single tactic or insight** | Too small for a skill. Summarise it; offer to save it as a memory |
| **Opinion, commentary, news** | Summarise. Do not make a skill |
| **Product demo / ad** | Summarise what it claims. Do not make a skill |
| **Entertainment** | Just say what is in it |

Say which it is and why before building anything. A skill made from a video
that was really just an opinion is worse than no skill — it will fire on
future tasks and inject noise.

## Step 4 — convert, when it earns it

Invoke the `skill-creator` skill to write it. Feed it:

- the transcript and your reading of the frames,
- the procedure you extracted, as concrete steps,
- the triggers a user would actually type to want this.

Rules that matter for video-derived skills:

- **Extract the method, not the script.** The creator's phrasing, hook and
  personality are not the skill. The repeatable procedure is.
- **Keep the creator's specifics when they are the value** — exact numbers,
  thresholds, tool names, orderings. Strip the filler.
- **Record the source** in the skill body: URL, creator, date. A claim from
  one creator's video is not an established practice, and the next reader
  deserves to know where it came from.
- **Mark unverified claims as unverified.** Growth and marketing videos are
  full of numbers with no evidence. Do not launder them into instructions.

## Step 5 — report

Always end with these four, in this order. A skill the user cannot name,
invoke, or recall the contents of may as well not exist.

1. **What the video teaches** — a few lines.
2. **The skill name**, exactly as written, and where it lives on disk.
3. **How to use it** — the trigger phrases that fire it, and the explicit
   invocation. Skills fire automatically on matching requests; say so, and
   give a realistic example sentence the user would actually type.
4. **Every point it covers** — list them. Not a summary: the actual items,
   so the user can see what they now have without opening the file.

Then note anything the frames or transcript could not resolve.

When nothing was converted, say which category it fell into and why, and
offer the alternative (a summary, or saving it as a memory).

## Cost note

Everything here runs locally: yt-dlp, ffmpeg, whisper. No API, no account, no
billing. Reading many frames does consume context — 12 is a reasonable
default, 30+ only when the content demands it.
