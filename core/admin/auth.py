# -*- coding: utf-8 -*-

import functools
from tornado.web import urlparse, urlencode, HTTPError


def authenticated(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        if not self.current_user:
            if self.request.method in ("GET", "HEAD"):
                url = self.get_admin_login_url()
                if "?" not in url:
                    if urlparse.urlsplit(url).scheme:
                        next_url = self.request.full_url()
                    else:
                        next_url = self.request.uri
                    url += "?" + urlencode(dict(next=next_url))
                return self.redirect(url)
            raise HTTPError(403)
        return func(self, *args, **kwargs)
    return wrapper
