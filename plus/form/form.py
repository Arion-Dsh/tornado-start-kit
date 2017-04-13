#!/usr/bin/env python3
# -*- coding:utf-8 -*-

from wtforms import Form as wtForm
from tornado import locale

__all__ = ("Form", )


class Form(wtForm):
    """
    `WTForms` wrapper for Tornado.
    """

    def __init__(self, formdata=None, obj=None, prefix='', **kwargs):
        """
        Wrap the `formdata` with the `TornadoInputWrapper` and call the base
        constuctor.
        """
        self._handler = formdata
        super(Form, self).__init__(TornadoInputWrapper(formdata),
                                   obj=obj, prefix=prefix, **kwargs)

    def _get_translations(self):
        if self._handler.get_user_locale():
            _locale = self._handler.get_user_locale()
        else:
            _locale = locale.get("en_US")
        return TornadoLocaleWrapper(_locale)


class TornadoInputWrapper(object):

    def __init__(self, handler):
        self._handler = handler

    def __iter__(self):
        return iter(self._handler.request.arguments)

    def __len__(self):
        return len(self._handler.request.arguments)

    def __contains__(self, name):
        return (name in self._handler.request.arguments)

    def getlist(self, name):
        return self._handler.get_arguments(name)


class TornadoLocaleWrapper(object):

    def __init__(self, _locale):
        self.locale = _locale

    def gettext(self, message):
        return self.locale.translate(message)

    def ngettext(self, message, plural_message, count):
        return self.locale.translate(message, plural_message, count)
