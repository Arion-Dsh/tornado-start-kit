# !/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime
from mongoengine import StringField, ListField, DateTimeField, ReferenceField


from plus.mongoengine import Document


class PermissionModel(Document):

    name = StringField(unique=True, required=True, max_length=50)
    alias = StringField(max_length=50)

    meta = {
        'collection': 'permission',
        'ordering': ['-create_time']
    }


class UserRoleModel(Document):

    name = StringField(unique=True, max_length=50, required=True)
    permissions = ListField(StringField(max_length=20, queryset=PermissionModel))
    pers = ListField(ReferenceField("PermissionModel"))
    create_time = DateTimeField(default=datetime.now)
    update_time = DateTimeField(default=datetime.now)

    meta = {
        'collection': 'user_role',
        'ordering': ['-create_time'],
    }

    def clean(self):
        self.update_time = datetime.now()
