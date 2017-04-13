# !/usr/bin/env python3
# -*- coding: utf-8 -*-

from mongoengine import StringField, IntField

from plus.mongoengine import Document


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


class AdminModel(object):

    """Admin View Model

    :attr str __alias__: this will be show in page as main block name  and encode in url

    :atrr list list_exclude: show those model's attr in list page

     """

    __alias__ = None

    list_exclude = []  # show in list page

    only = []
    exclude = []

    form_only = None
    form_eclude = None
    form_args = None

    menu = dict(
        alias=None,
        index=0,
        parent_name="Other",
        parent_index=0,
    )
