#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author:zhangcong
# Email:zc_92@sina.com


from django.forms import Form
from django.forms import fields

from webadmin import models

from webadmin.views_dir import pub


class EditContentForm(Form):
    client_user_id = fields.CharField(
        error_messages={
            "required": "请选择客户名称！",
        },
    )
    number = fields.IntegerField(
        error_messages={
            "required": "请填写发布数量！",
            "invalid": "发布数量应该为大于0的整数"
        },
    )

    file = fields.CharField(
        error_messages={
            "required": "请上传参考资料！",
        },
    )

    remark = fields.CharField(
        error_messages={
            "required": "请填写任务说明！",
        },
    )

    def clean_number(self):
        number = self.data["number"]
        if number.isdigit() and int(number) > 0:
            return number
        else:
            self.errors["number"] = "编写数量应该为大于0的整数!"

