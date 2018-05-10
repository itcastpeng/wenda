#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author:zhangcong
# Email:zc_92@sina.com


from django.shortcuts import render, HttpResponse, redirect, reverse
from webadmin.views_dir import pub

from webadmin import models
from django.http import JsonResponse
from django.db import connection

from webadmin.forms import user
import json

from django.db.models import F
from django.db.models import Q
from webadmin.views_dir.wenda.message import AddMessage
from django.db.models import Count
import os
import time
from wenda_celery_project import tasks
import datetime


# 覆盖报表
@pub.is_login
def zhidaohuida(request):
    role_id = request.session.get("role_id")
    user_id = request.session.get("user_id")

    # 客户
    filter_dict = {}
    if role_id == 5:
        filter_dict["keywords__client_user"] = user_id

    if "type" in request.GET and request.GET["type"] == "ajax_json":
        length = int(request.GET.get("length"))
        start = int(request.GET.get("start"))

        # 排序
        """
        index, obj.keywords.client_user.username, keyword, obj.get_page_type_display(),
                    obj.rank, create_date, oper
        """
        column_list = ["index", "id", "create_date", "title", "content", "status", "update_date", "oper"]
        order_column = request.GET.get('order[0][column]', 1)  # 第几列排序
        order = request.GET.get('order[0][dir]')  # 正序还是倒序
        order_column = column_list[int(order_column)]
        if order == "desc":
            order_column = "-{order_column}".format(order_column=order_column)
        else:
            order_column = order_column

        q = Q()
        for index, field in enumerate(column_list):
            if field in request.GET and request.GET.get(field):  # 如果该字段存在并且不为空
                if field == "create_date":
                    q.add(Q(**{field + "__contains": request.GET[field]}), Q.AND)
                else:
                    q.add(Q(**{field: request.GET[field]}), Q.AND)

        objs = models.ZhidaoWenda.objects.filter(
            status=1
        ).filter(q).order_by(order_column)
        print(objs)

        result_data = {
            "recordsFiltered": objs.count(),
            "recordsTotal": objs.count(),
            "data": []
        }

        status_choices = models.UserProfile.status_choices

        for index, obj in enumerate(objs[start: (start + length)], start=1):
            # 创建时间
            if obj.create_date:
                create_date = obj.create_date.strftime("%Y-%m-%d %H:%M:%S")
            else:
                create_date = ""

            # 更新时间
            if obj.update_date:
                update_date = obj.update_date.strftime("%Y-%m-%d %H:%M:%S")
            else:
                update_date = ""

            content = """
                <textarea class="form-control" id="textareaDefault" rows="3" style="width: 95%"></textarea>
            """

            baocun = """
                <button type="button" ttype="save" tid="{tid}" class="btn btn-block btn-primary btn-sm">保存</button>
                <button type="button" ttype="delete" tid="{tid}" class="btn btn-block btn-danger btn-sm">删除</button>
            """.format(tid=obj.id)

            oper = """
                <a href='https://www.baidu.com/s?ie=utf-8&wd={title}' target='_blank'>百度</a>
                / <a href='https://www.so.com/s?ie=utf-8&q={title}' target='_blank'>360</a>
                / <a href='https://www.sogou.com/web?ie=utf8&query={title}' target='_blank'>搜狗</a>
            """.format(
                title=obj.title,
                tid=obj.id
            )

            # ["index", "id", "create_date", "title", "content", "update_date", "oper"]
            result_data["data"].append([
                index, obj.id, create_date, obj.title, content, baocun, update_date, oper
            ])
        return HttpResponse(json.dumps(result_data))

    status_choices = models.ZhidaoWenda.status_choices
    if "_pjax" in request.GET:
        return render(request, 'wenda/zhidaohuida/zhidaohuida_pjax.html', locals())
    return render(request, 'wenda/zhidaohuida/zhidaohuida.html', locals())


@pub.is_login
def zhidaohuida_oper(request, oper_type, o_id):
    user_id = request.session["user_id"]
    role_id = request.session.get("role_id")
    response = pub.BaseResponse()

    if request.method == "GET":
        # 保存答案
        if oper_type == "save_content":
            content = request.GET.get("content").strip()
            obj = models.ZhidaoWenda.objects.get(id=o_id)

            wenda_robot_task_obj = models.WendaRobotTask.objects.create(
                title=obj.title,
                content=content,
                wenda_url=obj.url,
                release_platform=1,
                wenda_type=1,
                status=2,
                next_date=datetime.datetime.now(),
            )

            obj.content = content
            obj.update_date = datetime.datetime.now()
            obj.status = 2
            obj.run_task = wenda_robot_task_obj
            obj.oper_user = models.UserProfile.objects.get(id=user_id)
            obj.save()

            response.status = True
            response.message = "保存成功"

        # 删除问答
        elif oper_type == "delete":
            models.ZhidaoWenda.objects.filter(id=o_id).delete()
            print(o_id)

            response.status = True
            response.message = "删除成功"

        return JsonResponse(response.__dict__)








