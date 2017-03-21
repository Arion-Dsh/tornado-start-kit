#!/usr/bin/env python
# -*- coding:utf-8 -*-

import logging
from tornado.web import RequestHandler
from plus.token import RESTfulTokenMixin
from plus.signed import AESCipher


class BHandlerMixin(object):

    @property
    def app_options(self):
        """ Application 配置！
        区别与 request 的options 方法

        """
        return self.application.options

    @property
    def redis(self):
        return self.application.redis

    @property
    def log(self):
        return logging.getLogger()


class BaseHandler (RequestHandler, BHandlerMixin):
    """ this is ordinary viwes basehandler.
    """

    def get_current_user(self):

        return self.get_secure_cookie('login_user')


class RESTfulBaseHandler (RequestHandler, BHandlerMixin, RESTfulTokenMixin):

    def prepare(self):
        self.set_header('Content-Type', 'text/json')
        self.set_header("Access-Control-Allow-Headers", "X-File-Name, Cache-Control, Authorization")
        # 跨域
        if self.settings['allow_remote_access'] or self.settings['debug']:
            self.__access_control_allow()

    def get_current_user(self):

        token = self.request.headers.get('Authorization')

        # has no token and debug is on or remote_ip in white list
        if not token and (self.settings['debug'] or self.request.remote_ip in self.settings['super_white_list']):
            return True

        if token and token.startswith("Bearer "):
            user = self.verify_jwt(token[7:])
            if user:
                self.token = token[7:]
                return user

    def user_passwd_encode(self, passwd):
        return self.signed.encrypt(passwd)

    def user_passwd_decode(self, passwd):

        return self.signed.decrypt(passwd)

    @property
    def signed(self):
        aes = AESCipher(self.settings.get('secret', 'secret'))
        return aes

    def __access_control_allow(self):
        # 是否跨越
        self.set_header("Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS")
        self.set_header("Access-Control-Allow-Headers", "Content-Type, Depth, User-Agent, X-File-Size, "
                                                        "X-Requested-With, X-Requested-By, If-Modified-Since, "
                                                        "X-File-Name, Cache-Control, Authorization")
        self.set_header('Access-Control-Allow-Origin', '*')
