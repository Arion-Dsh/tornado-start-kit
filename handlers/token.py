# -*- coding: utf-8 -*-

import base64
from tornado.web import authenticated
from tornado.gen import coroutine

from handlers import RESTfulBaseHandler


class TokenHandler(RESTfulBaseHandler):

    @coroutine
    def get(self):
        """获取token

        :url: /token
        :method: get

        返回token::

            {
            "token": wrwersf.kulyeE2.xgwqoj
            }


        """
        auth = self.request.headers.get("Authorization")
        if auth and auth.startswith("Basic "):
            auth = base64.b64decode(auth[6:]).decode("utf-8")
            user, passwd = auth.split(":", 1)
            if user == self.app_options.super_user and passwd == self.app_options.super_passwd:
                token = self.get_jwt(dict(id=0, user=user))
                return self.finish(dict(token=token))
        self.set_status(401)

        self.set_header('WWW-Authenticate', 'Basic realm="default"')
        self.finish()

    #  @coroutine
    @authenticated
    def delete(self):
        """ 删除token， 普通上来说上来说这个是没有比 因为在客户端
        不携带token就可以了。当鉴于token可能被盗，所以服务器删除。

        :url: /token
        :method: delete

        成功返回::

            {
                "result": true
            }

        """
        self.del_jwt(self.token)
        self.finish(dict(result=True))
