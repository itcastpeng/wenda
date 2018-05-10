#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author:zhangcong
# Email:zc_92@sina.com


from django.shortcuts import render, HttpResponse
from webadmin.views_dir import pub

from webadmin import models
from django.http import JsonResponse

import json

from django.db.models import Q
from django.db.models import Count

from webadmin.forms.wenda_robot import WendaRobotTaskCreateForm
from openpyxl import Workbook
import time
import os
import datetime

from wenda_celery_project import tasks


# 问答机器人
@pub.is_login
def wenda_robot(request):
    user_id = request.session["user_id"]
    role_id = models.UserProfile.objects.get(id=user_id).role_id

    status_choices = models.WendaRobotTask.status_choices
    wenda_type_choices = models.WendaRobotTask.wenda_type_choices
    release_platform_choices = models.WendaRobotTask.release_platform_choices

    tasks_objs = models.WendaRobotTask.objects.values("task_id", "task__name").distinct()

    if "type" in request.GET and request.GET["type"] == "ajax_json":

        length = int(request.GET.get("length"))
        start = int(request.GET.get("start"))

        # 排序
        column_list = ["id", "task__release_user_id", "task_id", "title", "content", "add_map", "wenda_type", "status", "create_date", "update_date", "next_date" "oper", "task__release_user_id", "task__is_test"]
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
                print('field -->', field)
                if field == "task__is_test":
                    print('--> task__is_test')
                    if request.GET.get(field) == "1":   # 正式任务
                        q.add(Q(**{"task__is_test": False}), Q.AND)
                    else:
                        q.add(Q(**{"task__is_test": True}), Q.AND)
                else:
                    q.add(Q(**{field: request.GET[field]}), Q.AND)
                # if field in ["webda_type", "status", "phone_area", "phone_type"]:
                #
                # else:
                #     q.add(Q(**{field + "__contains": request.GET[field]}), Q.AND)

        task_objs = models.WendaRobotTask.objects.select_related('task__release_user', 'task').filter(q).order_by(order_column)

        print(task_objs.query)

        result_data = {
            "recordsFiltered": task_objs.count(),
            "recordsTotal": task_objs.count(),
            "data": []
        }
        x = task_objs[start: (start + length)]
        print(x.query)
        for index, obj in enumerate(task_objs[start: (start + length)], start=1):

            content = obj.content
            # if obj.wenda_url and obj.status > 1:
            #     title = "<a href='{url}' target='_blank'>{title}</a>".format(url=obj.wenda_url, title=obj.title)

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

            # 更新时间
            if obj.next_date:
                next_date = obj.next_date.strftime("%Y-%m-%d %H:%M:%S")
            else:
                next_date = ""

            # 状态
            status = ""
            for i in status_choices:
                if i[0] == obj.status:
                    status = i[1]
                    break

            # 问答类型
            wenda_type = ""
            for i in wenda_type_choices:

                if i[0] == obj.wenda_type:
                    wenda_type = i[1]
                    break

            # phone_number = ""
            # robot_account_log_objs = obj.robotaccountlog_set.all()
            # if robot_account_log_objs:
            #     phone_number = robot_account_log_objs.filter(status=1).last().phone_num

            oper = ""

            if obj.status <= 2 and obj.add_map == 2 and obj.next_date > (datetime.datetime.now() - datetime.timedelta(minutes=10)):
                oper += """
                    <a class="btn btn-round btn-sm bg-success" aria-hidden="true" href="add_map/{tid}/" data-toggle="modal" data-target="#exampleFormModal">
                        <i class="icon fa-map-marker" aria-hidden="true"></i> 添加地图
                    </a>
                """.format(tid=obj.id)

            if obj.task:
                username = obj.task.release_user.username
                task_name = obj.task.name
            else:
                username = "养账号任务"
                task_name = "养账号任务"

            title = obj.title
            if obj.wenda_type == 2:
                title = "<a href='{href}' target='_blank'>{title}</a>".format(title=title, href=obj.wenda_url)
            obj_data = [index, username, task_name, title, content, obj.get_add_map_display(), wenda_type, status, create_date, update_date, next_date, oper]

            result_data["data"].append(obj_data)

        return HttpResponse(json.dumps(result_data))

    user_data = models.WendaRobotTask.objects.filter(task__release_user__is_delete=False).values(
        "task__release_user__username",
        "task__release_user_id"
    ).annotate(Count("id"))
    print(user_data)

    if "_pjax" in request.GET:
        return render(request, 'wenda/wenda_robot/wenda_robot_pjax.html', locals())
    return render(request, 'wenda/wenda_robot/wenda_robot.html', locals())


