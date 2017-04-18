# !/usr/bin/env python3
# -*- coding: utf-8 -*-

from tornado.web import authenticated, RequestHandler

from plus.mongoengine import Document

from plus.form import model_form


class AdminView(object):

    """Admin View Model

    :attr str __alias__: this will be show in page as main block name  and encode in url

    :atrr list list_exclude: show those model's attr in list page

     """

    __alias__ = None

    list_only = []  # show in list page

    page_exclude = []  # read create edit delete

    exclude = []
    only = []

    form_only = None
    form_exclude = None
    form_args = None

    menu = dict(
        alias=None,
        index=0,
        parent_name="Other",
        parent_index=0,
    )


class BaseHandler(RequestHandler):

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
                          exclude=self.admin_model.form_eclude,
                          field_args=self.admin_model.form_args,
                          )

    def get_current_user(self):
        user = self.get_secure_cookie("admin_user")
        if user:
            return

    def validate_permission(self, mod=None):
        user = self.get_current_user()

        if mod not in user.get("permissions", []):
            return
        return True


class ListHandler(BaseHandler):

    #  @authenticated
    async def get(self, page=1):
        per_page = self.get_argument("per_page", 10)
        q = self.get_argument("q", None)
        query = self.model.objects

        if q:
            query = query.search_text(q)

        for f in self.admin_model.exclude:
            query = query.exclude(f)

        for f in self.admin_model.only:
            query = query.only(f)

        data = query.paginate(page, per_page)
        return self.render("core/list.html",
                           model=data,
                           name=self.get_name(),
                           list_exclude=self.admin_model.list_exclude
                           )

    @authenticated
    async def delete(self):
        ids = self.get_arguments("ids", None)

        self.model.objects(id__in=ids).delete()

        return self.redirect(self.get_argument("next"))


class SingleFormHandler(BaseHandler):

    #  @authenticated
    async def get(self, id=None):
        if id:
            m = self.model.objects(id=id).first()
        else:
            m = self.model()

        f = self.form(self, obj=m)

        return self.render("core/single_form.html", model=m, form=f)

    async def post(self, id=None):
        if id:
            m = self.model.objects(id=id).first()
        else:
            m = self.model()
        f = self.form(self)
        if not f.validate():
            return self.render("core/single_form.html", model=m, form=f)

        f.populate_obj(m)
        m.save()
        return self.redirect(self.reverse_url(self.get_name() + "_edit", m.id))
