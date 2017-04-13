#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import logging
import os.path
import redis as redislib
import tornado.log
import tornado.web
import tornado.ioloop
import tornado.httpserver
from tornado.web import url
from tornado.options import define, options

from mongoengine import connect

from core.log import SMTPHandler

import uimodules

# handlers
from handlers.token import TokenHandler


#
from core.admin import sites

# version
version = 1.0

# begin

define("port", default=8000, help="run on the given port", type=int)
define("cookie_secret", default="secret", help="the secret to signed anything", type=str)
define("max_age_days", default=3, type=int, help="max cookie expire day")
define("debug", default=False, help="the debug is off on default", type=bool)
define("allow_remote_access", default=False, help="allow_remote_access")

define("mongo_dbname", "tornado_start", str, "the mongodb db's name")
define("mongo_host", "localhost", str, "the mongodb host")
define("mongo_port", str, "the mongodb db's port")


define("redis_host", default="127.0.0.1", type=str)
define("redis_port", default=6379, type=int)

define("smtp_server", help="the log mail smtp server address", type=str)
define("smtp_server_port", help="the log mail smtp server address port", type=int)
define("smtp_from_mail_addr", help="the log mail from mail address", type=str)
define("smtp_from_mail_passwd", help="the log mail from mail password", type=str)
define("smtp_to_mail_addr", help="send the log to those mail address", type=list)

define("super_user", default="admin", type=str, help="the super user for get token")
define("super_passwd", default="passwd", type=str, help="the pass word for super user")
define("super_white_list", default=[], type=list, help="the white ip address list for request")


# application
class Application (tornado.web.Application):

    def __init__(self, options):

        # connect db, just put there bcz must connect mongodb before admin register
        connect(options.mongo_dbname)

        self.options = options

        self.handlers = [
            url("/token", TokenHandler),

        ]

        self.handlers += sites.urls()

        self.settings = dict(
            debug=options.debug,

            template_path=os.path.join(os.path.dirname(__file__), 'templates'),
            static_path=os.path.join(os.path.dirname(__file__), 'static'),

            login_url="/token",
            admin_login_url="/admin/login",
            cookie_secret=options.cookie_secret,
            max_age_days=options.max_age_days,
            allow_remote_access=options.allow_remote_access,
            super_white_list=options.super_white_list,
            gzip=True,

            ui_modules=uimodules,
        )

        self.redis = redislib.Redis(

            connection_pool=redislib.ConnectionPool(
                host=options.redis_host,
                port=options.redis_port,
                db=0
            )
        )

        smtp_handler = SMTPHandler(
            (options.smtp_server, options.smtp_server_port),
            options.smtp_from_mail_addr,
            options.smtp_to_mail_addr,
            "Application's port %s" % options.port,
            (options.smtp_from_mail_addr, options.smtp_from_mail_passwd)
        )

        smtp_handler.setLevel(logging.ERROR)

        log = logging.getLogger("tornado.application")
        tornado.log.enable_pretty_logging(None, log)
        if not options.debug:
            log.addHandler(smtp_handler)

        self.log = log

        super(Application, self).__init__(self.handlers, **self.settings)


def main():
    options.parse_command_line()
    options.parse_config_file('settings.conf')
    http_server = tornado.httpserver.HTTPServer(Application(options))
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    main()
