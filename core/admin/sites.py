# !/usr/bin/env python3
# -*- coding: utf-8 -*-

from tornado.web import url

from .view_register import Register, URLS

from .handler import AdminUserLoginHandler

from .model import AdminPermissionGroupModel, AdminUserModel
from .view import AdminView

__all__ = ("register", "urls")


register = Register


def urls():
    _urls = [
        url("/admin/login", AdminUserLoginHandler, name="admin_login"),
    ]
    return _urls + URLS()()


class PG(AdminView):
    __alias__ = "pg"
    form_args = {
        "create_time": {"label": "Create Time", "render_kw": {"readonly": ""}},
        "update_time": {"label": "Update Time", "render_kw": {"readonly": ""}}
    }


register(AdminPermissionGroupModel, PG)


class User(AdminView):
    __alias__ = "user"

    form_args = {
        "passwd": {"label": "Password", "render_kw": {"type": "password"}},
        "create_time": {"label": "Create Time", "render_kw": {"readonly": ""}},
        "update_time": {"label": "Update Time", "render_kw": {"readonly": ""}}
    }


register(AdminUserModel, User)
