import logging
from database import Memory
from telebot import types


# Enabling logging
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger()


def save_chat(message: types.Message):
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
    del db


def save_action(message: types.Message):
    db = Memory()
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