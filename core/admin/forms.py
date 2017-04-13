#! /usr/bin/env python3
# -*- coding: utf-8 -*-

from wtforms.fields import StringField, PasswordField, SelectMultipleField
from wtforms.validators import email, required, length
from plus.form import Form


class AdminLoginForm(Form):
    email = StringField("Email", [email("must be email address")])
    passwd = PasswordField("Password", [required("password must be input"), length(min=6, message="min length is 6")])


class AdminAddUserForm(Form):
    user_name = StringField("User Name", [required(), length(min=5, message="user name's length must be 6 or more")])
    email = StringField("Email", [required(), email("must be email address")])
    passwd = PasswordField("Password", [required(), length(min=6)])
    groups = SelectMultipleField("Groups")
    permissions = SelectMultipleField("Permissions")


