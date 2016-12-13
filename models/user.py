# -*- coding:utf-8 -*-

from mongoengine import FileField, DateTimeField, ListField, IntField, \
    StringField, SequenceField, ReferenceField, EmailField
from plus.mongoengine_plus import Document


class DocMinix(object):
    pass


class User(Document, DocMinix):
    email = EmailField(primary_key=True, required=True, unique=True)
    user_name = StringField()
    passwd = StringField()
