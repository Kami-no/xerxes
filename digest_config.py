#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from os import getenv

bot_token = getenv('secret_telegram_token')
bot_master = [1234567]

tz_name = 'Europe/Moscow'

ex_host = 'ex.any.ru'
ex_user = getenv('secret_exchange_user')
ex_pass = getenv('secret_exchange_pass')
ex_cal = 'admin@any.ru'
ex_tz = 'Europe/Moscow'

db_host = 'mysql'
db_user = getenv('secret_mysql_user')
db_pass = getenv('secret_mysql_pass')
db_name = 'xerxes'
