import os
import asyncio

from telegram import Bot, LinkPreviewOptions


def format_release_message(tag_name: str, name: str, body: str) -> str:
    """
    Formats a GitHub release message for Telegram with custom styling.

    :param tag_name: The release tag.
    :param name: The release name.
    :param body: The release description.
    :return: A neatly formatted message string ready to be sent on Telegram.
    """
    formatted_parts = []
    in_code_block = False
    current_code_block = []
    pip_command = None

    lines = body.split("\n")

    for line in lines:
        if line.startswith("```"):
            if in_code_block:
                in_code_block = False
                current_code_block.append(line)
                formatted_parts.append("\n".join(current_code_block))
                current_code_block = []
            else:
                in_code_block = True
                current_code_block.append(line)
        elif in_code_block:
            current_code_block.append(line)
        elif line.startswith("> Update with pip:"):
            pip_command = line.split("`")[1]
        elif line.startswith("-"):
            line = line.replace("[", "\\[").replace("]", "\\]")
            formatted_parts.append(f"• {line[1:]}")

    if pip_command:
        formatted_parts.append(f"\n>> Update with:\n```bash\n{pip_command}\n```")

    message_body = "\n".join(formatted_parts)

    # Remove redundant escape characters
    message_body = message_body.replace("\\[", "[").replace("\\]", "]")

    formatted_message = (
        f"🎉 **NEW VERSION • {name}**\n\n"
        f"📝 [Changelog](https://github.com/david-lev/pywa/releases/tag/{tag_name})\n\n"
        f"{message_body}\n"
    )

    return formatted_message


async def send_to_telegram():
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    release_name = os.getenv("RELEASE_NAME")
    release_tag = os.getenv("RELEASE_TAG")
    release_body = os.getenv("RELEASE_BODY")

    message = format_release_message(release_tag, release_name, release_body)
    print(message)

    bot = Bot(token=bot_token)
    await bot.send_message(
        chat_id=chat_id,
        text=message,
        parse_mode="Markdown",
        link_preview_options=LinkPreviewOptions(
            url="https://pywa.readthedocs.io/",
            prefer_large_media=False,
            show_above_text=True,
        ),
    )


if __name__ == "__main__":
    asyncio.run(send_to_telegram())
