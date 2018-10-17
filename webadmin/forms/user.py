#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author:zhangcong
# Email:zc_92@sina.com


from django.forms import Form
from django.forms import fields

from webadmin import models

from webadmin.views_dir import pub

class UserProfileCreateForm(Form):
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

    role_id = fields.CharField(
        error_messages={
            "required": "角色不能为空！",
        },
    )

    xiaoshou_id = fields.CharField(
        required=False,
    )

    guwen_id = fields.CharField(
        required=False
    )
    xinlaowenda_status = fields.IntegerField(
        required=False,
    )
    zhidao_hehuoren_website = fields.CharField(
        required=False,
    )

    def clean_username(self):
        username = self.data["username"]
        user_profile_objs = models.UserProfile.objects.filter(username=username, is_delete=False)
        if user_profile_objs:
            self.errors["username"] = "用户名已存在!"
        else:
            return username

    def clean_password(self):
        return pub.str_encrypt(self.data["password"])

    def clean_role_id(self):
        role_id = self.data["role_id"]
        xiaoshou_id = self.data["xiaoshou_id"]
        guwen_id = self.data["guwen_id"]
        if role_id in ["5", "15"]:   # 如果创建的是客户角色
            if not guwen_id:
                self.errors["guwen_id"] = "请选择营销顾问"
            elif not xiaoshou_id:
                self.errors["xiaoshou_id"] = "请选择销售"

            else:
                return self.data["role_id"]
        else:
            return self.data["role_id"]


class UserProfileUpdateForm(Form):
    username = fields.CharField(
        error_messages={
            "required": "用户名不能为空！",
        },
    )
    status = fields.IntegerField(
        error_messages={
            "required": "状态不能为空",
        },
    )

    password = fields.CharField(
        required=False,
    )

    role_id = fields.CharField(
        error_messages={
            "required": "角色不能为空！",
        },
    )

    xiaoshou_id = fields.CharField(
        required=False,
    )

    guwen_id = fields.CharField(
        required=False
    )

    xie_wenda_money = fields.IntegerField(
        required=False,
    )
    fa_wenda_money = fields.CharField(
        required=False,
    )

    map_search_keywords = fields.CharField(
        required=False,
    )
    map_match_keywords = fields.CharField(
        required=False,
    )

    shangwutong_url = fields.CharField(
        required=False,
    )
    xinlaowenda_status = fields.IntegerField(
        required=False,
    )

    def clean_username(self):
        username = self.data["username"]
        o_id = self.data["id"]
        print(username, o_id)
        user_profile_objs = models.UserProfile.objects.filter(username=username, is_delete=False).exclude(id=o_id)
        if user_profile_objs:
            self.errors["username"] = "用户名已存在!"
        else:
            return username

    def clean_password(self):
        if self.data["password"]:
            return pub.str_encrypt(self.data["password"])

    def clean_xie_wenda_money(self):
        xie_wenda_money = self.data["xie_wenda_money"]

        if xie_wenda_money:
            if not xie_wenda_money.isdigit():
                self.errors["xie_wenda_money"] = "写问答收益格式不正确"
            else:
                return xie_wenda_money
        else:
            xie_wenda_money = None
            return xie_wenda_money

    def clean_fa_wenda_money(self):
        fa_wenda_money = self.data["fa_wenda_money"]

        if fa_wenda_money:
            if not fa_wenda_money.isdigit():
                self.errors["fa_wenda_money"] = "发问答收益格式不正确"
            else:
                return fa_wenda_money
        else:
            fa_wenda_money = None
            return fa_wenda_money

    def clean_role_id(self):
        role_id = self.data["role_id"]

        if role_id == "5":  # 如果创建的是客户角色
            xiaoshou_id = self.data["xiaoshou_id"]
            guwen_id = self.data["guwen_id"]

            if not guwen_id:
                self.errors["guwen_id"] = "请选择营销顾问"
            elif not xiaoshou_id:
                self.errors["xiaoshou_id"] = "请选择销售"

            else:
                return self.data["role_id"]
        else:
            return self.data["role_id"]