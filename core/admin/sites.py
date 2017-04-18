# !/usr/bin/env python3
# -*- coding: utf-8 -*-

from tornado.web import url

from core.model import UserRoleModel, PermissionModel
from .view_register import Register, URLS

from .handler import AdminUserLoginHandler, AdminUserLogoutHandler

from .model import AdminUserModel, AdminMenuModel
from .view import AdminView

__all__ = ("register", "urls")


register = Register


def urls():
    _urls = [
        url("/admin/login", AdminUserLoginHandler, name="admin_login"),
        url("/admin/logout", AdminUserLogoutHandler, name="admin_logout")
    ]
    return _urls + URLS()()


class AdminRole(AdminView):
    __alias__ = "admin_role"
    form_args = {
        "permissions": {"label_attr": "name", "value_attr": "name"},
        "create_time": {"label": "Create Time", "render_kw": {"readonly": ""}},
        "update_time": {"label": "Update Time", "render_kw": {"readonly": ""}}
    }


register(UserRoleModel, AdminRole)


class User(AdminView):
    __alias__ = "admin_user"

    list_only = ["user_name", "create_time", "active"]

    form_args = {

        "role": {"label_attr": "name", "value_attr": "name"},
        "permissions": {"label_attr": "name", "value_attr": "name"},
        "passwd": {"label": "Password", "render_kw": {"type": "password"}},
        "create_time": {"label": "Create Time", "render_kw": {"readonly": ""}},
        "update_time": {"label": "Update Time", "render_kw": {"readonly": ""}}
    }


register(AdminUserModel, User)


class AdminMenu(AdminView):
    __alias__ = "admin_menu"

    page_exclude = ["create"]

    list_only = ["name", "alias", "index", "parent_name", "parent_index"]

    form_args = {
        'name': {"render_kw": {"readonly": ""}}
    }


register(AdminMenuModel, AdminMenu)

register(PermissionModel)
