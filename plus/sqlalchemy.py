#!/usr/bin/env python
# coding=utf-8
"""
    sqlalchemy.py
    ~~~~~~~~~~~~~
    :copyright: (c) 2010 by Armin Ronacher. From flask-sqlalchemy.
    :license: BSD, see LICENSE for more details.
"""

import os
import re
import uuid
import functools
from functools import partial
from threading import Lock
import sqlalchemy
from sqlalchemy import orm
from sqlalchemy.orm.session import Session
from sqlalchemy.orm import attributes, object_mapper
from sqlalchemy.orm.properties import RelationshipProperty
from sqlalchemy.orm.interfaces import MapperExtension, SessionExtension, \
    EXT_CONTINUE
from sqlalchemy.orm.exc import UnmappedClassError
from sqlalchemy.engine.url import make_url
from sqlalchemy.ext.declarative import declarative_base, DeclarativeMeta
from sqlalchemy.util import to_list
from .signals import Namespace

import tornado.web

_camelcase_re = re.compile(r'([A-Z]+)(?=[a-z0-9])')
_signals = Namespace()

models_committed = _signals.signal('models-committed')
before_models_committed = _signals.signal('before-models-committed')


def _make_table(db):
    def _make_table(*args, **kwargs):
        if len(args) > 1 and isinstance(args[1], db.Column):
            args = (args[0], db.metadata) + args[1:]
        return sqlalchemy.Table(*args, **kwargs)
    return _make_table


def _set_default_query_class(d):
    if 'query_class' not in d:
        d['query_class'] = BaseQuery


def _wrap_with_default_query_class(fn):
    @functools.wraps(fn)
    def newfn(*args, **kwargs):
        _set_default_query_class(kwargs)
        if "backref" in kwargs:
            backref = kwargs['backref']
            if isinstance(backref, str):
                backref = (backref, {})
            _set_default_query_class(backref[1])
        return fn(*args, **kwargs)
    return newfn


def _defines_primary_key(d):
    """Figures out if the given dictonary defines a primary key column."""
    return any(v.primary_key for k, v in d.items()
               if isinstance(v, sqlalchemy.Column))


def _include_sqlalchemy(obj):
    for module in sqlalchemy, sqlalchemy.orm:
        for key in module.__all__:
            if not hasattr(obj, key):
                setattr(obj, key, getattr(module, key))
    # Note: obj.Table does not attempt to be a SQLAlchemy Table class.
    obj.Table = _make_table(obj)
    obj.mapper = signalling_mapper
    obj.relationship = _wrap_with_default_query_class(obj.relationship)
    obj.relation = _wrap_with_default_query_class(obj.relation)
    obj.dynamic_loader = _wrap_with_default_query_class(obj.dynamic_loader)


class _BoundDeclarativeMeta(DeclarativeMeta):

    def __new__(cls, name, bases, d):
        tablename = d.get('__tablename__')

        # generate a table name automatically if it's missing and the
        # class dictionary declares a primary key.  We cannot always
        # attach a primary key to support model inheritance that does
        # not use joins.  We also don't want a table name if a whole
        # table is defined
        if not tablename and not d.get('__table__') and \
           _defines_primary_key(d):
            def _join(match):
                word = match.group()
                if len(word) > 1:
                    return ('_%s_%s' % (word[:-1], word[-1])).lower()
                return '_' + word.lower()
            d['__tablename__'] = _camelcase_re.sub(_join, name).lstrip('_')

        return DeclarativeMeta.__new__(cls, name, bases, d)

    def __init__(self, name, bases, d):
        bind_key = d.pop('__bind_key__', None)
        DeclarativeMeta.__init__(self, name, bases, d)
        if bind_key is not None:
            self.__table__.info['bind_key'] = bind_key


class _SignallingSession(Session):

    def __init__(self, db, autocommit=False, autoflush=False, **options):
        self.app = db.get_app()
        self.sender = db.sender
        self._model_changes = {}
        Session.__init__(self, autocommit=autocommit, autoflush=autoflush,
                         expire_on_commit=True,
                         extension=db.session_extensions,
                         bind=db.engine, **options)


class _QueryProperty(object):

    def __init__(self, sa):
        self.sa = sa

    def __get__(self, obj, type):
        try:
            mapper = orm.class_mapper(type)
            if mapper:
                return type.query_class(mapper, session=self.sa.session())
        except UnmappedClassError:
            return None


