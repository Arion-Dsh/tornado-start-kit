#! /usr/bin/env python3
# -*- coding: utf-8 -*-

from plus.mongoengine import Document
from plus.form import model_form
from core.handler import BaseHandler as BHandler

from .forms import AdminLoginForm
from .model import AdminUserModel
from .view import AdminView


class BaseHandler(BHandler):

    model = Document
    admin_model = AdminView

    @classmethod
    def get_name(cls):
        if cls.admin_model.__alias__:
            return cls.admin_model.__alias__
        return cls.model._class_name.lower()

    @property
    def form(self):
        return model_form(self.model,
                          only=self.admin_model.form_only,
                          exclude=self.admin_model.form_exclude,
                          field_args=self.admin_model.form_args,
                          )

    def db_objects(self, *args, **kwargs):
        query = self.model.objects(*args, **kwargs)
        for f in self.admin_model.exclude:
            query = query.exclude(f)

        for f in self.admin_model.only:
            query = query.only(f)

        return query

    def get_current_user(self):
        id = self.get_secure_cookie("admin_user")
        if not id:
            return
        user = AdminUserModel.objects(id=id.decode()).first()
        return user

    def validate_permission(self, mod=None):
        user = self.get_current_user()

        if mod not in user.get("permissions", []):
            return
        return True


class AdminUserLoginHandler(BaseHandler):

    async def get(self):
        form = AdminLoginForm(self)

        return self.render("core/login.html", form=form)

    async def post(self):

        form = AdminLoginForm(self)
        if form.validate():
            user = AdminUserModel.objects(email=form.email.data).first()
            if not user:
                self.flash("have no this user.", "error")
                return self.redirect(self.request.uri)
            if self.passwd_decode(user.passwd) != form.passwd.data:
                self.flash("email or passwd is wrong.", "error")
                return self.redirect(self.request.uri)
            self.set_secure_cookie("admin_user", str(user.id))

            return self.redirect(self.get_argument("next", "/admin"))
        return self.render("core/login.html", form=form)


class AdminUserLogoutHandler(BaseHandler):

    async def get(self):
        self.clear_cookie("admin_user")
        self.redirect(self.reverse_url("admin_login"))
