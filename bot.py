import os
import logging
import telebot
from telebot import types, apihelper
from convert import Converter
from flask import Flask, request
from utils import save_chat, save_action, transform_settings, get_settings, update_settings, create_markup,\
    download_file, get_chat_name, get_chats, set_chat_inactive,\
    TEXT_ABOUT

MODE = os.getenv('MODE')
TOKEN = os.getenv('TOKEN')

bot = telebot.TeleBot(TOKEN)
converter = Converter()

# Enabling logging
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger()


@bot.message_handler(commands=['start'])
def start(message: types.Message):
    chat_name = get_chat_name(message)
    logger.info(f"Chat {chat_name} (ID: {message.chat.id}) started bot")
    welcome_mess = 'Привет! Отправляй голосовое, я расшифрую!'
    save_chat(message)
    bot.send_message(message.chat.id, welcome_mess)
    save_action(message, 'start')


@bot.message_handler(content_types=['voice', 'video_note'])
def get_audio_messages(message: types.Message):
    save_chat(message)  # костыль если не нажали start, надо подумать как изменить логику

    allow_type = {
        'all': ['voice', 'video_note'],
        'audio': ['voice'],
        'video': ['video_note']
    }

    chat_name = get_chat_name(message)
    settings = transform_settings(get_settings(message.chat.id))

    if settings and message.content_type in allow_type[settings]:
        logger.info(f"Chat {chat_name} (ID: {message.chat.id}) start converting")

        file_name = download_file(bot, message)
        logger.info(f"Chat {chat_name} (ID: {message.chat.id}) download file {file_name}")

        message_text = converter.audio_to_text(file_name)
        if message_text:
            bot.send_message(message.chat.id, message_text, reply_to_message_id=message.message_id)
        else:
            logger.error('Произошла ошибка при конвертации')
            save_action(message, 'failed_conversion')
        logger.info(f"Chat {chat_name} (ID: {message.chat.id}) end converting")

        os.remove(file_name)
        logger.info(f"Chat {chat_name} (ID: {message.chat.id}) File {file_name} deleted")
        save_action(message, 'successful_conversion')
    else:
        logger.info(f"Chat {chat_name} (ID: {message.chat.id}) converting disable for type {message.content_type}")
        save_action(message, 'conversion_disabled')


@bot.message_handler(commands=['settings'])
def settings(message: types.Message):
    chat_name = get_chat_name(message)
    logger.info(f"Chat {chat_name} (ID: {message.chat.id}) send settings")
    message_text = 'Укажите, что мне трансформировать в текст'

    bot.send_message(message.chat.id, message_text,
                     reply_markup=create_markup(transform_settings(get_settings(message.chat.id))))
    save_action(message, 'show_settings')


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call: types.CallbackQuery):
    logger.info(f"Chat (ID: {call.message.chat.id}) edit settings: {call.data}")
    markup = create_markup(transform_settings(update_settings(call.message.chat.id, call.data)))
    bot.answer_callback_query(call.id, "Меняю настройки!")
    bot.edit_message_reply_markup(call.message.chat.id, call.message.id, call.inline_message_id,
                                  reply_markup=markup)
    save_action(call.message, 'edit_settings')


@bot.message_handler(commands=['broadcast'])
def settings(message: types.Message):
    chat_name = get_chat_name(message)
    admins = os.getenv("ADMIN_IDS").split(',')
    message_text = message.text.split(maxsplit=1)
    if message_text and len(message_text) > 1:
        if str(message.from_user.id) in admins:
            logger.info(f"Chat {chat_name} (ID: {message.chat.id}) start broadcast")
            for chat_id in get_chats():
                logger.info(f"Chat {chat_name} (ID: {chat_id}) send broadcast message")
                try:
                    bot.send_message(chat_id, message_text[1])
                except apihelper.ApiTelegramException:
                    set_chat_inactive(chat_id)
                    logger.info(f"Chat {chat_name} (ID: {chat_id}) message don't send")
        else:
            logger.info(f"Chat {chat_name} (ID: {message.chat.id}) failed broadcast. {message.from_user.id} isn't admin")
    else:
        logger.info(f"Chat {chat_name} (ID: {message.chat.id}) failed broadcast. {message_text} invalid")
    save_action(message, 'broadcast')


@bot.message_handler(commands=['about'])
def settings(message: types.Message):
    chat_name = get_chat_name(message)
    logger.info(f"Chat {chat_name} (ID: {message.chat.id}) get about")
    message_text = TEXT_ABOUT
    bot.send_message(message.chat.id, message_text)

    save_action(message, 'about')


if __name__ == '__main__':
    logger.info("Starting bot")
    if MODE == 'dev':
        bot.remove_webhook()
        bot.polling(none_stop=True, timeout=123)
    else:
        server = Flask(__name__)


        @server.post('/' + TOKEN)
        def get_message():
            json_string = request.get_data().decode('utf-8')
            update = telebot.types.Update.de_json(json_string)
            bot.process_new_updates([update])
            return "!", 200

        @server.route("/")
        def webhook():
            bot.remove_webhook()
            url = f'{os.getenv("APP_URL")}/{TOKEN}'
            bot.set_webhook(url=url)
            return "!", 200


        server.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
