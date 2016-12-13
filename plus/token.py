#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import functools

from tornado.web import HTTPError, create_signed_value, decode_signed_value
from plus.redis import redis
import config


class RestfulToken(object):
    """ the RestfulToken
    """
    @classmethod
    def create_token(cls, uid):
        """ this medthod create a token at redis
        key named 'token:<uid>'
        """
        if not uid:
            raise HTTPError(403)
        secret = config.SECRET
        token = create_signed_value(secret=secret, name='token', value=uid)
        token = str(token)
        redis.set('token:%s' % uid, token)
        # redi.set('token:' + uid, config['TOKEN_MAX_DAY'] * 86400)
        return token

    @classmethod
    def validate_token(cls, token):
        """ verification token, if pass return uid
        """
        secret = config.SECRET
        token = decode_signed_value(secret=secret, name='token', value=token,
                                    max_age_days=config.TOKEN_MAX_DAY)
        token = str(token)
        if token:
            active_token = redis.get('token:%s' % token)
            if active_token is None or token != active_token:
                return

        return token

    @classmethod
    def delete_token(cls, uid):
        """ delete token
        """
        redis.remove('token:' + uid)


def restful_authenticated(method):
    """ this is restful aurthenticated
    must with <tornado.web.RequestHandler.authenticated>

    If you token verification failed it will raise 403 http error
    """
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        if not self.current_user:
            raise HTTPError(403)
        return method(self, *args, **kwargs)
    return wrapper
