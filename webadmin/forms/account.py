#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author:zhangcong
# Email:zc_92@sina.com


from django.forms import Form
from django.forms import fields

from webadmin.views_dir import pub


# 登录 Form
class LoginForm(Form):
    username = fields.CharField(
        error_messages={
            "required": "用户名不能为空！",
        },
    )

    password = fields.CharField(
        error_messages={
            "required": "密码不能为空！",
        },
    )

    check_code = fields.CharField(
        error_messages={
            "required": "验证码不能为空！",
        },
    )

    def clean_password(self):
        return pub.str_encrypt(self.data["password"])
