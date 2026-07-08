import os
import logging
from gtts import gTTS
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")

# Supported languages (extend as needed)
LANGUAGES = {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "ar": "Arabic",
    "hi": "Hindi",
    "pt": "Portuguese",
}

# Simple per-user language preference (in-memory; resets on restart)
user_lang = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hi! Send me any text and I'll convert it to an audio voice message.\n\n"
        "Commands:\n"
        "/lang <code> - set language (en, es, fr, de, ar, hi, pt)\n"
        "/languages - list supported languages\n\n"
        "Default language: English (en)"
    )


async def list_languages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "🌍 Supported languages:\n" + "\n".join(
        f"`{code}` - {name}" for code, name in LANGUAGES.items()
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /lang <code>  (e.g. /lang es)")
        return

    code = context.args[0].lower()
    if code not in LANGUAGES:
        await update.message.reply_text(
            f"❌ Unsupported language code '{code}'. Use /languages to see options."
        )
        return

    user_lang[update.effective_user.id] = code
    await update.message.reply_text(f"✅ Language set to {LANGUAGES[code]} ({code}).")


async def text_to_speech(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id
    lang = user_lang.get(user_id, "en")

    if not text or len(text.strip()) == 0:
        await update.message.reply_text("Please send some text first.")
        return

    if len(text) > 1000:
        await update.message.reply_text(
            "⚠️ Text is too long (max 1000 characters). Please shorten it."
        )
        return

    processing_msg = await update.message.reply_text("🎙️ Generating audio...")

    try:
        tts = gTTS(text=text, lang=lang)
        file_path = f"/tmp/{user_id}_voice.mp3"
        tts.save(file_path)

        with open(file_path, "rb") as audio_file:
            await update.message.reply_voice(voice=audio_file)

        os.remove(file_path)
        await processing_msg.delete()

    except Exception as e:
        logger.error(f"Error generating audio: {e}")
        await processing_msg.edit_text(
            "❌ Sorry, something went wrong generating the audio."
        )


def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN environment variable is not set!")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("languages", list_languages))
    app.add_handler(CommandHandler("lang", set_language))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_to_speech))

    logger.info("Bot started polling...")
    app.run_polling()


if __name__ == "__main__":
    main()
