#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author:zhangcong
# Email:zc_92@sina.com

# from django.forms import fields
from django import forms

class CreateForm(forms.Form):
    yonghuming = forms.IntegerField(
            required=True,
             error_messages={
            'required': "用户名不能为空"
        }
    )

    # guanjianci_create = forms.CharField(
    #     required=True,
    #     error_messages={
    #         "required": "关键词不能为空！",
    #     }
    # )

    jieping_time = forms.DateField(
        required=True,
        error_messages={
            "required": "截屏日期不能为空！",
        }
    )
