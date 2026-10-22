---
description: Watch a social media video (TikTok, Reel, YouTube, X) and turn what it teaches into a skill
argument-hint: <video URL> [what to do with it]
---

Use the `watch` skill to process this video: $ARGUMENTS

If no URL was supplied, ask for one and stop.

Work through the skill's pipeline:

1. Run `scripts/ingest.py` with an output directory under `/tmp/`.
   Pick the frame count from the content: ~12 for a talking head, ~30 for a
   screen recording or anything fast-cut.
2. Read `MANIFEST.md`, then `transcript.txt`, then `caption.txt` (never
   skip the caption - creators finish their lists there), then every frame
   in `frames/` in filename order using the Read tool.
3. Classify the video before converting anything — procedure, single tactic,
   opinion, demo, or entertainment. Say which it is.
4. Convert to a skill only if it is a repeatable procedure. Use the
   `skill-creator` skill, and record the source URL and creator in it.
   Anything smaller: summarise, and offer to save it as a memory instead.
5. Report, always: what it teaches, the exact skill name and path, how to
   invoke it (trigger phrases plus an example sentence), and the full list
   of points it covers.

If the user named something specific they want from the video, that goal
wins over the default behaviour.
