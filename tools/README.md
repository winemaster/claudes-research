# Tools

## `yt.py`: YouTube transcripts and metadata

Tested 2026-10-04 from the cloud environment (full network access).

```sh
python3 -m pip install -U yt-dlp          # once per session
python3 tools/yt.py 65yjqIDghEk /mnt/project-files/youtube/
python3 tools/yt.py --list "https://www.youtube.com/@QualiaResearchInstitute/videos"
python3 tools/yt.py --list "https://www.youtube.com/playlist?list=PLZ7ikzmc6zlN7M6CrEnBPZ2qywnGYdUDk"
```

The output file `<video id>.md` has the title, channel, upload date, duration, description, chapters and the transcript as paragraphs of about a minute each, stamped `[h:mm:ss]`. A two-hour video comes to roughly 18k words, so read it in pieces (`sed -n`, `grep`) rather than all at once.

### What works and what doesn't

| Route | Result from the cloud |
|---|---|
| Watch page `youtube.com/watch?v=…` | ❌ 302 to a Google "sorry" captcha, then 429 |
| `youtube-transcript-api` | ❌ `IpBlocked` (cloud-provider IP) |
| `yt-dlp` default clients, `android_vr`, `ios`, `tv_simply` | ❌ "Sign in to confirm you're not a bot" |
| **`yt-dlp` with `player_client=web_embedded`** | ✅ metadata and caption tracks (human-made and auto-generated) |
| Playlist and channel pages (`--list`, or plain `curl`) | ✅ |
| oEmbed `youtube.com/oembed?url=…` | ✅ title and channel only |
| Channel/playlist RSS `youtube.com/feeds/videos.xml?…` | ✅ latest 15 videos |
| YouTube Data API `googleapis.com/youtube/v3` | needs an API key (none set) |

The caption server occasionally answers 429 when several videos are fetched back to back; the script waits and retries. Space out bulk fetches.

### If it stops working

YouTube changes this cat-and-mouse often. In rough order:
1. `python3 -m pip install -U yt-dlp` (new releases track YouTube's changes) and retry.
2. Look for the transcript elsewhere: podcast transcript sites (e.g. podscripts.co for *Theories of Everything*), the show's own site, Substack.
3. Things only Josiah can provide, none of them required today:
   - upload transcripts he copies from YouTube's "Show transcript" panel into the project files;
   - a YouTube cookies file (exported from a logged-in browser) for `yt-dlp --cookies`; best from a throwaway account, since Google can flag accounts used this way;
   - run `yt.py` on his own computer, whose home IP isn't blocked, via a Remote Control session.
