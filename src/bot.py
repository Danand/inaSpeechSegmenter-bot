from inaSpeechSegmenter_bot.helpers import get_gendered_segments_overall
from inaSpeechSegmenter_client import SegmenterClient

import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import Message, User

import logging
import sys

from posixpath import basename
from os import environ

api_url = environ.get("INA_SPEECH_SEGMENTER_API_URL", "http://127.0.0.1:8888")
bot_token = environ.get("INA_SPEECH_SEGMENTER_BOT_TOKEN", "")
log_level_str = environ.get("INA_SPEECH_SEGMENTER_BOT_LOG_LEVEL", "DEBUG")

log_level = getattr(logging, log_level_str)

logging.basicConfig(
    level=log_level,
    format="%(asctime)s [%(levelname)s] %(name)s (%(filename)s:%(lineno)d) %(funcName)s() - %(message)s",
    stream=sys.stdout,
)

logger = logging.getLogger(__name__)

segmenter_client = SegmenterClient(
    api_url=api_url,
)

def get_voice_file_id(message: Message) -> str | None:
    if message.voice is not None:
        return message.voice.file_id
    if message.audio is not None:
        return message.audio.file_id

    return None

def format_user_info(user: User | None) -> str:
    info = "unknown"

    if user is None:
        return info

    if user.username is not None:
        info = f"`{user.username}`"
    elif user.full_name is not None:
        info = user.full_name

    if user.id is not None:
        info += f" (`{user.id}`)"

    return info

async def get_analysis_report(
    bot: Bot,
    file_id: str,
    user_info: str,
) -> str:
    file = await bot.get_file(file_id)

    file_path = file.file_path

    if file_path is None:
        logger.debug(f"Received message from user {user_info} has no voice data file path!")
        return "Cannot analyze audio: file not found."

    file_name = basename(file_path)

    binary_io = await bot.download_file(file_path)

    if binary_io is None:
        logger.debug(f"Received message from user {user_info} has no readable data!")
        return "Cannot analyze audio: file not found."

    file_bytes = binary_io.read()

    segments_response = segmenter_client.get_segments(
        audio_file_name=file_name,
        audio_bytes=file_bytes,
    )

    report = ""

    gendered_segments = get_gendered_segments_overall(segments_response)

    for gendered_segment in gendered_segments:
        report += f"**{gendered_segment.label.capitalize()}**"
        report += f": {gendered_segment.ratio:.1%}"
        report += "\n"

    report += "\n"

    report += "Full report:\n"
    report += "```json\n"
    report += segments_response.model_dump_json(indent=2)
    report += "\n```"

    return report

dp = Dispatcher()

@dp.message()
async def handle_voice_message(message: Message) -> None:
    user_info = format_user_info(message.from_user)
    bot = message.bot

    if bot is None:
        logger.error(f"Received message from user {user_info} has no bot instance!")
        return

    voice_file_id = get_voice_file_id(message)

    if voice_file_id is None:
        logger.debug(f"Received message from user {user_info} has no voice data!")
        await message.reply("Please send me a voice message.")
    else:
        analysis_report = await get_analysis_report(
            bot=bot,
            file_id=voice_file_id,
            user_info=user_info,
        )

        logger.debug(f"Received message from user {user_info} has voice data analyzed:\n{analysis_report}")

        await message.reply(analysis_report)


async def main() -> None:
    bot = Bot(
        token=bot_token,
        default=DefaultBotProperties(
            parse_mode=ParseMode.MARKDOWN,
        ),
    )

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
