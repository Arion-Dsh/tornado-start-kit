#!/usr/bin/env python3
#-*- coding:utf-8 -*-

import os.path
import logging

from tornado.options import options
from tornado.testing import AsyncHTTPTestCase
from server import Application


log = logging.getLogger()


class BaseCase(AsyncHTTPTestCase):

    def setUp(self):
        super(BaseCase, self).setUp()
        self.log = log

    def get_app(self):

        self.app = Application
        s_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "settings.conf"))
        options.parse_config_file(s_file)
        return self.app()
