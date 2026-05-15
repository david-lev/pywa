# 06 — Media: receive, download, send

Demonstrates:

- Downloading inbound images / video / audio / docs to `./downloads/`.
- Sending media **from a remote URL** (PyWa streams it to WhatsApp for you).
- Filter composition (`filters.audio | filters.voice`).

## Run

```bash
cp ../.env.example .env
fastapi dev main.py
```

Then send the bot:
- any image / audio / doc / video → it gets saved and you get back the filename.
- the text `cat` → you get a 🐈.
- a sticker → 👀 reaction.

## Notes

- Files land under `examples/06_media_handling/downloads/`. The name is `<media_id><ext>` so duplicates are deterministic.
- `media.extension` is a property that returns the dot-prefixed extension based on the MIME type. For `Document`, it prefers the original filename's extension.
- For large files, prefer `media.stream()` (chunked) over `media.get_bytes()` (loads into memory).
- WhatsApp media URLs expire — `MediaURL.regenerate_url()` re-fetches a fresh one without re-uploading.
