#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author:zhangcong
# Email:zc_92@sina.com


from django.forms import Form
from django.forms import fields

from webadmin import models

from webadmin.views_dir import pub

class HospitalInformationForm(Form):
    name = fields.CharField(
        error_messages={
            "required": "医院名称不能为空！",
        },
    )
    department_id = fields.CharField(
        error_messages={
            "required": "请选择医院科室！",
        },
    )

    web_site = fields.URLField(
        error_messages={
            "required": "医院官网不能为空！",
            "invalid": "医院官网格式错误!",
        },
    )

    content_direction = fields.CharField(
        required=False,
    )

    content_direction_custom = fields.CharField(
        required=False,
    )

    reply_role = fields.CharField(
        error_messages={
            "required": "请勾选表达人称角色！",
        },
    )

    def clean_content_direction(self):
        content_direction = self.data.get("content_direction", False)
        content_direction_custom = self.data.get("content_direction_custom", False)

        if not content_direction and not content_direction_custom:
            self.errors["content_direction"] = "请选择问答内容方向或者输入其他内容方向"
        else:
            content_direction = ",".join(content_direction)
            return content_direction

    def clean_reply_role(self):
        reply_role = self.data.get("reply_role", False)
        if reply_role:
            reply_role = ",".join(reply_role)
            return reply_role

