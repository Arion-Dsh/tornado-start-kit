# -*- coding: utf-8 -*-

from datetime import datetime
from mongoengine.fields import DateTimeField, EmailField, StringField, ListField, \
    BooleanField, IntField, ObjectId

from plus.mongoengine import Document


class AdminUserModel(Document):

    user_name = StringField(required=True, max_length=100)
    email = EmailField(required=True, unique=True)
    passwd = StringField(required=True, max_length=64, min_length=6)

    update_time = DateTimeField(default=datetime.now)
    create_time = DateTimeField(default=datetime.now)

    role = ListField(StringField())
    permissions = ListField(StringField())

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


class AdminPermissionGroupModel(Document):

    name = StringField(unique=True, max_length=50, required=True)
    permissions = ListField(StringField(max_length=20))
    # pers = ReferenceField("AdminPermissionModel")
    create_time = DateTimeField(default=datetime.now)
    update_time = DateTimeField(default=datetime.now)

    meta = {
        'collection': 'admin_user_group',
        'ordering': ['-create_time'],
    }

    def clean(self):
        self.update_time = datetime.now()


class AdminPermissionModel(Document):

    name = StringField(unique=True, required=True)
    create_time = DateTimeField(default=datetime.now)

    meta = {
        'collection': 'admin_permission',
        'ordering': ['-create_time']
    }


class AdminMenuModel(Document):

    name = StringField(required=True, unique=True)
    alias = StringField(max_length=50)
    index = IntField()
    parent_name = StringField(max_length=50)
    parent_index = IntField()
    meta = {
        'collection': 'admin_menu',
        'ordering': ['-index'],
    }