class _SignalTrackingMapperExtension(MapperExtension):

    def after_delete(self, mapper, connection, instance):
        return self._record(mapper, instance, 'delete')

    def after_insert(self, mapper, connection, instance):
        return self._record(mapper, instance, 'insert')

    def after_update(self, mapper, connection, instance):
        return self._record(mapper, instance, 'update')

    def _record(self, mapper, model, operation):
        pk = tuple(mapper.primary_key_from_instance(model))
        #orm.object_session(model)._model_changes[pk] = (model, operation)
        changes = {}

        for prop in object_mapper(model).iterate_properties:
            if not isinstance(prop, RelationshipProperty):
                try:
                    history = attributes.get_history(model, prop.key)
                except:
                    continue

                added, unchanged, deleted = history

                newvalue = added[0] if added else None

                if operation == 'delete':
                    oldvalue = unchanged[0] if unchanged else None
                else:
                    oldvalue = deleted[0] if deleted else None

                if newvalue or oldvalue:
                    changes[prop.key] = (oldvalue, newvalue)

        orm.object_session(model)._model_changes[pk] = (model.__tablename__, pk[0], changes, operation)
        return EXT_CONTINUE


class _SignallingSessionExtension(SessionExtension):

    def before_commit(self, session):
        d = session._model_changes
        if d:
            before_models_committed.send(session.sender, changes=list(d.values()))
        return EXT_CONTINUE

    def after_commit(self, session):
        d = session._model_changes
        if d:
            models_committed.send(session.sender, changes=list(d.values()))
            d.clear()
        return EXT_CONTINUE

    def after_rollback(self, session):
        session._model_changes.clear()
        return EXT_CONTINUE


def signalling_mapper(*args, **kwargs):
    """Replacement for mapper that injects some extra extensions"""
    extensions = to_list(kwargs.pop('extension', None), [])
    extensions.append(_SignalTrackingMapperExtension())
    kwargs['extension'] = extensions
    return sqlalchemy.orm.mapper(*args, **kwargs)


class _ModelTableNameDescriptor(object):

    def __get__(self, obj, type):
        tablename = type.__dict__.get('__tablename__')
        if not tablename:
            def _join(match):
                word = match.group()
                if len(word) > 1:
                    return ('_%s_%s' % (word[:-1], word[-1])).lower()
                return '_' + word.lower()
            tablename = _camelcase_re.sub(_join, type.__name__).lstrip('_')
            setattr(type, '__tablename__', tablename)
        return tablename


class _EngineConnector(object):

    def __init__(self, sa, app, bind=None):
        self._sa = sa
        self._app = app
        self._engine = None
        self._connected_for = None
        self._bind = bind
        self._lock = Lock()

    def get_uri(self):
        if self._bind is None:
            return self._app.settings['sqlalchemy_database_uri']
        binds = self._app.settings.get('sqlalchemy_binds') or ()
        assert self._bind in binds, \
            'Bind %r is not specified.  Set it in the SQLALCHEMY_BINDS ' \
            'configuration variable' % self._bind
        return binds[self._bind]

    def get_engine(self):
        with self._lock:
            uri = self.get_uri()
            echo = self._app.settings['sqlalchemy_echo']
            if (uri, echo) == self._connected_for:
                return self._engine
            info = make_url(uri)
            options = {'convert_unicode': True}
            self._sa.apply_pool_defaults(self._app, options)
            self._sa.apply_driver_hacks(self._app, info, options)
            if echo:
                options['echo'] = True
            self._engine = rv = sqlalchemy.create_engine(info, **options)
            self._connected_for = (uri, echo)
            return rv


def get_state(app):
    """Gets the state for the application"""
    assert 'sqlalchemy' in app.extensions, \
        'The sqlalchemy extension was not registered to the current ' \
        'application.  Please make sure to call init_app() first.'
    return app.extensions['sqlalchemy']


class _SQLAlchemyState(object):
    """Remembers configuration for the (db, app) tuple."""

    def __init__(self, db, app):
        self.db = db
        self.app = app
        self.connectors = {}


