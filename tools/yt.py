#!/usr/bin/env python3
"""Fetch a YouTube video's metadata and transcript from a cloud session.

YouTube blocks the normal watch page from cloud IPs (it redirects to a
Google "sorry" captcha, and yt-dlp / youtube-transcript-api report
"Sign in to confirm you're not a bot"). The *embedded player* client is
not blocked, so this asks yt-dlp to pretend to be an embedded player.

Usage:
    python3 -m pip install -U yt-dlp      # once per session
    python3 tools/yt.py VIDEO_URL_OR_ID [OUT_DIR]
    python3 tools/yt.py --list PLAYLIST_OR_CHANNEL_URL

Writes OUT_DIR/<id>.md: title, channel, date, duration, link, description,
chapters, then the transcript as plain paragraphs with [h:mm:ss] marks.
OUT_DIR defaults to the scratch dir /tmp/yt. Transcripts are long; read
the file in pieces rather than printing it whole.
"""
import json
import re
import sys
import time
from pathlib import Path

import yt_dlp

CLIENTS = ["web_embedded", "mweb", "tv_simply"]


def ydl(client=None, **extra):
    opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "ignore_no_formats_error": True,
        "js_runtimes": {"node": {}},
    }
    if client:
        opts["extractor_args"] = {"youtube": {"player_client": [client]}}
    opts.update(extra)
    return yt_dlp.YoutubeDL(opts)


def pick_track(info):
    """English captions: human-made first, then YouTube's auto captions.

    Auto captions list "en-orig" (the speech recognizer's own output) next to
    "en" entries that are machine translations (URLs with tlang=); those
    translated URLs are the ones the caption server rate-limits hardest.
    """
    for key in ("subtitles", "automatic_captions"):
        tracks = info.get(key) or {}
        for lang in ("en-orig", "en", "en-US", "en-GB"):
            for t in tracks.get(lang, []):
                if t.get("ext") == "json3" and "tlang=" not in t["url"]:
                    return key, lang, t["url"]
    return None


def stamp(ms):
    s = int(ms // 1000)
    return f"{s // 3600}:{s % 3600 // 60:02d}:{s % 60:02d}"


def transcript(url, every_ms=60_000):
    """Join caption events into paragraphs, starting a new one about once a minute."""
    for wait in (20, 60, 120, None):  # the caption server rate-limits in bursts
        try:
            with ydl().urlopen(url) as r:
                data = json.load(r)
            break
        except yt_dlp.networking.exceptions.HTTPError as e:
            if e.status != 429 or wait is None:
                raise
            print(f"caption server said 429, retrying in {wait}s", file=sys.stderr)
            time.sleep(wait)
    paras, cur, start = [], [], None
    for ev in data.get("events", []):
        text = "".join(s.get("utf8", "") for s in ev.get("segs") or [])
        text = text.replace("\n", " ").replace("\xa0", " ").strip()
        if not text:
            continue
        t = ev.get("tStartMs", 0)
        if start is None:
            start = t
        cur.append(text)
        # Break at a sentence end; auto captions may lack punctuation, so force one later.
        if (t - start >= every_ms and re.search(r"[.?!]$", text)) or t - start >= 3 * every_ms:
            paras.append(f"[{stamp(start)}] " + re.sub(r"\s+", " ", " ".join(cur)))
            cur, start = [], None
    if cur:
        paras.append(f"[{stamp(start)}] " + re.sub(r"\s+", " ", " ".join(cur)))
    return "\n\n".join(paras)


def fetch(video, out_dir):
    url = video if video.startswith("http") else f"https://www.youtube.com/watch?v={video}"
    last_err = None
    for client in CLIENTS:
        try:
            info = ydl(client).extract_info(url, download=False)
        except yt_dlp.utils.DownloadError as e:
            last_err = e
            continue
        track = pick_track(info)
        if track:
            break
        last_err = f"{client}: no English captions offered"
    else:
        sys.exit(f"Could not get captions: {last_err}")

    kind, lang, sub_url = track
    body = transcript(sub_url)
    chapters = info.get("chapters") or []
    lines = [
        f"# {info.get('title')}",
        "",
        f"- Channel: {info.get('channel') or info.get('uploader')}",
        f"- Uploaded: {info.get('upload_date')}",
        f"- Duration: {info.get('duration_string')}",
        f"- Link: https://www.youtube.com/watch?v={info['id']}",
        f"- Captions: {'human-made' if kind == 'subtitles' else 'auto-generated'} ({lang}), via player client `{client}`",
        "",
        "## Description",
        "",
        (info.get("description") or "").strip(),
        "",
    ]
    if chapters:
        lines += ["## Chapters", ""]
        lines += [f"- [{stamp(c['start_time'] * 1000)}] {c['title']}" for c in chapters]
        lines.append("")
    lines += ["## Transcript", "", body, ""]
    out = Path(out_dir) / f"{info['id']}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines))
    print(f"{out}  ({len(body.split())} words, {kind}, client {client})")


def list_videos(url):
    info = ydl(extract_flat=True).extract_info(url, download=False)
    for e in info.get("entries") or []:
        for v in e.get("entries") or [e]:  # a channel URL nests its tabs
            secs = v.get("duration")
            length = stamp(secs * 1000) if secs else "?"
            print(f"{v.get('id')} | {length} | {v.get('title')}", flush=True)


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        sys.exit(__doc__)
    if args[0] == "--list":
        list_videos(args[1])
    else:
        fetch(args[0], args[1] if len(args) > 1 else "/tmp/yt")
