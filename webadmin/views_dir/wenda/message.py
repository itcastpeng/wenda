#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author:zhangcong
# Email:zc_92@sina.com


from django.shortcuts import render, HttpResponse
from webadmin.views_dir import pub

from webadmin import models
from django.http import JsonResponse

import json

from django.db.models import F
from django.db.models import Q
from datetime import datetime


# 添加消息
def AddMessage(request, to_user_id, content):
    user_id = request.session["user_id"]
    models.Message.objects.create(
        user_id=to_user_id,
        content=content,
        m_user_id=user_id
    )


# 消息管理
@pub.is_login
def message(request):
    user_id = request.session["user_id"]
    # 显示数据的时候区分管理员用户和普通用户

    status_choices = models.Message.status_choices

    if "type" in request.GET and request.GET["type"] == "ajax_json":
        length = int(request.GET.get("length"))
        start = int(request.GET.get("start"))

        message_objs = models.Message.objects.select_related('m_user').filter(user_id=user_id)
        column_list = ['id', 'content', 'status', 'create_at', 'update_at', 'create_user']

        order_column = request.GET.get('order[0][column]')  # 第几列排序
        order = request.GET.get('order[0][dir]')  # 正序还是倒序
        order_column = column_list[int(order_column)]
        if order == "desc":
            order_column = "-{order_column}".format(order_column=order_column)
        else:
            order_column = order_column
        q = Q()
        for index, field in enumerate(column_list):
            if field in request.GET and request.GET[field]:     # 如果该字段存在并且不为空
                q.add(Q(**{field + "__contains": request.GET[field]}), Q.AND)

        message_objs = message_objs.filter(q).order_by(order_column)

        # ##### 排序加搜索 ##### ↑↑↑↑↑↑↑↑↑↑↑

        result_data = {
            "recordsFiltered": message_objs.count(),
            "data": []
        }

        for index, obj in enumerate(message_objs[start: (start + length)], start=1):

            delete_input_html = "<input type='checkbox' message_id='{message_id}' />".format(message_id=obj.id)

            if obj.create_at:
                create_date = obj.create_at.strftime("%y-%m-%d %H:%M:%S")
            else:
                create_date = ""

            if obj.update_at:
                update_at = obj.update_at.strftime("%y-%m-%d %H:%M:%S")
            else:
                update_at = ""

            status = ""
            for i in status_choices:
                if i[0] == obj.status:
                    status = i[1]
                    break

            if obj.status == 1:
                oper = """
                    <a class="btn btn-round btn-sm bg-primary" aria-hidden="true" href="read/{obj_id}/" data-toggle="modal" data-target="#exampleFormModal"><i class="icon fa-pencil-square-o"></i>设置已读</a>
                """.format(obj_id=obj.id)
            else:
                oper = ""

            table_data = [delete_input_html, index, obj.content, status, create_date, update_at, obj.m_user.username, oper]

            result_data["data"].append(table_data)

        return HttpResponse(json.dumps(result_data))

    if "_pjax" in request.GET:
        return render(request, 'wenda/message/message_pjax.html', locals())
    return render(request, 'wenda/message/message.html', locals())


@pub.is_login
def message_oper(request, oper_type, o_id):
    user_id = request.session["user_id"]
    response = pub.BaseResponse()

    if request.method == "POST":

        # 设置消息为已读状态
        if oper_type == "read":
            response.status = True
            response.message = "修改成功"

            models.Message.objects.filter(id=o_id).update(
                status=2,
                update_at=datetime.now()
            )

        # 批量设置消息为已读状态
        if oper_type == "batch_read":
            response.status = True
            response.message = "修改成功"

            batch_read_ids = request.POST.get('batch_read_ids')

            if len(batch_read_ids.split(',')):
                print(batch_read_ids.split(','))

                batch_read_ids = [int(i) for i in batch_read_ids.split(',')]
                models.Message.objects.filter(id__in=batch_read_ids).update(
                    status=2,
                    update_at=datetime.now()
                )
            else:
                response.status = False
                response.message = "未勾选需要修改状态的消息"
        return JsonResponse(response.__dict__)

    else:
        # 设置消息为已读
        if oper_type == "read":
            return render(request, 'wenda/message/message_modal_update.html', locals())

        elif oper_type == "batch_read":
            batch_read_ids = request.GET.get('batch_read_ids')
            print(batch_read_ids)
            return render(request, 'wenda/message/message_modal_batch_read.html', locals())