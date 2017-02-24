#!/usr/bin/env python3
# -*- coding:utf-8 -*-


import asyncio
import functools


def run_in_executor(fn):
    @functools.wraps(fn)
    def wrapper(*arg, **kwargs):
        loop = asyncio.get_event_loop()
        return loop.run_in_executor(None, fn, *arg, **kwargs)
    return wrapper
