import os
import telebot
from telebot import types
from convert import Converter
from flask import Flask, request
from database import Memory

MODE = os.getenv('MODE')
TOKEN = os.getenv('TOKEN')

bot = telebot.TeleBot(TOKEN)


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


@bot.message_handler(commands=['start'])
def start(message: types.Message):
    welcome_mess = 'Привет! Отправляй голосовое, я расшифрую!'
    save(message)
    bot.send_message(message.chat.id, welcome_mess)


@bot.message_handler(content_types=['voice'])
def get_audio_messages(message: types.Message):
    file_info = bot.get_file(message.voice.file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    file_name = str(message.message_id) + '.ogg'

    with open(file_name, 'wb') as new_file:
        new_file.write(downloaded_file)
    converter = Converter(file_name)
    os.remove(file_name)
    message_text = converter.audio_to_text()
    del converter

    save(message)
    bot.send_message(message.chat.id, message_text, reply_to_message_id=message.message_id)


if __name__ == '__main__':
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
