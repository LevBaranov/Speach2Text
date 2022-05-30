import os
import logging
import sys
import telebot
from telebot import types
from convert import Converter
from flask import Flask, request
from database import Memory

MODE = os.getenv('MODE')
TOKEN = os.getenv('TOKEN')

bot = telebot.TeleBot(TOKEN)

# Enabling logging
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger()


def save(message: types.Message):
    db = Memory()
    db.added_chat(telegram_id=message.from_user.id,
                  t_username=message.from_user.username,
                  t_first_name=message.from_user.first_name,
                  t_last_name=message.from_user.last_name,
                  language_code=message.from_user.language_code,
                  chat_id=message.chat.id,
                  chat_type=message.chat.type,
                  title=message.chat.title,
                  c_username=message.chat.username,
                  c_first_name=message.chat.first_name,
                  c_last_name=message.chat.last_name,
                  bio=message.chat.bio,
                  description=message.chat.description
                  )
    db.added_action(telegram_id=message.from_user.id,
                    chat_id=message.chat.id
                    )
    del db


def transform_settings(setting_from_db: dict | None) -> str | None:
    if setting_from_db:
        if setting_from_db["video"] and setting_from_db["audio"]:
            return "all"
        elif setting_from_db["video"]:
            return "video"
        elif setting_from_db["audio"]:
            return "audio"
    return None


def get_settings(chat_id: int) -> dict | None:
    db = Memory()
    chat_settings = db.get_settings(chat_id)
    del db
    logger.info(f'Settings for ID {chat_id}: {chat_settings.__repr__()}')
    return chat_settings


def update_settings(chat_id: int, key: str) -> str | None:
    cur_settings = get_settings(chat_id)
    res = None
    if cur_settings:
        db = Memory()
        res = db.update_settings(chat_id, key, (not cur_settings[key]))
        logger.info(f'Update settings for ID {chat_id}: {res.__repr__()}')
        del db
    return res


def create_markup(type: str = None) -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup()
    markup.row_width = 2
    check_a = ' ✔' if type and type in ['audio', 'all'] else ''
    check_v = ' ✔' if type and type in ['video', 'all'] else ''
    markup.add(types.InlineKeyboardButton(f"Audio{check_a}", callback_data="audio"),
               types.InlineKeyboardButton(f"Video{check_v}", callback_data="video"))
    return markup


@bot.message_handler(commands=['start'])
def start(message: types.Message):
    name = message.chat.first_name if message.chat.first_name else 'No_name'
    logger.info(f"Chat {name} (ID: {message.chat.id}) started bot")
    welcome_mess = 'Привет! Отправляй голосовое, я расшифрую!'
    save(message)
    bot.send_message(message.chat.id, welcome_mess)


@bot.message_handler(content_types=['voice', 'video_note'])
def get_audio_messages(message: types.Message):
    name = message.chat.first_name if message.chat.first_name else 'No_name'
    logger.info(f"Chat {name} (ID: {message.chat.id}) start converting")
    file_id = message.voice.file_id if message.voice else message.video_note.file_id
    file_info = bot.get_file(file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    file_name = str(message.message_id) + '.ogg'
    logger.info(f"Chat {name} (ID: {message.chat.id}) download file {file_name}")

    with open(file_name, 'wb') as new_file:
        new_file.write(downloaded_file)
    converter = Converter(file_name)
    os.remove(file_name)
    message_text = converter.audio_to_text()
    logger.info(f"Chat {name} (ID: {message.chat.id}) end converting")
    del converter

    save(message)
    bot.send_message(message.chat.id, message_text, reply_to_message_id=message.message_id)


@bot.message_handler(commands=['settings'])
def settings(message: types.Message):
    name = message.chat.first_name if message.chat.first_name else 'No_name'
    logger.info(f"Chat {name} (ID: {message.chat.id}) send settings")
    message_text = 'Укажите, что мне трансформировать в текст'

    bot.send_message(message.chat.id, message_text,
                     reply_markup=create_markup(transform_settings(get_settings(message.chat.id))))


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call: types.CallbackQuery):
    logger.info(f"Chat (ID: {call.message.chat.id}) edit settings: {call.data}")
    markup = create_markup(transform_settings(update_settings(call.message.chat.id, call.data)))
    bot.answer_callback_query(call.id, "Меняю настройки!")
    bot.edit_message_reply_markup(call.message.chat.id, call.message.id, call.inline_message_id,
                                  reply_markup=markup)


if __name__ == '__main__':
    logger.info("Starting bot")
    if MODE == 'dev':
        bot.polling(none_stop=True, timeout=123)
    else:
        server = Flask(__name__)


        @server.route('/' + TOKEN, methods=['POST'])
        def get_message():
            json_string = request.get_data().decode('utf-8')
            update = telebot.types.Update.de_json(json_string)
            bot.process_new_updates([update])
            return "!", 200


        @server.route("/")
        def webhook():
            bot.remove_webhook()
            url = f'https://{os.getenv("HEROKU_APP_NAME")}.herokuapp.com/{TOKEN}'
            bot.set_webhook(url=url)
            return "!", 200


        server.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
