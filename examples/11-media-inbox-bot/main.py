"""
Media Inbox Bot
=================
Feature focus: `pywa.types` media objects — downloading inbound images/video/audio/documents to
disk, and sending outbound media straight from a remote URL.
"""

import os
import pathlib

import dotenv

from pywa_async import WhatsApp, filters, types
from pywa_async.utils import start_ngrok_tunnel

dotenv.load_dotenv()

callback_url = os.getenv("CALLBACK_URL")
if not callback_url:
    callback_url = start_ngrok_tunnel(auth_token=os.environ["NGROK_AUTH_TOKEN"])

wa = WhatsApp(
    phone_id=os.environ["WHATSAPP_PHONE_ID"],
    token=os.environ["WHATSAPP_TOKEN"],
    app_id=os.environ["WHATSAPP_APP_ID"],
    app_secret=os.environ["WHATSAPP_APP_SECRET"],
    callback_url=callback_url,
    verify_token=os.environ.get("WHATSAPP_VERIFY_TOKEN", "xyzxyz"),
)

DOWNLOADS_DIR = pathlib.Path(__file__).parent / "downloads"
DOWNLOADS_DIR.mkdir(exist_ok=True)

CAT_IMAGE_URL = "https://cataas.com/cat"


async def _save(media: types.media.ArrivedMedia, fallback_ext: str) -> pathlib.Path:
    """Download an inbound media object to DOWNLOADS_DIR/<media_id><ext>."""
    ext = media.extension or f".{fallback_ext}"
    return await media.download(path=DOWNLOADS_DIR, filename=f"{media.id}{ext}")


@wa.on_message(filters.image)
async def on_image(_: WhatsApp, msg: types.Message):
    path = await _save(msg.image, "jpg")
    await msg.reply(f"🖼️ Saved your image as {path.name} ({path.stat().st_size} bytes).")


@wa.on_message(filters.video)
async def on_video(_: WhatsApp, msg: types.Message):
    path = await _save(msg.video, "mp4")
    await msg.reply(f"🎬 Saved your video as {path.name}.")


@wa.on_message(filters.document)
async def on_document(_: WhatsApp, msg: types.Message):
    path = await _save(msg.document, "bin")
    await msg.reply(f"📄 Saved your document as {path.name}.")


@wa.on_message(filters.audio | filters.voice)
async def on_audio(_: WhatsApp, msg: types.Message):
    path = await _save(msg.audio, "ogg")
    await msg.reply(f"🎧 Saved your audio as {path.name}.")


@wa.on_message(filters.sticker)
async def on_sticker(_: WhatsApp, msg: types.Message):
    await msg.react("👀")


@wa.on_message(filters.command("cat", ignore_case=True))
async def send_cat(_: WhatsApp, msg: types.Message):
    await msg.reply_image(image=CAT_IMAGE_URL, caption="🐈")


@wa.on_message(filters.text)
async def hint(_: WhatsApp, msg: types.Message):
    await msg.reply(
        "Send me an image, video, document, audio note or sticker and I'll save it.\n"
        "Or send /cat for a surprise."
    )


# Run with: pywa dev
