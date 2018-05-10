#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author:zhangcong
# Email:zc_92@sina.com


from django.forms import Form
from django.forms import fields


class MyTaskCreateForm(Form):
    release_platform = fields.CharField(
        error_messages={
            "required": "发布平台选择异常,请单击上一步选择发布平台！",
        },
    )
    wenda_type = fields.IntegerField(
        error_messages={
            "required": "问答类型选择异常,请单击上一步选择问答类型！",
        },
    )

    num = fields.IntegerField(
        error_messages={
            "required": "发布数量不能为空,请单击上一步填写发布数量！",
            "invalid": "发布数量格式异常,请单击上一步填写发布数量！",
        },
    )

    file_obj = fields.CharField(
        error_messages={
            "required": "请上传任务需求文件",
        },
    )

    def clean_num(self):
        num = self.data.get("num", False)

        if int(num) > 0:
            return num

        else:
            self.errors["num"] = "发布数量必须大于0"

