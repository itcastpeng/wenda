#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author:zhangcong
# Email:zc_92@sina.com


from django.shortcuts import render, HttpResponse
from webadmin.views_dir import pub

from webadmin import models
from django.http import JsonResponse

from webadmin.forms import edit_content
import json

from django.db.models import Q

import os
import time

import datetime
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment
from webadmin.views_dir.wenda.message import AddMessage
from wenda_celery_project import tasks


# 敏感词库
@pub.is_login
def sensitive_word_library(request):

    w_type_choices = models.SensitiveWordLibrary.w_type_choices

    if "type" in request.GET and request.GET["type"] == "ajax_json":
        length = int(request.GET.get("length"))
        start = int(request.GET.get("start"))

        # 排序
        column_list = [
            "id", "w_type", "name", "oper_user__username", "create_date", "oper"
        ]
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
                q.add(Q(**{field: request.GET[field]}), Q.AND)

        objs = models.SensitiveWordLibrary.objects.select_related("oper_user").filter(q).order_by(order_column)

        result_data = {
            "recordsFiltered": objs.count(),
            "recordsTotal": objs.count(),
            "data": []
        }

        for index, obj in enumerate(objs[start: (start + length)], start=1):

            if obj.create_date:
                create_date = obj.create_date.strftime("%Y-%m-%d %H:%M:%S")
            else:
                create_date = ""

            oper = """
                <a class="btn btn-round btn-sm bg-primary" aria-hidden="true" href="update/{obj_id}/" data-toggle="modal" data-target="#exampleFormModal"><i class="icon fa-pencil-square-o"></i>修改</a>
                <a class="btn btn-round btn-sm bg-danger" aria-hidden="true" href="delete/{obj_id}/" data-toggle="modal" data-target="#exampleFormModal"><i class="fa fa-trash-o fa-fw"></i>删除</a>
            """.format(obj_id=obj.id)

            result_data["data"].append(
                [
                    index, obj.get_w_type_display(), obj.name, obj.oper_user.username, create_date, oper
                ]
            )

        return HttpResponse(json.dumps(result_data))

    if "_pjax" in request.GET:
        return render(request, 'wenda/sensitive_word_library/sensitive_word_library_pjax.html', locals())
    return render(request, 'wenda/sensitive_word_library/sensitive_word_library.html', locals())


@pub.is_login
def sensitive_word_library_oper(request, oper_type, o_id):
    user_id = request.session["user_id"]
    response = pub.BaseResponse()

    status_choices = models.EditContentManagement.status_choices

    if request.method == "POST":
        # 添加
        if oper_type == "create":
            names = request.POST.get('names')
            w_type = request.POST.get('w_type')
            if not names:
                response.status = False
                response.message = "请输入敏感词"
            elif not w_type:
                response.status = False
                response.message = "请选择敏感词类型"
            else:
                name_list = set([name.strip() for name in names.strip().split("\n")])
                query = []
                for name in name_list:
                    if name:
                        if models.SensitiveWordLibrary.objects.filter(name=name, w_type=w_type).count() == 0:
                            query.append(
                                models.SensitiveWordLibrary(
                                    name=name,
                                    oper_user_id=user_id,
                                    w_type=w_type
                                )
                            )

                if query:
                    models.SensitiveWordLibrary.objects.bulk_create(query)

                    response.status = True
                    response.message = "添加成功, 新增 {query_length} 个敏感词".format(query_length=len(query))
                else:
                    response.status = False
                    response.message = "添加的敏感词都已经存在"

        # 修改
        elif oper_type == "update":
            name = request.POST.get('name')
            if not name:
                response.status = False
                response.message = "敏感词不能为空"
            else:
                if models.SensitiveWordLibrary.objects.filter(name=name).exclude(id=o_id).count() == 0:
                    obj = models.SensitiveWordLibrary.objects.get(id=o_id)
                    obj.name = name
                    obj.save()
                    response.status = True
                    response.message = "修改成功"
                else:
                    response.status = False
                    response.message = "敏感词已经存在"

        # 删除
        elif oper_type == "delete":
            obj = models.SensitiveWordLibrary.objects.filter(id=o_id).delete()

            response.status = True
            response.message = "删除成功"

        return JsonResponse(response.__dict__)

    else:
        w_type_choices = models.SensitiveWordLibrary.w_type_choices

        # 添加
        if oper_type == "create":
            return render(request, 'wenda/sensitive_word_library/sensitive_word_library_modal_create.html', locals())

        # 修改
        elif oper_type == "update":
            obj = models.SensitiveWordLibrary.objects.get(id=o_id)

            return render(request, 'wenda/sensitive_word_library/sensitive_word_library_modal_update.html', locals())

        # 删除
        elif oper_type == "delete":
            obj = models.SensitiveWordLibrary.objects.get(id=o_id)
            return render(request, 'wenda/sensitive_word_library/sensitive_word_library_modal_delete.html', locals())
