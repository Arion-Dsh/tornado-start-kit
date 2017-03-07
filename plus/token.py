#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import datetime
import python_jwt as jwt


class RESTfulTokenMixin(object):
    """ the RESTfulTokenMixin must use with `tornado.web.RequestHandler`
    """

    def get_jwt(self, payload):
        """ this medthod create a token with python_jwt
        """
        assert isinstance(payload, dict)
        assert('id' in payload)

        self.require_setting("jwt_secret", "crypto jwt")
        expire_days = self.settings.get("max_age_days", 1)
        return jwt.generate_jwt(payload, self.settings['jwt_secret'],
                                datetime.timedelta(days=expire_days))

    def verify_jwt(self, token):
        """ verification token, if pass return claims
        """
        try:
            _, claims = jwt.verify_jwt(token, self.settings['jwt_secret'], "HS256")
        except:
            return

        is_blacked = self.redis.get("jwt_blacked:%s" % claims["id"])

        if is_blacked:
            return

        return claims

    def del_jwt(self, token):
        """ delete token
        """
        self.require_setting("jwt_secret", "crypto jwt")
        token = token.split(".")
        self.redis.set("jwt_blacked:%s" % token[-1], 1)
        self.redis.expire("jwt_blacked:%s" % token[-1], 86400 * self.settings["max_age_days"])
