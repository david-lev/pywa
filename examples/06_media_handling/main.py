"""
06 — Media: receive, download, send

What it does:
- Receives images, audio, documents, video. Downloads each to ./downloads/
  with a sensible filename, and replies with the saved path.
- On "send me a cat" → uploads a remote URL and replies with the image.
- Stickers → re-sends as a reaction so the user sees PyWa supports them.

Run:
    cp ../.env.example .env
    fastapi dev main.py
"""

from __future__ import annotations

import logging
import os
import pathlib

from dotenv import load_dotenv
from fastapi import FastAPI

from pywa import WhatsApp, filters, types

load_dotenv()
logging.basicConfig(level=logging.INFO)

DOWNLOADS = pathlib.Path(__file__).parent / "downloads"
DOWNLOADS.mkdir(exist_ok=True)

CAT_URL = "https://cataas.com/cat"

fastapi_app = FastAPI()

wa = WhatsApp(
    phone_id=os.environ["WA_PHONE_ID"],
    token=os.environ["WA_TOKEN"],
    server=fastapi_app,
    callback_url=os.environ["WA_CALLBACK_URL"],
    verify_token=os.environ["WA_VERIFY_TOKEN"],
    app_id=int(os.environ["WA_APP_ID"]),
    app_secret=os.environ["WA_APP_SECRET"],
)


def _download_arrived(media: types.media.ArrivedMedia, fallback_ext: str) -> pathlib.Path:
    """Download to ./downloads/<media_id><ext> and return the saved path."""
    ext = media.extension or f".{fallback_ext}"  # `extension` already includes the dot
    return media.download(path=DOWNLOADS, filename=f"{media.id}{ext}")


@wa.on_message(filters.image)
def on_image(_: WhatsApp, msg: types.Message) -> None:
    path = _download_arrived(msg.image, "jpg")
    msg.reply_text(f"Got your image — saved to {path.name} ({path.stat().st_size} bytes).")


@wa.on_message(filters.document)
def on_doc(_: WhatsApp, msg: types.Message) -> None:
    path = _download_arrived(msg.document, "bin")
    msg.reply_text(f"📄 Document saved as {path.name}.")


@wa.on_message(filters.audio | filters.voice)
def on_audio(_: WhatsApp, msg: types.Message) -> None:
    path = _download_arrived(msg.audio, "ogg")
    msg.reply_text(f"🎧 Audio saved as {path.name}.")


@wa.on_message(filters.video)
def on_video(_: WhatsApp, msg: types.Message) -> None:
    path = _download_arrived(msg.video, "mp4")
    msg.reply_text(f"🎬 Video saved as {path.name}.")


@wa.on_message(filters.sticker)
def on_sticker(_: WhatsApp, msg: types.Message) -> None:
    msg.react("👀")


@wa.on_message(filters.matches("cat", ignore_case=True))
def send_cat(_: WhatsApp, msg: types.Message) -> None:
    # PyWa accepts a remote URL directly — it streams it to WhatsApp's media endpoint.
    msg.reply_image(image=CAT_URL, caption="🐈")


@wa.on_message(filters.text)
def hint(_: WhatsApp, msg: types.Message) -> None:
    msg.reply_text(
        "Send me an image, video, document, audio or sticker — I'll save it.\n"
        'Or type "cat" for a surprise.'
    )
