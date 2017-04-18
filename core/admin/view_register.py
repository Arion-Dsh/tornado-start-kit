# -*- coding: utf-8 -*-

import bson
from tornado.web import url, RedirectHandler

from .view import AdminView
from .model import AdminMenuModel
from .handler import BaseHandler
from .auth import authenticated

__all__ = ("Register", "URLS")


class ListHandler(BaseHandler):

    @authenticated
    async def get(self, page=1):
        per_page = self.get_argument("per_page", 10)
        q = self.get_argument("q", None)
        query = self.db_objects()

        if q:
            query = query.search_text(q)

        data = query.paginate(page, per_page)
        return self.render("core/list.html",
                           model=data,
                           name=self.get_name(),
                           list_only=self.admin_model.list_only
                           )

    @authenticated
    async def delete(self):
        ids = self.get_arguments("ids", None)

        self.model.objects(id__in=ids).delete()

        return self.redirect(self.get_argument("next"))


class SingleFormHandler(BaseHandler):

    @authenticated
    async def get(self, id=None, form=None):
        if id:
            m = self.db_objects(id=id).first()
        else:
            m = self.model()

        if getattr(m, "passwd", None):
            m.passwd = self.passwd_decode(m.passwd)

        f = form or self.form(self, obj=m)

        return self.render("core/single_form.html", model=m, form=f)

    @authenticated
    async def post(self, id=None):
        if id:
            m = self.model.objects(id=id).first()
        else:
            m = self.model()
        f = self.form(self)

        if not f.validate():
            return self.render("core/single_form.html", model=m, form=f)

        f.populate_obj(m)
        if getattr(m, "passwd", None):
            m.passwd = self.passwd_encode(m.passwd).decode()

        if not m.id:
            m.id = bson.ObjectId()
        try:
            m.save()
        except Exception as e:
            self.flash(self.format_mongo_err(str(e)), "error")
            return self.redirect(self.reverse_url(self.get_name() + "_add"))
        return self.redirect(self.reverse_url(self.get_name() + "_edit", m.id))


class URLS():
    urls = []
    registeries = []

    def __call__(self):
        _urls = []
        for r in self.registeries:
            _urls += r.regist()
        return self.urls + _urls


class Register():

    def __init__(self, model, admin_model=AdminView):
        self.model = model
        self.admin_model = admin_model

        URLS.registeries.append(self)

    def regist(self):
        model = self.model
        admin_model = self.admin_model
        urls = []
        # list page
        list_ = type("%sList" % model._class_name, (ListHandler, ),
                     dict(model=model, admin_model=admin_model))
        urls.append(
            url("/admin/%s/(\d+)" % list_.get_name(), list_, name="%s_list" % list_.get_name())
        )
        urls.append(
            url("/admin/%s" % list_.get_name(), RedirectHandler, {"url": "/admin/%s/1" % list_.get_name()})
        )

        # add to menu
        assert(isinstance(admin_model.menu, dict) and set(["parent_name", "parent_index", "index"]) <= set(admin_model.menu))
        menu = AdminMenuModel.objects(name=list_.get_name()).first()
        if not menu:
            menu = AdminMenuModel()
            menu.name = list_.get_name()
            menu.alias = admin_model.menu.get("alias", None) or list_.get_name()
            menu.index = admin_model.menu.get("index")
            menu.parent_name = admin_model.menu.get("parent_name")
            menu.parent_index = admin_model.menu.get("parent_index")

            try:
                menu.save()
            except Exception as e:
                raise(e)

        # single_page
        single_form = type("%sSingleForm" % model._class_name, (SingleFormHandler, ),
                           dict(model=model, admin_model=admin_model))
        urls.append(
            url("/admin/%s/add" % single_form.get_name(), single_form, name="%s_add" % single_form.get_name()),
        )
        urls.append(
            url("/admin/%s/([^/]+)/edit" % single_form.get_name(), single_form, name="%s_edit" % single_form.get_name())
        )

        return urls
