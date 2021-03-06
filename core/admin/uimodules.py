#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import itertools
import tornado.web

from .model import AdminMenuModel

__all__ = ("AdminListPage", "AdminMenu", "AdminPageName")


class AdminListPage(tornado.web.UIModule):

    def render(self, models, model_name, fields=[]):

        return self.render_string("core/modules/list.html", models=models, model_name=model_name, fields=fields)


class AdminMenu(tornado.web.UIModule):

    def render(self, current):

        query = AdminMenuModel.objects.all()
        menus = []
        for k, g in itertools.groupby(query, lambda menu: menu.parent_name):
            menus.append((k, list(g)))

        return self.render_string("core/modules/menu.html", menus=menus, current=current)


class AdminPageName(tornado.web.UIModule):

    def render(self, name, type_=None):
        menu = AdminMenuModel.objects(name=name).first()
        name = menu.alias
        if type_:
            name = "%s: %s" % (name, type_)

        return name
