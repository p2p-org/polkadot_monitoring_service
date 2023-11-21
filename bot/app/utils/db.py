import psycopg
import logging
import time
import traceback
from _thread import interrupt_main
from psycopg import Error
from psycopg.sql import Identifier, Literal, SQL


class DB():

    table_bot             = Identifier('maas_bot_v1')
    table_subscription    = Identifier('maas_subscription')
    col_id                = Identifier('id')
    col_chat_id           = Identifier('chat_id')
    col_subscription_name = Identifier('subscription_name')
    col_key               = Identifier('key_name')
    col_value             = Identifier('key_value')

    def __init__(self, db_name, db_user, db_pass, db_host, db_port):
        self.db_user = db_user
        self.db_pass = db_pass
        self.db_host = db_host
        self.db_port = db_port
        self.db_name = db_name
        self._connection = None
        self._cursor = None
        self.init()

    def connect(self, retry_counter=0, sleep=5, attempts=5):
        if not self._connection:
            try:
                self._connection = psycopg.connect(dbname=self.db_name,
                                                    user=self.db_user,
                                                    password=self.db_pass,
                                                    host=self.db_host,
                                                    port=self.db_port,
                                                    connect_timeout=3)
                return self._connection
            except (psycopg.DatabaseError, psycopg.OperationalError, psycopg.InterfaceError) as error:
                if retry_counter >= attempts:
                    logging.error('Unable connect to DB')
                    traceback.print_exc()
                    interrupt_main()
                else:
                    retry_counter += 1
                    logging.warning('Could not conect to DB retry ' + str(retry_counter))
                    time.sleep(sleep)
                    self.connect(retry_counter, sleep, attempts)
            except (Exception, psycopg.Error) as error:
                logging.error(error)
                traceback.print_exc()
                interrupt_main()

    def cursor(self):
        if not self._connection:
            self.reset()

        self._cursor = self._connection.cursor()

        return self._cursor

    def query(self, query, compact=True):
        result = []

        if self._cursor:
            if self._cursor.closed:
                self.reset()
                logging.error('Unable connect to DB')

            try:
                self._cursor.execute(query)
            except (psycopg.errors.UniqueViolation, psycopg.errors.UndefinedColumn, psycopg.errors.InFailedSqlTransaction) as e:
                logging.error(e)
                self._connection.rollback()
            except psycopg.OperationalError:
                self.reset()

            if self._cursor.description:
                colnames = [desc[0] for desc in self._cursor.description]
                rows = self._cursor.fetchall()

                if len(list(rows)) == 1 and compact:
                    return rows[0][0]

                for row in rows:
                    idx = 0
                    row_data = {}
                    for col in colnames:
                        row_data[col] = row[idx]
                        idx += 1
                    result.append(row_data)
        else:
            self.reset()
            logging.error('Unable connect to DB')

        return result

    def commit(self):
        try:
            self._connection.commit()
        except (Exception, Error) as e:
            logging.error(e)
            self._connection.rollback()

    def init(self):
        if self.connect():
            self.cursor()

    def reset(self):
        self.close()
        if self.connect(0, 1, 2):
            self.cursor()

    def close(self):
        if self._connection:
            if self._cursor:
                self._cursor.close()
            self._connection.close()
        self._connection = None
        self._cursor = None

    def get_records(self, field, key, value):
        try:
            result = self.query(SQL('SELECT {} FROM {} WHERE {} = {}').format(
                Identifier(field),
                DB.table_bot,
                Identifier(key),
                Literal(value)))
        except (IndexError, KeyError):
            result = None

        return result

    def add_account(self, chat_id, username):
        self.query(SQL('INSERT INTO {} VALUES ({})').format(
            DB.table_bot,
            SQL(', ').join([Literal(chat_id), Literal(username)])))

        self.commit()

    def update_record(self, chat_id, field, value):
        self.query(SQL('UPDATE {} set {} = {} WHERE {} = {}').format(
            DB.table_bot,
            Identifier(field),
            Literal(value),
            DB.col_id,
            Literal(chat_id)))
        self.commit()

    def delete_account(self, chat_id):
        self.query(SQL('DELETE FROM {} WHERE {} = {}').format(
            DB.table_bot,
            DB.col_id,
            Literal(chat_id)))
        self.commit()

    def get_subscriptions(self, chat_id):
        try:
            result = self.query(SQL('SELECT {subscription_name}, {label}, {match} FROM {table} WHERE {chat_id} = {val1}').format(
                subscription_name=DB.col_subscription_name,
                label=DB.col_key,
                match=DB.col_value,
                table=DB.table_subscription,
                chat_id=DB.col_chat_id,
                val1=Literal(chat_id)), compact=False)
        except Exception as e:
            result = None
        return result

    def add_or_update_subscription(self, chat_id, subscription_name, matchers):
        if not isinstance(matchers, dict):
            return 0
    
        columns = [DB.col_chat_id, DB.col_subscription_name, DB.col_key, DB.col_value]
        values = []
        
        for key, vals in matchers.items():
            for val in vals:
                try:
                    values.append(SQL('({chat_id}, {subscription_name}, {key}, {value})').format(
                        chat_id=Literal(chat_id),
                        subscription_name=Literal(subscription_name),
                        key=Literal(key),
                        value=Literal(val)))
                except IndexError:
                    return 0

        try:
            self.query(SQL('DELETE FROM {table} WHERE {chat_id} = {val1} AND {subscription_name} = {val2}').format(
                table=DB.table_subscription,
                chat_id=DB.col_chat_id,
                val1=Literal(chat_id),
                subscription_name=DB.col_subscription_name,
                val2=Literal(subscription_name)))
            self.query(SQL('INSERT INTO {table} ({columns}) VALUES {values}').format(
                table=DB.table_subscription,
                columns=SQL(',').join(columns),
                values=SQL(',').join(values)))
            self._connection.commit()
            return len(values)
        except Exception as e:
            logging.error("unable to add/update subscription: {}".format(str(e)))
            self._connection.rollback()
            return 0

    def delete_subscription(self, chat_id, subscription_name):
        self.query(SQL('DELETE FROM {table} WHERE {chat_id} = {val1} AND {subscription_name} = {val2}').format(
            table=DB.table_subscription,
            chat_id=DB.col_chat_id,
            val1=Literal(chat_id),
            subscription_name=DB.col_subscription_name,
            val2=Literal(subscription_name)
        ))
        self.commit()
