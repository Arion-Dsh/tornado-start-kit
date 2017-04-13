#! /usr/bin/env python3
# -*- coding: utf-8 -*-


from core.handler import BaseHandler
from .forms import AdminLoginForm
from .model import AdminUserModel


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
        print(form.errors)
