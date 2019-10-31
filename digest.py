#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Анонс дежурств
"""

import config
import warnings
from telegram.ext import Updater
from exchangelib import DELEGATE, Configuration, Credentials, Account
from exchangelib.ewsdatetime import UTC_NOW
from exchangelib.protocol import BaseProtocol, NoVerifyHTTPAdapter
from datetime import timedelta, datetime
from peewee import *
from playhouse.pool import PooledMySQLDatabase
from apscheduler.schedulers.background import BlockingScheduler


# Disable insecure SSL warnings
warnings.filterwarnings("ignore")

# Disable SSL verification for exchangelib
BaseProtocol.HTTP_ADAPTER_CLS = NoVerifyHTTPAdapter


"""
Database
"""
# MySQL Pool
db = PooledMySQLDatabase(
    config.db_name,
    host=config.db_host,
    user=config.db_user,
    passwd=config.db_pass,
    max_connections=8,
    stale_timeout=300)


class BaseModel(Model):
    class Meta:
        database = db


class Chat(BaseModel):
    id = CharField()
    type = CharField()
    username = CharField()
    lastname = CharField()
    started = DateTimeField(default=datetime.now)
    last = DateTimeField(default=datetime.now)
    ym = BooleanField(default=False)
    rl = BooleanField(default=False)
    digest = BooleanField(default=False)

    class Meta:
        indexes = (
            (('id', 'type'), True)
        )


class Option(BaseModel):
    name = CharField(unique=True)
    value = CharField()


def db_get_digest():
    """
    Получить список каналов для оповещения о дежурствах

    :return:
    """
    try:
        db.connect()
        db_chat = Chat.select(Chat.id, Chat.lastname).where(Chat.digest == '1')
        result = []

        for line in db_chat:
            result.append([line.id, line.lastname])
    finally:
        db.close()
    return result


# Создать таблицы
db.connect()
db.create_tables([Chat, Option], safe=True)
db.close()


"""
Exchange
"""


def digest(person, delta, subj):
    now = UTC_NOW()

    cal_start = now + timedelta(minutes=delta)
    delta_end = delta + 1
    cal_end = now + timedelta(minutes=delta_end)

    ex_cred = Credentials(config.ex_user, config.ex_pass)
    ex_cfg = Configuration(server=config.ex_host, credentials=ex_cred)
    ex_acc = Account(primary_smtp_address=config.ex_cal, config=ex_cfg, access_type=DELEGATE, autodiscover=False)

    result = [subj]

    for event in ex_acc.calendar.view(start=cal_start, end=cal_end).only('subject').order_by('subject'):

        body = event.subject[:150]

        if body.find(person) > 1:
            result.append('Дежурство %s!' % body.split('-')[0])

    return result


def digest_all(shift=0, subj='Сегодня:'):

    for chat in db_get_digest():
        duty_list = digest(chat[1], shift, subj)
        if len(duty_list) > 1:
            bot = Updater(token=config.bot_token).bot
            msg = ''
            if len(duty_list) > 2:
                msg += 'Автор жжот\n'

            msg += '\n'.join(duty_list)
            bot.sendMessage(chat_id=chat[0], text=msg, parse_mode='Markdown')


def forecast():
    for day_shift in [[1, 'В субботу:'], [2, 'В воскресенье:']]:
        min_shift = day_shift[0] * 24 * 60
        digest_all(min_shift, day_shift[1])


if __name__ == "__main__":
    "Инициализируем расписание"
    scheduler = BlockingScheduler(timezone='Europe/Moscow')

    "Добавляем задачи"
    scheduler.add_job(digest_all, 'cron', day_of_week='mon-fri', hour=10, minute=00)
    scheduler.add_job(forecast, 'cron', day_of_week='fri', hour=10, minute=10)

    "Запускаем расписание"
    scheduler.start()
