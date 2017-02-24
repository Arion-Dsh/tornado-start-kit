#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import os.path
import redis as redislib
import tornado.web
import tornado.ioloop
import tornado.httpserver
from tornado.web import url
from tornado.options import define, options

define("port", default=8000, help="run on the given port", type=int)
define("secret", default="secret", help="the secret to signed anything")
define("debug", default=False, help="the debug is off on default", type=bool)
define("log_file_prefix", default='logs/server.log')

define("redis_host", default="localhost", type=str)
define("redis_port", default=6397, type=int)


class Application (tornado.web.Application):

    handlers = [
        url()
    ]
    settings = dict(
        template_path=os.path.join(os.path.dirname(__file__), 'templates'),
        static_path=os.path.join(os.path.dirname(__file__), 'static'),
        allow_remote_access=True,
        cookie_secret=options.secret,
        debug=options.debug,
        gzip=True,
    )

    def __init__(self):
        super(Application, self).__init__(self.handlers, **self.settings)
        self.redis = redislib.Redis(
            connection_pool=redislib.ConnectionPool(
                host=options.redis_host,
                port=options.redis_port,
                db=0
            )
        )


def main():
    options.parse_config_file('settings.conf')
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    main()
