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
import os
import xlrd

from webadmin.views_dir.wenda.message import AddMessage


@pub.is_login
def wait_clearing(request):
    user_id = request.session["user_id"]
    role_id = models.UserProfile.objects.get(id=user_id).role_id

    release_platform_choices = models.Task.release_platform_choices
    type_choices = models.Task.type_choices
    clearing_choices = models.Task.clearing_choices

    if "type" in request.GET and request.GET["type"] == "ajax_json":

        length = int(request.GET.get("length"))
        start = int(request.GET.get("start"))

        # 排序
        column_list = ["id", "name", "release_platform", "wenda_type", "num", "clearing", "task_demand_excel", "task_result_excel", "publish_task_result_excel", "create_date", "complete_date", "oper"]
        order_column = request.GET.get('order[0][column]', 1)  # 第几列排序
        order = request.GET.get('order[0][dir]', "asc")  # 正序还是倒序
        order_column = column_list[int(order_column)]
        if order == "desc":
            order_column = "-{order_column}".format(order_column=order_column)
        else:
            order_column = order_column

        q = Q()
        for index, field in enumerate(column_list):
            if field in request.GET and request.GET.get(field):  # 如果该字段存在并且不为空
                if field in ["release_platform", "clearing", "wenda_type"]:

                    q.add(Q(**{field: request.GET[field]}), Q.AND)

                else:
                    q.add(Q(**{field + "__contains": request.GET[field]}), Q.AND)

        task_objs = models.Task.objects.filter(status=10).filter(q).order_by(order_column)

        result_data = {
            "recordsFiltered": task_objs.count(),
            "recordsTotal": task_objs.count(),
            "data": []
        }

        for index, obj in enumerate(task_objs[start: (start + length)], start=1):

            # 创建时间
            if obj.create_date:
                create_date = obj.create_date.strftime("%Y-%m-%d %H:%M:%S")
            else:
                create_date = ""

            # 编辑完成时间
            if obj.complete_date:
                complete_date = obj.create_date.strftime("%Y-%m-%d %H:%M:%S")
            else:
                complete_date = ""

            # 结算状态
            clearing = ""
            for i in clearing_choices:
                if i[0] == obj.clearing:
                    clearing = i[1]
                    break

            # 发布平台
            release_platform = ""
            for i in release_platform_choices:
                if i[0] == obj.release_platform:
                    release_platform = i[1]
                    break

            # 问答类型
            wenda_type = ""
            for i in type_choices:
                if i[0] == obj.wenda_type:
                    wenda_type = i[1]
                    break

            # 任务需求表格
            task_demand_excel = "<a href='/{task_demand_file_path}' download='{task_demand_file_path_name}'>下载</a> / <a href='online_preview_task_demand/{obj_id}/' data-toggle='modal' data-target='#exampleFormModal'>在线预览</a> ".format(
                task_demand_file_path=obj.task_demand_file_path,
                task_demand_file_path_name=obj.task_demand_file_path.split('/')[-1],
                obj_id=obj.id
            )

            # 任务结果表格
            task_result_excel = ""
            if obj.task_result_file_path:
                task_result_excel = "<a href='/{task_result_file_path}' download='{task_result_file_path_name}'>下载</a> / <a href='online_preview_task_result/{obj_id}/' data-toggle='modal' data-target='#exampleFormModal'>在线预览</a>".format(
                    task_result_file_path=obj.task_result_file_path,
                    task_result_file_path_name=obj.task_result_file_path.split('/')[-1],
                    obj_id=obj.id
                )

            # 发问答结果表格
            publish_task_result_excel = ""
            if obj.publish_task_result_file_path:
                publish_task_result_excel = "<a href='/{task_result_file_path}' download='{task_result_file_path_name}'>下载</a> / <a href='online_preview_publish_task_result/{obj_id}/' data-toggle='modal' data-target='#exampleFormModal'>在线预览</a>".format(
                    task_result_file_path=obj.publish_task_result_file_path,
                    task_result_file_path_name=obj.publish_task_result_file_path.split('/')[-1],
                    obj_id=obj.id
                )

            oper = ""
            if obj.clearing == 1:
                oper += """
                    <a class="btn btn-round btn-sm bg-success" aria-hidden="true" href="clearing/{obj_id}/" data-toggle="modal" data-target="#exampleFormModal"><i class="icon fa-dollar" aria-hidden="true"></i>结算</a>
                """.format(obj_id=obj.id)

            result_data["data"].append(
                [index, obj.name, release_platform, wenda_type, obj.num, clearing, task_demand_excel, task_result_excel, publish_task_result_excel, create_date, complete_date, oper])

        return HttpResponse(json.dumps(result_data))

    if "_pjax" in request.GET:
        return render(request, 'wenda/wait_clearing/wait_clearing_pjax.html', locals())
    return render(request, 'wenda/wait_clearing/wait_clearing.html', locals())