@pub.is_login
def wenda_robot_oper(request, oper_type, o_id):
    user_id = request.session["user_id"]
    response = pub.BaseResponse()

    if request.method == "POST":

        if oper_type == "create":
            print("xxx")
            form_obj = WendaRobotTaskCreateForm(request.POST)

            if form_obj.is_valid():

                release_platform = form_obj.cleaned_data["release_platform"]
                wenda_type = form_obj.cleaned_data["wenda_type"]
                content = form_obj.cleaned_data["content"]

                create_data = {
                    "release_platform": release_platform,
                    "wenda_type": wenda_type,
                    "content": content,
                    "user_id": user_id,
                }
                print('create_data  -- > ',create_data)

                if wenda_type == "1":
                    title = request.POST["title"]
                    create_data["title"] = title
                elif wenda_type == "2":
                    wenda_url = request.POST["wenda_url"]
                    create_data["wenda_url"] = wenda_url
                    create_data["status"] = 2

                models.WendaRobotTask.objects.create(**create_data)

                response.status = True
                response.message = "添加成功"

            else:
                pass

        elif oper_type == "download":
            print(request.POST)

            task_id = request.POST.get("task_id")
            print(task_id)
            if not task_id:
                response.status = False
                response.message = "请选择任务名称"
            else:
                wenda_robot_task_objs = models.WendaRobotTask.objects.filter(task_id=task_id).order_by('status')

                status_choices = models.WendaRobotTask.status_choices

                file_name = os.path.join("statics", "upload_files", str(int(time.time() * 1000)) + ".xlsx")

                wenda_robot_task_list = []
                for obj in wenda_robot_task_objs:
                    wenda_robot_task_list.append({
                        "status": obj.status,
                        "wenda_url": obj.wenda_url,
                        "title": obj.title,
                        "content": obj.content,
                    })

                tasks.WendaRobotWriteExcel.delay(file_name, wenda_robot_task_list, status_choices)

                response.status = True
                response.message = "导出成功"
                response.download_url = "/" + file_name

        elif oper_type == "add_map":
            obj = models.WendaRobotTask.objects.get(id=o_id)
            obj.add_map = 1
            obj.save()

            response.status = True
            response.message = "添加地图成功"

        return JsonResponse(response.__dict__)

    else:
        # 添加
        if oper_type == "create":
            release_platform_choices = models.WendaRobotTask.release_platform_choices
            wenda_type_choices = models.WendaRobotTask.wenda_type_choices

            return render(request, "wenda/wenda_robot/wenda_robot_modal_create.html", locals())

        # 导出
        elif oper_type == "download":

            wenda_type_choices = models.WendaRobotTask.wenda_type_choices
            task_names = models.WendaRobotTask.objects.values("task_id", "task__name").distinct()

            return render(request, "wenda/wenda_robot/wenda_robot_modal_download.html", locals())

        elif oper_type == "add_map":
            obj = models.WendaRobotTask.objects.get(id=o_id)

            # 判断是否填写地图搜索关键词和地图匹配关键词
            if obj.task.release_user.map_search_keywords and obj.task.release_user.map_match_keywords:
                map_flag = True
            else:
                map_flag = False

            return render(request, "wenda/wenda_robot/wenda_robot_modal_add_map.html", locals())
