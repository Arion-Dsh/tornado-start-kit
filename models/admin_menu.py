# -*- coding: utf-8 -*-

from datetime import datetime
from mongoengine import DateTimeField, StringField, ListField

from plus.mongoengine import Document


class AdminMenuModel(Document):

    name = StringField(required=True)
    alias = StringField()

    update_time = DateTimeField(default=datetime.now)
    create_time = DateTimeField(default=datetime.now)

    groups = ListField(StringField())

    meta = {
        'collection': 'admin_menu',
        'ordering': ['-create_time'],
    }

    def clean(self):
        self.update_time = datetime.now()
