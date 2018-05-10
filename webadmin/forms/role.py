#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author:zhangcong
# Email:zc_92@sina.com


from django.forms import Form
from django.forms import fields


# 添加和修改都用这一个
class RoleForm(Form):
    name = fields.CharField(
        error_messages={
            "required": "角色名称不能为空！",
        },
    )
    access_rules = fields.CharField(
        error_messages={
            "required": "请为权限勾选权限！",
        },
    )