class Pagination(object):

    def __init__(self, query, page, per_page=20, need_total=True):
        self.query = query
        self.per_page = per_page if per_page > 0 and per_page < 100 else 20
        self.need_total = need_total
        if need_total:
            max_page = (max(0, self.total - 1) // per_page + 1)
            self.page = max_page if page > max_page else page
        else:
            self.page = page if page > 1 else 1

    @property
    def items(self):
        return self.query.offset((self.page - 1) * self.per_page).limit(self.per_page).all()

    @property
    def total(self):
        if self.need_total:
            return self.query.count()

    def iter_pages(self, left_edge=1, left_current=1,
                   right_current=2, right_edge=1):
        if not self.need_total:
            yield None
        last = 0
        for num in range(1, self.pages + 1):
            if num <= left_edge or \
               (num > self.page - left_current - 1 and
                num < self.page + right_current) or \
               num > self.pages - right_edge:
                if last + 1 != num:
                    yield None
                yield num
                last = num

    @property
    def has_prev(self):
        return self.page > 1

    @property
    def prev_num(self):
        return self.page - 1

    @property
    def next_num(self):
        return self.page + 1

    @property
    def has_next(self):
        if self.total:
            return self.page < self.pages
        else:
            return self.per_page == len(self.items)

    @property
    def pages(self):
        if self.total:
            return max(0, self.total - 1) // self.per_page + 1


class BaseQuery(orm.Query):
    """The default query object used for models.  This can be subclassed and
    replaced for individual models by setting the :attr:`~Model.query_class`
    attribute.  This is a subclass of a standard SQLAlchemy
    :class:`~sqlalchemy.orm.query.Query` class and has all the methods of a
    standard query as well.
    """

    def get_or_404(self, ident):
        """Like :meth:`get` but aborts with 404 if not found instead of
        returning `None`.
        """
        rv = self.get(ident)
        if rv is None:
            raise tornado.web.HTTPError(404)
        return rv

    def first_or_404(self):
        """Like :meth:`first` but aborts with 404 if not found instead of
        returning `None`.
        """
        rv = self.first()
        if rv is None:
            raise tornado.web.HTTPError(404)
        return rv

    def paginate(self, page, per_page=20, need_total=True):
        """Returns `per_page` items from page `page`.
        Returns an :class:`Pagination` object.
        """
        return Pagination(self, page, per_page, need_total)


class Model(object):
    """Baseclass for custom user models."""

    #: the query class used.  The :attr:`query` attribute is an instance
    #: of this class.  By default a :class:`BaseQuery` is used.
    query_class = BaseQuery

    #: an instance of :attr:`query_class`.  Can be used to query the
    #: database for instances of this model.
    query = None

    PER_PAGE = None


class SQLAlchemy(object):
    """
    Example:
        db = SQLAlchemy(app=app1)

        class User(db.Model):
            username = db.Column(db.String(16), unique=True, nullable=False, index=True)
            password = db.Column(db.String(30), nullable=False)
            email = db.Column(db.String(30), nullable=False)

        >>> user1 = User.query.filter(User.username=='name').first()
        >>> user2 = User.query.get(1)
        >>> user_list = User.query.filter(db.and_(User.username=='test1', User.email.ilike('%@gmail.com'))).limit(10)

    """

    def __init__(self, app=None, use_native_unicode=True, session_extensions=None, session_options=None):
        # create signals sender
        self.sender = str(uuid.uuid4())
        self.use_native_unicode = use_native_unicode

        self.session_extensions = to_list(session_extensions, []) + \
            [_SignallingSessionExtension()]
        self.session = self.create_scoped_session(session_options)
        self.Model = self.make_declarative_base()
        self._engine_lock = Lock()
        #self.engine = sqlalchemy.create_engine(engine_url, echo=echo, pool_recycle=pool_recycle, pool_size=pool_size)

        if app is not None:
            self.app = app
            self.init_app(app)
        else:
            self.app = None

        _include_sqlalchemy(self)
        self.Query = BaseQuery

    @property
    def engine(self):
        """Gives access to the engine.  If the database configuration is bound
        to a specific application (initialized with an application) this will
        always return a database connection.  If however the current application
        is used this might raise a :exc:`RuntimeError` if no application is
        active at the moment.
        """
        return self.get_engine(self.get_app())

    def make_connector(self, app, bind=None):
        """Creates the connector for a given state and bind."""
        return _EngineConnector(self, app, bind)

    def get_engine(self, app, bind=None):
        """Returns a specific engine.
        """
        with self._engine_lock:
            state = get_state(app)
            connector = state.connectors.get(bind)
            if connector is None:
                connector = self.make_connector(app, bind)
                state.connectors[bind] = connector
            return connector.get_engine()

    def get_app(self, reference_app=None):
        """Helper method that implements the logic to look up an application.
        """
        if reference_app is not None:
            return reference_app
        if self.app is not None:
            return self.app
        raise RuntimeError('application not registered on db '
                           'instance and no application bound '
                           'to current context')

    def create_scoped_session(self, options=None):
        """Helper factory method that creates a scoped session."""
        if options is None:
            options = {}
        return orm.scoped_session(partial(_SignallingSession, self, **options))

    def make_declarative_base(self):
        """Creates the declarative base."""
        base = declarative_base(cls=Model, name='Model',
                                mapper=signalling_mapper,
                                metaclass=_BoundDeclarativeMeta)
        base.query = _QueryProperty(self)
        return base

    def init_app(self, app):
        """This callback can be used to initialize an application for the
        use with this database setup.  Never use a database in the context
        of an application not initialized that way or connections will
        leak.
        """
        app.settings.setdefault('sqlalchemy_database_uri', 'sqlite://')
        app.settings.setdefault('sqlalchemy_binds', None)
        app.settings.setdefault('sqlalchemy_native_unicode', None)
        app.settings.setdefault('sqlalchemy_echo', False)
        app.settings.setdefault('sqlalchemy_record_queries', None)
        app.settings.setdefault('sqlalchemy_pool_size', None)
        app.settings.setdefault('sqlalchemy_pool_timeout', None)
        app.settings.setdefault('sqlalchemy_pool_recycle', None)
        app.settings.setdefault('sqlalchemy_max_overflow', None)
        app.settings.setdefault('sqlalchemy_commit_on_teardown', False)

        if not hasattr(app, 'extensions'):
            app.extensions = {}
        app.extensions['sqlalchemy'] = _SQLAlchemyState(self, app)
        self.app = app

    def apply_pool_defaults(self, app, options):
        def _setdefault(optionkey, configkey):
            value = app.settings[configkey]
            if value is not None:
                options[optionkey] = value
        _setdefault('pool_size', 'sqlalchemy_pool_size')
        _setdefault('pool_timeout', 'sqlalchemy_pool_timeout')
        _setdefault('pool_recycle', 'sqlalchemy_pool_recycle')
        _setdefault('max_overflow', 'sqlalchemy_max_overflow')

    def apply_driver_hacks(self, app, info, options):
        """This method is called before engine creation and used to inject
        driver specific hacks into the options.  The `options` parameter is
        a dictionary of keyword arguments that will then be used to call
        the :func:`sqlalchemy.create_engine` function.

        The default implementation provides some saner defaults for things
        like pool sizes for MySQL and sqlite.  Also it injects the setting of
        `SQLALCHEMY_NATIVE_UNICODE`.
        """
        if info.drivername.startswith('mysql'):
            info.query.setdefault('charset', 'utf8')
            if info.drivername != 'mysql+gaerdbms':
                options.setdefault('pool_size', 10)
                options.setdefault('pool_recycle', 7200)
        elif info.drivername == 'sqlite':
            pool_size = options.get('pool_size')
            detected_in_memory = False
            # we go to memory and the pool size was explicitly set to 0
            # which is fail.  Let the user know that
            if info.database in (None, '', ':memory:'):
                detected_in_memory = True
                if pool_size == 0:
                    raise RuntimeError('SQLite in memory database with an '
                                       'empty queue not possible due to data '
                                       'loss.')
            # if pool size is None or explicitly set to 0 we assume the
            # user did not want a queue for this sqlite connection and
            # hook in the null pool.
            elif not pool_size:
                from sqlalchemy.pool import NullPool
                options['poolclass'] = NullPool

            # if it's not an in memory database we make the path absolute.
            if not detected_in_memory:
                info.database = os.path.join(app.root_path, info.database)

        unu = app.settings['sqlalchemy_native_unicode']
        if unu is None:
            unu = self.use_native_unicode
        if not unu:
            options['use_native_unicode'] = False

    def create_all(self):
        """Creates all tables."""
        self.Model.metadata.create_all(bind=self.engine)

    def drop_all(self):
        """Drops all tables."""
        self.Model.metadata.drop_all(bind=self.engine)
