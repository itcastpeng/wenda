#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author:zhangcong
# Email:zc_92@sina.com


from django.forms import Form
from django.forms import fields


# 添加和修改都用这一个
class AuthForm(Form):
    name = fields.CharField(
        error_messages={
            "required": "角色名称不能为空！",
        },
    )

    url_path = fields.CharField(
        error_messages={
            "required": "权限url不能为空！",
        },
    )
