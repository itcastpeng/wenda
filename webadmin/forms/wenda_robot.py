#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author:zhangcong
# Email:zc_92@sina.com


from django.forms import Form
from django.forms import fields


class WendaRobotTaskCreateForm(Form):
    release_platform = fields.CharField(
        error_messages={
            "required": "请选择问答平台！",
        },
    )

    wenda_type = fields.CharField(
        error_messages={
            "required": "请选择问答类型！",
        },
    )

    content = fields.CharField(
        error_messages={
            "required": "答案不能为空！",
        },
    )

    def clean_wenda_type(self):
        wenda_type = self.data['wenda_type']

        if wenda_type == "1":   # 新问答
            title = self.data['title']
            if not title:
                self.errors["wenda_type"] = "问题不能为空!"

        elif wenda_type == "2":     # 老问答
            wenda_url = self.data['wenda_url']
            if not wenda_url:
                self.errors["wenda_type"] = "问答链接不能为空"

        return wenda_type
