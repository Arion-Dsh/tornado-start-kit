#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import functools

from tornado.web import HTTPError, create_signed_value, decode_signed_value
from plus.redis import redis


class RestfulToken(object):
    """ the RestfulToken
    """
    def __init__(self, settings=dict()):
        self.secret = settings.get('secret', 'secret')
        self.max_age_days = settings.get('max_age_days', 3)

    def createn(self, uid):
        """ this medthod create a token at redis
        key named 'token:<uid>'
        """
        if not uid:
            raise HTTPError(403)
        token = create_signed_value(secret=self.secret, name='token', value=uid,
                                    max_age_days=self.max_age_days)
        token = str(token)
        redis.set('token:%s' % uid, token).expire('token:%s' % uid, self.max_age_days * 86400)
        # redi.set('token:' + uid, config['TOKEN_MAX_DAY'] * 86400)
        return token

    def validate(self, token):
        """ verification token, if pass return uid
        """
        token = decode_signed_value(secret=self.secret, name='token', value=token,
                                    max_age_days=self.max_age_days)
        token = str(token)
        if token:
            active_token = redis.get('token:%s' % token)
            if active_token is None or token != active_token:
                return

        return token

    def delete(self, uid):
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
