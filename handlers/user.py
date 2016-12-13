#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import tornado.web
from tornado import gen
from tornado.web import HTTPError, RequestHandler

from handlers import RestfulBaseHander
from models.user import User
from plus.token import restful_authenticated as auth, RestfulToken


class UserSignUpHandler(RestfulBaseHander):
    """

    """
    def get(self):
        user = User.objects.exclude('passwd').all().to_json()
        self.write(user)

    @tornado.web.asynchronous
    # @gen.coroutine
    def post(self):
        user_name = self.get_body_argument('user_name', '')
        email = self.get_body_argument('email', '')
        passwd = self.get_body_argument('passwd', '')

        user = User.objects(email=email).first()
        if user:
            raise HTTPError(403)

        passwd = self.user_passwd_encode(passwd)
        user = User(
            user_name=user_name,
            email=email,
            passwd=passwd
        )
        user.save()
        token = RestfulToken.create_token(user.id)
        self.finish(dict(token=token))
