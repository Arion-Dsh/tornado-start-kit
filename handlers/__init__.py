#!/usr/bin/env python
# -*- coding:utf-8 -*-

from tornado.web import RequestHandler

from plus.token import RestfulToken

from plus.signed import AESCipher


class BaseHander (RequestHandler):
    """ this is ordinary viwes basehandler.
    """

    def get_current_user(self):

        # token = RestfulToken.get_token()

        return self.get_secure_cookie('login_user')


class RestfulBaseHander (RequestHandler):

    def prepare(self):
        self.set_header('Content-Type', 'text/json')
        self.set_header("Access-Control-Allow-Headers", "X-File-Name, Cache-Control, Authorization")
        # 跨域
        if self.settings['allow_remote_access'] or self.settings['debug']:
            self._access_control_allow()

    @property
    def token(self):
        # soooooo ugly
        settings = dict(
            secret=self.settings.get('secret'),
            redis=self.application.redis
        )
        return RestfulToken(settings)

    def get_current_user(self):
        token = self.request.headers['Authorization']
        if token:
            uid = self.token.validate(token)
            return uid

    def user_passwd_encode(self, passwd):
        return self.signed.encrypt(passwd)

    def user_passwd_decode(self, passwd):

        return self.signed.decrypt(passwd)

    @property
    def signed(self):
        aes = AESCipher(self.settings.get('secret', 'secret'))
        return aes

    def _access_control_allow(self):
        # 是否跨越
        self.set_header("Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS")
        self.set_header("Access-Control-Allow-Headers", "Content-Type, Depth, User-Agent, X-File-Size, "
                                                        "X-Requested-With, X-Requested-By, If-Modified-Since, "
                                                        "X-File-Name, Cache-Control, Authorization")
        self.set_header('Access-Control-Allow-Origin', '*')


class TestHandler(RequestHandler):

    async def get(self):

        self.finish("1")
