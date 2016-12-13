#!/usr/bin/env python2
# -*- coding:utf-8 -*-

import logging

from tornado.web import RequestHandler, create_signed_value, decode_signed_value

from plus.token import RestfulToken


class BaseHander (RequestHandler):
    """ this is ordinary viwes basehandler.
    """

    def get_current_user(self):

        # token = RestfulToken.get_token()

        return self.get_secure_cookie('login_user')


class RestfulBaseHander (RequestHandler):

    def prepare(self):
        self.set_header('Content-Type', 'text/json')

        # 跨域
        if self.settings['allow_remote_access'] or self.settings['debug']:
            self._access_control_allow()

    def get_current_user(self):
        token = self.request.headers['Token'] or self.request.headers['Authorization']
        if token:
            uid = RestfulToken.validate_token(token)
            return uid

    def user_passwd_encode(self, passwd):
        return self.create_signed_value(name='passwd', value=passwd)

    def user_passwd_decode(self, passwd):
        return self.get_secure_cookie(name='passwd', value=passwd)

    def _access_control_allow(self):
        # 是否跨越
        self.set_header("Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS")
        self.set_header("Access-Control-Allow-Headers", "Content-Type, Depth, User-Agent, X-File-Size, "
                                                        "X-Requested-With, X-Requested-By, If-Modified-Since, "
                                                        "X-File-Name, Cache-Control, Token")
        self.set_header('Access-Control-Allow-Origin', '*')
