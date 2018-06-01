#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author:zhangcong
# Email:zc_92@sina.com

# from django.forms import fields
from django import forms

class OuterAddForm(forms.Form):
    yonghuming = forms.IntegerField(
            required=True,
             error_messages={
            'required': "答案不能为空"
        }
    )

    xiaoshou = forms.IntegerField(
        required=True,
        error_messages={
            "required": "销售不能为空！",
        }
    )

    bianji = forms.IntegerField(
        required=True,
        error_messages={
            "required": "编辑不能为空！",
        }
    )

    daozhang = forms.IntegerField(
        required=True,
        error_messages={
            "required": "实际到账不能为空！",
        }
    )

    fugailiang = forms.IntegerField(
        required=True,
        error_messages={
            "required": "覆盖量不能为空！",
        }
    )

    start_time = forms.DateField(
        required=True,
        error_messages={
            "required": "开始时间不能为空！",
        }
    )

    stop_time = forms.DateField(
        required=True,
        error_messages={
            "required": "结束不能为空！",
        }
    )


class OuterUpdateForm(forms.Form):
    daozhang = forms.IntegerField(
        required=False,
        error_messages={
            "required": "类型错误！",
        }
    )

    fugailiang =forms.IntegerField(
        required=False,
        error_messages={
            "required": "类型错误！",
        }
    )

