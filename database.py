import os
import psycopg2
from psycopg2 import sql


class Memory:
    """ Класс для работы с БД """

    def __init__(self):
        self.conn = psycopg2.connect(dbname=os.getenv('POSTGRES_DB'),
                                     user=os.getenv('POSTGRES_USER'),
                                     password=os.getenv('POSTGRES_PASSWORD'),
                                     host=os.getenv('POSTGRES_HOST'))
        self.conn.autocommit = True

    def __del__(self):
        self.conn.close()

    def _insert(self, query, values):
        with self.conn.cursor() as cursor:
            cursor.execute(sql.SQL(query).format(
                sql.SQL(',').join(map(sql.Literal, values))
            ))

    def added_chat(self, **model):
        insert_user = '''
            INSERT INTO public.users (telegram_id, username, first_name, last_name, language_code)
            VALUES {}
            ON CONFLICT (telegram_id) DO NOTHING
        '''
        insert_chat = '''
            INSERT INTO public.chats (chat_id, chat_type, title, username,
                first_name, last_name, bio, description)
            VALUES {}
            ON CONFLICT (chat_id) DO NOTHING
        '''
        self._insert(insert_user, [(model['telegram_id'],
                                    model['t_username'],
                                    model['t_first_name'],
                                    model['t_last_name'],
                                    model['language_code'])])
        self._insert(insert_chat, [(model['chat_id'],
                                    model['chat_type'],
                                    model['title'],
                                    model['c_username'],
                                    model['c_first_name'],
                                    model['c_last_name'],
                                    model['bio'],
                                    model['description'])])

    def added_action(self, **model):
        insert_bot_use = '''
            INSERT INTO public.bot_usage (telegram_id, chat_id)
            VALUES {}
        '''
        self._insert(insert_bot_use, [(model['telegram_id'],
                                       model['chat_id'])])