@pub.is_login
def wait_clearing_oper(request, oper_type, o_id):
    user_id = request.session["user_id"]
    response = pub.BaseResponse()

    if request.method == "POST":

        # 结算
        if oper_type == "clearing":

            publish_ok_num = request.POST["publish_ok_num"]

            if publish_ok_num.isdigit() and int(publish_ok_num) > 0:

                publish_ok_num = int(publish_ok_num)

                task_obj = models.Task.objects.get(id=o_id)
                global_settings_obj = models.GlobalSettings.objects.all()[0]

                receive_user_username = task_obj.receive_user.username      # 写问答的人
                publish_user_username = task_obj.publish_user.username      # 发问答的人

                # 给写问答的人结算
                if task_obj.receive_user.xie_wenda_money:
                    money = task_obj.receive_user.xie_wenda_money * publish_ok_num
                else:
                    money = global_settings_obj.xie_wenda_money * publish_ok_num

                user_profile_obj = models.UserProfile.objects.get(id=task_obj.receive_user.id)
                user_profile_obj.balance += money
                user_profile_obj.save()

                models.BalanceDetail.objects.create(
                    user_id=task_obj.receive_user.id,
                    account_type=3,
                    money=money,
                    oper_user_id=user_id,
                    remark="编写问答收益"
                )

                message = "编写问答任务 [{task_name}] 已经结算成功, 请注意查看".format(
                    task_name=task_obj.name,
                )
                AddMessage(request, task_obj.receive_user.id, message)

                # 给写问答的人结算
                if task_obj.publish_user.xie_wenda_money:
                    money = task_obj.publish_user.xie_wenda_money * publish_ok_num
                else:
                    money = global_settings_obj.fa_wenda_money * publish_ok_num

                user_profile_obj = models.UserProfile.objects.get(id=task_obj.publish_user.id)
                user_profile_obj.balance += money
                user_profile_obj.save()

                models.BalanceDetail.objects.create(
                    user_id=task_obj.publish_user.id,
                    account_type=3,
                    money=money,
                    oper_user_id=user_id,
                    remark="发布问答收益"
                )

                message = "发布问答任务 [{task_name}] 已经结算成功, 请注意查看".format(
                    task_name=task_obj.name,
                )

                AddMessage(request, task_obj.publish_user.id, message)

                task_obj.clearing = 2
                task_obj.publish_ok_num = publish_ok_num
                task_obj.save()

                response.status = True
                response.message = "结算成功"

            else:
                response.status = False
                response.message = "成功数量有误"

        return JsonResponse(response.__dict__)

    else:
        # 结算
        if oper_type == "clearing":
            task_obj = models.Task.objects.get(id=o_id)
            return render(request, 'wenda/wait_clearing/wait_clearing_modal_clearing.html', locals())

        # 在线预览任务需求
        elif oper_type == "online_preview_task_demand":
            task_obj = models.Task.objects.get(id=o_id)

            file_name_path = os.path.join(os.getcwd(), task_obj.task_demand_file_path)
            print(file_name_path)

            book = xlrd.open_workbook(file_name_path)
            sh = book.sheet_by_index(0)

            table_data = []

            for row in range(2, sh.nrows):

                line_data = []
                for col in range(sh.ncols):
                    value = sh.cell_value(rowx=row, colx=col)
                    line_data.append(value)

                table_data.append(line_data)
            print(table_data)
            return render(request, "wenda/my_task/my_task_modal_online_preview.html", locals())

        # 在线预览任务结果
        elif oper_type == "online_preview_task_result":
            task_obj = models.Task.objects.get(id=o_id)

            file_name_path = os.path.join(os.getcwd(), task_obj.task_result_file_path)
            print(file_name_path)

            book = xlrd.open_workbook(file_name_path)
            sh = book.sheet_by_index(0)

            table_data = []

            for row in range(2, sh.nrows):

                line_data = []
                for col in range(sh.ncols):
                    value = sh.cell_value(rowx=row, colx=col)
                    line_data.append(value)

                table_data.append(line_data)
            print(table_data)
            return render(request, "wenda/my_task/my_task_modal_online_preview.html", locals())

        # 在线预览任务结果
        elif oper_type == "online_preview_publish_task_result":
            task_obj = models.Task.objects.get(id=o_id)

            file_name_path = os.path.join(os.getcwd(), task_obj.publish_task_result_file_path)
            print(file_name_path)

            book = xlrd.open_workbook(file_name_path)
            sh = book.sheet_by_index(0)

            table_data = []

            for row in range(2, sh.nrows):

                line_data = []
                for col in range(sh.ncols):
                    value = sh.cell_value(rowx=row, colx=col)

                    if (task_obj.wenda_type == 1 and col == 2) or (task_obj.wenda_type == 2 and col == 1):  # 新问答
                        value = "<a href='{value}'>查看链接</a>".format(value=value)

                    line_data.append(value)

                table_data.append(line_data)
            print(table_data)
            return render(request, "wenda/my_task/my_task_modal_online_preview.html", locals())

