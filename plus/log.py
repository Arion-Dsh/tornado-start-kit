# -*- coding: utf-8 -*-
""" there ars some log handler

"""

import logging
import logging.handlers
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate


class SMTPHandler(logging.handlers.SMTPHandler):
    """ smtp mail handler

    usage
        mail_handler = SMTPHandler("smtp server", "fromaddr", ["admin mail",], "subject", ("smtp user", "smtp user passwd"))
        mail_handler.setLevel(logging.ERROR)
        logger = logging.getLogger()
        logger.addHander(mail_handler)

    """

    def emit(self, record):
        try:
            if 'StreamClosedError' in record.getMessage():
                return

            port = self.mailport
            if not port:
                port = smtplib.SMTP_PORT
            smtp = smtplib.SMTP_SSL(self.mailhost, port)
            msg = MIMEMultipart('alternative')
            msg['Subject'] = self.getSubject(record)
            msg['From'] = self.fromaddr
            msg['To'] = ",".join(self.toaddrs)
            msg['Date'] = formatdate()

            msg.attach(MIMEText(record.getMessage(), 'plain'))
            if record.exc_text:
                info = (self.formatter or logging._defaultFormatter)._fmt % record.__dict__
                html = ('<html><head></head><body><p style="white-space: pre-wrap; word-wrap: break-word;">%s</p>%s</body></html>') % (info, record.exc_text)
                msg.attach(MIMEText(html, 'html'))
            if self.username:
                smtp.login(self.username, self.password)

            smtp.sendmail(self.fromaddr, self.toaddrs, msg.as_string())
            smtp.quit()
        except:
            self.handleError(record)
