# -*- coding: utf-8 -*-

from datetime import datetime
from mongoengine.fields import DateTimeField, EmailField, StringField, ListField, \
    BooleanField, IntField, ObjectId

from plus.mongoengine import Document
from core.model import PermissionModel, UserRoleModel


class AdminUserModel(Document):

    user_name = StringField(required=True, max_length=100)
    email = EmailField(required=True, unique=True)
    passwd = StringField(required=True, max_length=64, min_length=6)

    update_time = DateTimeField(default=datetime.now)
    create_time = DateTimeField(default=datetime.now)

    role = ListField(StringField(max_length=50, queryset=UserRoleModel))
    permissions = ListField(StringField(max_length=50, queryset=PermissionModel))

    active = BooleanField()

    meta = {
        'collection': 'admin_user',
        'ordering': ['-create_time'],
    }

    def clean(self):
        if not self.id:
            self.id = ObjectId()
        self.update_time = datetime.now()
        if not self.create_time:
            self.create_time = datetime.now()


class AdminMenuModel(Document):

    name = StringField(required=True, unique=True, max_length=50)
    alias = StringField(required=True, max_length=50)
    index = IntField()
    parent_name = StringField(max_length=50)
    parent_index = IntField()
    meta = {
        'collection': 'admin_menu',
        'ordering': ['-index'],
    }
