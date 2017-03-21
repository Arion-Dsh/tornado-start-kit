# -*- coding: utf-8 -*-

import base64
import json
import jws

from test.base_test import BaseCase


class TokenHandlerTest(BaseCase):

    def test_get(self):
        self.log.info("test get")
        auth = base64.b64encode(b"admin:admin")
        headers = dict(
            Authorization=b"Basic %s" % auth
        )

        req = self.fetch("/token", headers=headers)

        body = json.loads(req.body)
        _, claims, _ = body['token'].split('.', 3)

        user = jws.utils.from_base64(claims).decode('utf-8')
        user = json.loads(user)
        self.assertEqual(user['id'], 0)

    def test_fail_get(self):
        self.log.info("test get fail")
        auth = base64.b64encode(b"admin:test")
        headers = dict(
            Authorization=b"Basic %s" % auth
        )

        req = self.fetch("/token", headers=headers)
        self.assertEqual(req.code, 401)

    def test_delete(self):
        auth = base64.b64encode(b"admin:admin")
        headers = dict(
            Authorization=b"Basic %s" % auth
        )

        req = self.fetch("/token", headers=headers)

        body = json.loads(req.body)

        token = "Bearer %s" % body['token']

        headers = dict(
            Authorization=token
        )

        self.log.info(" test del token")
        req = self.fetch("/token", method="DELETE", headers=headers)
        body = json.loads(req['body'])
        self.assertIs(True, body['result'])
