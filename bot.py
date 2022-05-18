import os
import telebot
from telebot import types
from convert import Converter

MODE = os.getenv('MODE')
TOKEN = os.getenv('TOKEN')

bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=['start'])
def start(message: types.Message):
    welcome_mess = 'Привет! Отправляй голосовое, я расшифрую!'
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

    bot.send_message(message.chat.id, message_text, reply_to_message_id=message.message_id)


if __name__ == '__main__':
    if MODE == 'dev':
        bot.polling(none_stop=True, timeout=123)
    else:
        HEROKU_APP_NAME = os.getenv('HEROKU_APP_NAME')
        url=f'https://{HEROKU_APP_NAME}.herokuapp.com/{TOKEN}'
        bot.set_webhook(url=url)