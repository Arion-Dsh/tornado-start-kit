#!/usr/bin/env python
# -*- coding:utf-8 -*-

import re
import logging
from tornado.web import RequestHandler
from core.token import RESTfulTokenMixin
from core.signed import AESCipher
from core.flash import FlashMessageMixIn

__all__ = ("BaseHandler", "RESTfulBaseHandler")


class BHandlerMixin(object):

    @property
    def app_options(self):
        """ Application's options！
        deferent the request's options method

        """
        return self.application.options

    @property
    def redis(self):
        return self.application.redis

    @property
    def log(self):
        return logging.getLogger()

    def passwd_encode(self, passwd):
        return self.signed.encrypt(passwd)

    def passwd_decode(self, passwd):

        return self.signed.decrypt(passwd)

    def format_mongo_err(self, text, type_="unique"):
        if type_ == "unique":
            print(text)
            field = re.findall(r'index: (.+)_1 dup', text)[0]
            value = re.findall(r'{ : "(.+)" }', text)[0]
            return '%s:%s already token' % (field, value)

    @property
    def signed(self):
        aes = AESCipher(self.settings.get('secret', 'secret'))
        return aes


class BaseHandler (RequestHandler, BHandlerMixin, FlashMessageMixIn):
    """ this is ordinary viwes basehandler.
    """

    def get_current_user(self):

        return self.get_secure_cookie('login_user')

    def get_admin_login_url(self):
        self.require_setting("login_url", "@core.admin.authenticated")
        return self.application.settings["admin_login_url"]


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

    def __access_control_allow(self):
        # 是否跨越
        self.set_header("Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS")
        self.set_header("Access-Control-Allow-Headers", "Content-Type, Depth, User-Agent, X-File-Size, "
                                                        "X-Requested-With, X-Requested-By, If-Modified-Since, "
                                                        "X-File-Name, Cache-Control, Authorization")
        self.set_header('Access-Control-Allow-Origin', '*')
