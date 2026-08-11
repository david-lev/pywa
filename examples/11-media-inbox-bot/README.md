# 📥 Media Inbox Bot

> 🤖 **AI-generated example.** This bot and its README were written by an AI coding assistant
> for pywa's example gallery. It's meant as a learning reference, not vetted
> production code — please read through it before running it.

**Feature focus:** [`pywa.types`](https://pywa.readthedocs.io/en/latest/content/types/media.html) media objects —
downloading inbound images/video/audio/documents to disk, and sending outbound media straight from
a remote URL.

## What it demonstrates

- `filters.image` / `filters.video` / `filters.document` / `filters.audio | filters.voice` /
  `filters.sticker` to route by media type
- `media.download(path=..., filename=...)` to save an inbound file to disk
- `media.extension` to pick a sensible file extension from the MIME type
- Sending outbound media directly from a URL (`msg.reply_image(image=<url>)`) — pywa streams it to
  WhatsApp for you, no local download/re-upload needed

## Prerequisites

- Python 3.10+
- A Meta App with the WhatsApp product added

## Setup

```bash
cd examples/11-media-inbox-bot
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edit .env with your credentials
```

## Run

```bash
pywa dev
```

## Try it

Send the bot a photo, a video, a document, a voice note, or a sticker — it saves each one under
`./downloads/` and confirms the filename. Send `/cat` for a bonus reply with a remote image.

## Notes

For large files, prefer streaming (`media.stream()`) over `download()`/`get_media_bytes()` so you
don't have to hold the whole file in memory. Downloaded files are named `<media_id><ext>` for
deterministic, collision-free filenames — swap `DOWNLOADS_DIR` for real object storage (S3, GCS,
etc.) in production.

## Async / sync

This example is written with `pywa_async`. Run `pywa new examples 11-media-inbox-bot --async` to
fetch it as-is, or omit `--async` to get an automatically generated synchronous (`pywa`) version
instead.
