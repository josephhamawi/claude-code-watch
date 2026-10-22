#!/usr/bin/env python3
"""
Download a social media video and reduce it to things Claude can actually
read: a transcript and a handful of still frames.

Claude cannot watch video. This script does the mechanical part so the model
only has to do the understanding part.

    python3 ingest.py <url> [--out DIR] [--frames N] [--model MODEL]
    python3 ingest.py <local.mp4> --local

Writes into the output directory:
    video.mp4           the source (kept for re-runs at different frame rates)
    audio.wav           16k mono, what whisper wants
    transcript.txt      plain text
    transcript.srt      timestamped, so frames can be matched to speech
    frames/f000.jpg ... evenly spaced stills, or scene cuts when detected
    meta.json           title, uploader, duration, description, url
    MANIFEST.md         what was produced, for the agent to read first
"""

import argparse
import json
import os
import shutil
import subprocess
import sys

# Anaconda ships MKL's OpenMP and ctranslate2 (under faster-whisper) brings
# its own. Loading both aborts the process with "OMP: Error #15". This must
# be set before either library is imported, so it stays at the top of the
# file rather than next to the transcriber.
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("OMP_NUM_THREADS", str(max(1, (os.cpu_count() or 4) - 1)))


def run(cmd, **kw):
    """Run a command, raising with the tail of stderr when it fails."""
    p = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if p.returncode != 0:
        tail = (p.stderr or p.stdout or "").strip().splitlines()[-6:]
        raise SystemExit(
            f"FAILED: {' '.join(cmd[:4])}...\n  " + "\n  ".join(tail)
        )
    return p.stdout


def need(binary, hint):
    if not shutil.which(binary):
        raise SystemExit(f"Missing `{binary}`. {hint}")
    return shutil.which(binary)


def download(url, out):
    """Fetch the video, then try for subtitles separately.

    Subtitles are a nice-to-have: creator captions save a whole whisper pass.
    But asking for them in the same call makes a subtitle failure - a 429, a
    missing language - abort the video download too. So they get their own
    attempt, and that attempt is allowed to fail.
    """
    ytdlp = need("yt-dlp", "Install with: pipx install yt-dlp")
    video = os.path.join(out, "video.mp4")

    run([
        ytdlp, url,
        "-f", "bv*[height<=1080]+ba/b[height<=1080]/b",
        "--merge-output-format", "mp4",
        "-o", video,
        "--write-info-json", "--no-playlist",
        "--restrict-filenames", "--no-warnings",
    ])

    # Named languages only. A wildcard like "en.*" pulls every machine
    # translation the site offers and gets the request rate-limited.
    subprocess.run([
        ytdlp, url, "--skip-download",
        "--write-subs", "--write-auto-subs",
        "--sub-format", "vtt", "--sub-langs", "en,en-US,en-GB,en-orig",
        "-o", os.path.join(out, "video"),
        "--no-playlist", "--restrict-filenames", "--no-warnings",
    ], capture_output=True, text=True, timeout=180)

    if not os.path.exists(video):
        # yt-dlp sometimes lands on a different container despite --merge
        for f in sorted(os.listdir(out)):
            if (f.startswith("video.") and
                    not f.endswith((".json", ".vtt", ".srt"))):
                video = os.path.join(out, f)
                break
    return video


def read_meta(out, url):
    meta = {"url": url}
    for f in os.listdir(out):
        if f.endswith(".info.json"):
            with open(os.path.join(out, f)) as fh:
                raw = json.load(fh)
            for k in ("title", "uploader", "channel", "duration",
                      "description", "view_count", "like_count",
                      "upload_date", "webpage_url"):
                if raw.get(k) is not None:
                    meta[k] = raw[k]
            break
    with open(os.path.join(out, "meta.json"), "w") as fh:
        json.dump(meta, fh, indent=2)

    # The caption gets its own file. Creators routinely say "the rest is in
    # the caption" and put the actual list there, so burying it inside
    # meta.json means the most useful text in the post goes unread.
    caption = (meta.get("description") or "").strip()
    if caption:
        with open(os.path.join(out, "caption.txt"), "w") as fh:
            fh.write(caption + "\n")
    return meta


def duration_of(video):
    out = run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", video,
    ])
    try:
        return float(out.strip())
    except ValueError:
        return 0.0


def extract_audio(video, out):
    wav = os.path.join(out, "audio.wav")
    run(["ffmpeg", "-y", "-i", video, "-vn",
         "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", wav])
    return wav


def existing_subs(out):
    """Creator captions, if the site gave us any."""
    for f in sorted(os.listdir(out)):
        if f.endswith(".vtt"):
            return os.path.join(out, f)
    return None


def transcribe(wav, out, model):
    """Whisper via faster-whisper if present, else the whisper CLI."""
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        WhisperModel = None

    if WhisperModel is not None:
        m = WhisperModel(model, device="cpu", compute_type="int8")
        segments, _ = m.transcribe(wav, vad_filter=True)
        segments = list(segments)
        _write_transcripts(out, [(s.start, s.end, s.text.strip())
                                 for s in segments])
        return "faster-whisper:" + model

    if shutil.which("whisper"):
        run(["whisper", wav, "--model", model, "--language", "en",
             "--output_format", "all", "--output_dir", out, "--fp16", "False"])
        return "whisper-cli:" + model

    raise SystemExit(
        "No transcriber. Install one:\n"
        "  pip install faster-whisper      (recommended)\n"
        "  pip install openai-whisper"
    )


def _ts(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}".replace(".", ",")


