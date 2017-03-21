# -*- coding: utf-8 -*-

import logging
from unittest import TestCase

from plus.log import SMTPHandler


class SMTPLogTest(TestCase):

    def setUp(self):
        smtp_handler = SMTPHandler(
            ("*", 465),
            "*",
            ["*"],
            "smtp test",
            ("*", "*"),
        )
        smtp_handler.setLevel(logging.ERROR)
        self.logger = logging.getLogger()
        self.logger.addHandler(smtp_handler)

    def test_sentmail(self):
        self.logger.error("this is a test")
        self.logger.error("test mail log")
        try:
            raise Exception('exc1')
        except:
            self.logger.exception('test message')
