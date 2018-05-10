#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author:zhangcong
# Email:zc_92@sina.com


from django.forms import Form
from django.forms import fields


class GlobalSettingsForm(Form):
    new_wenda_money = fields.IntegerField(
        error_messages={
            "required": "第一项不能为空！",
            "invalid": "第一项格式错误,请填写整数格式!",
        },
    )
    old_wenda_money = fields.IntegerField(
        error_messages={
            "required": "第二项不能为空！",
            "invalid": "第二项格式错误,请填写整数格式!",
        },
    )
    xie_wenda_money = fields.IntegerField(
        error_messages={
            "required": "第三项不能为空！",
            "invalid": "第三项格式错误,请填写整数格式!",
        },
    )
    fa_wenda_money = fields.IntegerField(
        error_messages={
            "required": "第四项不能为空！",
            "invalid": "第四项格式错误,请填写整数格式!",
        },
    )