def _write_transcripts(out, rows):
    with open(os.path.join(out, "transcript.txt"), "w") as fh:
        fh.write("\n".join(r[2] for r in rows if r[2]) + "\n")
    with open(os.path.join(out, "transcript.srt"), "w") as fh:
        for i, (start, end, text) in enumerate(rows, 1):
            if not text:
                continue
            fh.write(f"{i}\n{_ts(start)} --> {_ts(end)}\n{text}\n\n")


def extract_frames(video, out, count, dur):
    """Scene cuts where they exist, otherwise an even spread.

    Social video is cut fast, so scene detection usually gives far better
    coverage than fixed intervals - it lands on the moment each new idea
    appears on screen.
    """
    fdir = os.path.join(out, "frames")
    os.makedirs(fdir, exist_ok=True)

    # Allowed to find nothing. A static talking head has no scene cuts, and
    # ffmpeg errors rather than exiting cleanly when it writes no frames, so
    # this pass must not use run().
    subprocess.run(
        ["ffmpeg", "-y", "-i", video,
         "-vf", "select='gt(scene,0.3)',scale=720:-2",
         "-vsync", "vfr", "-frames:v", str(count * 2),
         os.path.join(fdir, "s%03d.jpg")],
        capture_output=True, text=True,
    )

    got = sorted(f for f in os.listdir(fdir) if f.startswith("s"))
    if len(got) >= max(3, count // 2):
        # thin an over-eager detector down to the requested budget
        keep = {got[round(i * (len(got) - 1) / max(1, count - 1))]
                for i in range(min(count, len(got)))}
        for f in got:
            if f not in keep:
                os.remove(os.path.join(fdir, f))
        return len(keep), "scene-change"

    for f in got:
        os.remove(os.path.join(fdir, f))
    fps = max(count / dur, 0.05) if dur else 0.2
    run(["ffmpeg", "-y", "-i", video,
         "-vf", f"fps={fps:.4f},scale=720:-2",
         "-frames:v", str(count),
         os.path.join(fdir, "f%03d.jpg")])
    return len([f for f in os.listdir(fdir)]), "even-spread"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url", help="video URL, or a local file with --local")
    ap.add_argument("--out", default=None)
    ap.add_argument("--frames", type=int, default=12)
    ap.add_argument("--model", default="small.en")
    ap.add_argument("--local", action="store_true")
    args = ap.parse_args()

    out = args.out or os.path.join(os.getcwd(), "watch-out")
    os.makedirs(out, exist_ok=True)

    need("ffmpeg", "Install with: brew install ffmpeg")

    if args.local:
        video = os.path.join(out, "video.mp4")
        if os.path.abspath(args.url) != os.path.abspath(video):
            shutil.copy(args.url, video)
        meta = {"url": args.url, "title": os.path.basename(args.url)}
        with open(os.path.join(out, "meta.json"), "w") as fh:
            json.dump(meta, fh, indent=2)
    else:
        print("[watch] downloading", flush=True)
        video = download(args.url, out)
        meta = read_meta(out, args.url)

    dur = duration_of(video)
    print(f"[watch] {dur:.0f}s video", flush=True)

    print("[watch] extracting audio", flush=True)
    wav = extract_audio(video, out)

    subs = existing_subs(out)
    if subs:
        print(f"[watch] using creator captions: {os.path.basename(subs)}",
              flush=True)
        engine = "site-captions"
        _vtt_to_txt(subs, out)
    else:
        print(f"[watch] transcribing with {args.model} (slowest step)",
              flush=True)
        engine = transcribe(wav, out, args.model)

    print("[watch] sampling frames", flush=True)
    n, how = extract_frames(video, out, args.frames, dur)

    words = 0
    tpath = os.path.join(out, "transcript.txt")
    if os.path.exists(tpath):
        words = len(open(tpath).read().split())

    cpath = os.path.join(out, "caption.txt")
    cap_words = len(open(cpath).read().split()) if os.path.exists(cpath) else 0
    cap_note = (f"{cap_words} words in `caption.txt` - READ IT" if cap_words
                else "none published with this video")

    with open(os.path.join(out, "MANIFEST.md"), "w") as fh:
        fh.write(f"""# watch pack

- **source**: {meta.get('webpage_url') or meta.get('url')}
- **title**: {meta.get('title', 'unknown')}
- **uploader**: {meta.get('uploader') or meta.get('channel', 'unknown')}
- **duration**: {dur:.0f}s
- **transcript**: {words} words via {engine}
- **caption**: {cap_note}
- **frames**: {n} stills ({how}) in `frames/`

Read `transcript.txt` first, then `caption.txt`, then look at the frames in
order. `transcript.srt` carries timestamps if you need to align a frame to
what was being said.

The caption is not an afterthought: creators routinely cut a list short on
camera and finish it in the post text, so the caption often carries items
the video never says out loud.
""")

    print(f"[watch] done -> {out}")
    print(f"[watch] {words} words, {cap_words} caption words, "
          f"{n} frames ({how})")


def _vtt_to_txt(vtt, out):
    """Flatten a VTT into plain text, dropping cue headers and dupes."""
    lines, seen = [], None
    for raw in open(vtt, encoding="utf-8", errors="ignore"):
        s = raw.strip()
        if (not s or s == "WEBVTT" or "-->" in s or s.isdigit()
                or s.startswith(("NOTE", "Kind:", "Language:"))):
            continue
        s = s.replace("&nbsp;", " ")
        while "<" in s and ">" in s:            # strip inline cue tags
            a, b = s.find("<"), s.find(">")
            if a < b:
                s = s[:a] + s[b + 1:]
            else:
                break
        s = s.strip()
        if s and s != seen:
            lines.append(s)
            seen = s
    with open(os.path.join(out, "transcript.txt"), "w") as fh:
        fh.write("\n".join(lines) + "\n")
    shutil.copy(vtt, os.path.join(out, "transcript.srt"))


if __name__ == "__main__":
    sys.exit(main())
