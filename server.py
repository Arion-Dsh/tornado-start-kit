#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import logging
import os.path
import tornado.web
import tornado.ioloop
import tornado.httpserver
from tornado.web import URLSpec as url
from tornado.options import define, options
from tornado.log import app_log

from handlers.user import UserSignUpHandler

import config

# 链接数据库
from mongoengine import connect
db_name = config.DB_NAME

db = connect(db_name)

define("port", default=8000, help="run on the given port", type=int)
define("log_file_prefix", default='/opt/logs/tornado/my_server.log')


class Application (tornado.web.Application):

    handlers = [
        url(r'/user/sign_up', UserSignUpHandler, name="sign_up"),
    ]
    settings = dict(
        template_path=os.path.join(os.path.dirname(__file__), 'templates'),
        static_path=os.path.join(os.path.dirname(__file__), 'static'),
        allow_remote_access=True,
        cookie_secret=config.SECRET,
        debug=True,
        gzip=True,
    )

    def __init__(self):
        handlers = self.handlers
        settings = self.settings
        super(Application, self).__init__(handlers, **settings)


def main():
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == '__main__':
    main()
