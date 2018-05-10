#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author:zhangcong
# Email:zc_92@sina.com


from django import template
register = template.Library()


# 对链接进行切片
@register.simple_tag
def cut_str(string):
    print(string)
    return string[:-9] + "..."
