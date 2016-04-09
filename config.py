#!/usr/bin/env python3
# -*- coding:utf-8 -*-

DB_HOST = 'localhost'
DB_PORT = 27017
DB_NAME = 'test'

REDIS_HOST = 'localhost'
REDIS_PORT = 6379



SECRET = 'Arion&kelly' # 'anything you think SECRET. use to cookies secret'
TOKEN_MAX_DAY = 31

try:
    import locale_config
except:
    pass