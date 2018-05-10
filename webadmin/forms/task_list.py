#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author:zhangcong
# Email:zc_92@sina.com


from django.forms import Form
from django.forms import fields

from webadmin import models

from webadmin.views_dir import pub


class OldWendaCreateForm(Form):
    client_id = fields.CharField(
        error_messages={
            "required": "请选择对应用户！",
        },
    )

    bianji_id = fields.CharField(
        error_messages={
            "required": "请选择对应编辑！",
        },
    )

    num = fields.CharField(
        error_messages={
            "required": "请输入编写数量！",
            "invalid": "编写数量格式异常!"
        },
    )

    task_excel_obj = fields.CharField(
        error_messages={
            "required": "请上传任务需求文件",
        },
    )


class TaskListCreateForm(Form):
    keywords = fields.CharField(
        error_messages={
            "required": "关键词不能为空！",
        },
    )
    url = fields.URLField(
        error_messages={
            "required": "网址不能为空！",
            "invalid": "网址格式不正确!"
        },
    )

    def clean_keywords(self):
        keywords = self.data['keywords']
        url = self.data['url']
        user_id = self.data["user_id"]

        if url.startswith("http://"):
            print(url)
            url = url.lstrip("http://")
        elif url.startswith("https://"):
            url = url.lstrip("https://")

        task_objs = models.Task.objects.filter(keywords=keywords, url=url, user_id=user_id)

        if task_objs:
            self.errors["keywords"] = "关键词和url 已经存在"
        else:
            return keywords

    def clean_url(self):
        url = self.data['url']
        if url.startswith("http://"):
            print(url)
            url = url.lstrip("http://")
        elif url.startswith("https://"):
            url = url.lstrip("https://")

        return url

    # day_click_number = fields.IntegerField(
    #     error_messages={
    #         "required": "日点击次数不能为空！",
    #         "invalid": "日点击次数只能为整数!",
    #     },
    # )
    #
    # search_engine = fields.CharField(
    #     error_messages={
    #         "required": "搜索引擎不能为空！",
    #     },
    # )
    #
    # click_strategy_id = fields.CharField(
    #     error_messages={
    #         "required": "点击策略不能为空！",
    #     },
    # )


class TaskListUpdateForm(Form):
    keywords = fields.CharField(
        error_messages={
            "required": "关键词不能为空！",
        },
    )
    url = fields.URLField(
        error_messages={
            "required": "网址不能为空！",
            "invalid": "网址格式不正确!"
        },
    )

    day_click_number = fields.IntegerField(
        error_messages={
            "required": "日点击次数不能为空！",
            "invalid": "日点击次数只能为整数!",
        },
    )

    search_engine = fields.CharField(
        error_messages={
            "required": "搜索引擎不能为空！",
        },
    )

    click_strategy_id = fields.CharField(
        error_messages={
            "required": "点击策略不能为空！",
        },
    )


# 任务批量审核
class TaskListAuditForm(Form):

    day_click_number = fields.IntegerField(
        error_messages={
            "required": "日点击次数不能为空！",
            "invalid": "日点击次数只能为整数!",
        },
    )

    search_engine = fields.CharField(
        error_messages={
            "required": "搜索引擎不能为空！",
        },
    )

    click_strategy_id = fields.CharField(
        error_messages={
            "required": "点击策略不能为空！",
        },
    )
    batch_audit_ids = fields.CharField(
        error_messages={
            "required": "未勾选需要审核的任务！",
        },
    )