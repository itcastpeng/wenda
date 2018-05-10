#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author:zhangcong
# Email:zc_92@sina.com

from django.conf import settings
from django.core.cache import cache
import json


# 从redis 中读取数据
def read_from_cache(key):
    key = 'wenda_' + key
    value = cache.get(key)
    if value is None:
        data = None
    else:
        data = value
    return data


# 将键值对写入redis
def write_to_cache(key, value):
    key = 'wenda_' + key
    cache.set(key, value, settings.NEVER_REDIS_TIMEOUT)

