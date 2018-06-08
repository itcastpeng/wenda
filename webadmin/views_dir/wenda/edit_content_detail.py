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

from django.db.models import F
from django.db.models import Q
from django.db.models import Count
from webadmin.views_dir.wenda.message import AddMessage
import datetime

import os
import time
from wenda_celery_project import tasks


# 编辑内容详情
@pub.is_login
def edit_content_detail(request):
    print('进入任务内容 ====================================== ')
    user_id = request.session.get('user_id')
    role_id = request.session.get('role_id')
    print("role_id -->", role_id)
    guanli_role_list = [1, 4, 7]  # 超级管理员、管理员、营销顾问角色id

    role_names = models.Role.objects.values_list("id", "name")

    status_choices = models.EditPublickTaskManagement.status_choices

    if "type" in request.GET and request.GET["type"] == "ajax_json":
        length = int(request.GET.get("length"))
        start = int(request.GET.get("start"))

        # 排序
        column_list = [
            "id", "task_id", "status", "title", "content",
            "submit_num", "update_date", "oper", "task__task__client_user_id"
        ]
        order_column = request.GET.get('order[0][column]', 1)  # 第几列排序
        order = request.GET.get('order[0][dir]')  # 正序还是倒序
        order_column = column_list[int(order_column)]
        if order == "desc":
            order_column = "-{order_column}".format(order_column=order_column)
        else:
            order_column = order_column

        q = Q()
        status = request.GET.get("status", "default")
        print(status)
        if status == "default" and role_id != 14:
            q.add(Q(**{"status": 2}), Q.AND)

        for index, field in enumerate(column_list):
            if field in request.GET and request.GET.get(field):  # 如果该字段存在并且不为空
                if field == "title":
                    q.add(Q(Q(**{field + "__contains": request.GET[field]}) | Q(**{"url__contains": request.GET[field]})), Q.AND)
                    # q.add(Q(**{field + "__contains": request.GET[field]}), Q.AND)

                else:
                    q.add(Q(**{field: request.GET[field]}), Q.AND)
        # q = Q()
        if role_id in guanli_role_list:
            filter_dict = {
                "task__task__status__lt": 10,   # 已撤销的不显示
                # "task__task__client_user__task_edit_show": True,   # 显示该用户所有的任务
            }
            # q.add(Q(Q(**{"task__task__task__wenda_type__in": [1, 10]}) | Q(**{"task__task__client_user__task_edit_show": True})), Q.AND)
        else:
            print(user_id)
            filter_dict = {
                "task__edit_user_id": user_id,
                "task__task__status__lt": 10,
            }
            # if role_id != 14:
            #     filter_dict["task__task__client_user__task_edit_show"] = True
                # q.add(Q(Q(**{"task__task__client_user__task_edit_show": True}) | Q(**{"task__task__task__wenda_type__in": [1, 10]})), Q.AND)

        # objs = models.EditPublickTaskManagement.objects.select_related('task__task__client_user').filter(**filter_dict).filter(q).order_by(order_column)
        # objs = models.EditPublickTaskManagement.objects.select_related('task__task__client_user', 'task__task__task','task__edit_user').filter(**filter_dict).filter(q).order_by(order_column)
        objs = models.EditPublickTaskManagement.objects.select_related('task__task__client_user', 'task__task__task','task__edit_user').filter(**filter_dict).filter(q).order_by(order_column)
        print('filter_dict -->', filter_dict)
        print('q -->', q, objs.count(), user_id)

        data_list = []
        for obj in objs:
            if obj.task.task.task.wenda_type == 2 and role_id != 14 and not obj.task.task.client_user.task_edit_show:
                continue
            else:
                data_list.append(obj)

        result_data = {
            "recordsFiltered": len(data_list),
            "recordsTotal": len(data_list),
            "data": [],
        }

        for index, obj in enumerate(data_list[start: (start + length)], start=1):
            client_username = "%s-%s" % (obj.task.task.client_user.username, obj.task.id)

            update_date = ""
            if obj.update_date:
                update_date = obj.update_date.strftime("%Y-%m-%d %H:%M:%S")

            oper = ""
            if role_id != 14:   # 商务通渠道角色不显示下面功能
                if obj.status == 2:
                # if obj.status == 2 and obj.task.status != 5 and role_id == 13:
                    oper += """
                        <a class="btn btn-round btn-sm bg-warning margin-bottom-5" href="/edit_error_content/{tid}/" target="_blank"><i class="icon fa-pencil" aria-hidden="true"></i>修改</a>
                    """.format(tid=obj.id)

                # 如果修改次数大于0 则展示历史数据
                if obj.submit_num > 0:
                    oper += """
                        <a class="btn btn-round btn-sm bg-warning margin-bottom-5" aria-hidden="true" href="edit_history/{tid}/" data-toggle="modal" data-target="#exampleFormModal">
                            <i class="icon fa-search" aria-hidden="true"></i>查看历史数据
                        </a>
                    """.format(tid=obj.id)
                if role_id in guanli_role_list:
                    oper += """
                        <a class="btn btn-round btn-sm bg-info margin-bottom-5" aria-hidden="true" href="rengong/{tid}/" data-toggle="modal" data-target="#exampleFormModal">
                            <i class="icon fa-edit" aria-hidden="true"></i>人工回答
                        </a>
                    """.format(tid=obj.id)

            title = obj.title
            if obj.is_select_cover_back:
                title = "<a href={link} target='_blank'>{title}</a>".format(title=title, link=obj.url)

            result_data["data"].append(
                [
                    index, client_username,obj.task.edit_user.username, obj.get_status_display(),obj.task.task.task.get_wenda_type_display(), title, obj.content,
                    obj.submit_num, update_date, oper
                ]
            )

        return HttpResponse(json.dumps(result_data))

    if role_id in [1, 4]:
        filter_dict = {}
    else:
        filter_dict = {
            "edit_user_id": user_id
        }
    edit_task_management_objs = models.EditTaskManagement.objects.select_related("task__client_user").filter(**filter_dict)

    user_data = models.EditPublickTaskManagement.objects.values(
        'task__task__client_user_id',
        'task__task__client_user__username'
    ).annotate(Count("id"))
    print(user_data)

    if "_pjax" in request.GET:
        return render(request, 'wenda/edit_content_detail/edit_content_detail_pjax.html', locals())
    return render(request, 'wenda/edit_content_detail/edit_content_detail.html', locals())


@pub.is_login
def edit_content_detail_oper(request, oper_type, o_id):
    user_id = request.session["user_id"]
    response = pub.BaseResponse()

    if request.method == "POST":

        # 人工完成单条已经存在任务
        if oper_type == "rengong":

            response = pub.BaseResponse()

            content = request.POST.get("content")

            print(request.POST)
            obj = models.EditPublickTaskManagement.objects.select_related('run_task').get(id=o_id)

            if not content:
                response.status = False
                response.message = "请填写答案"

            if response.status and obj.content == content:
                response.status = False
                response.message = "答案无变化"

            if response.status:
                obj.status = 3
                obj.content = content

                wenda_robot_task_obj = models.WendaRobotTask.objects.get(id=obj.run_task.id)
                wenda_robot_task_obj.content = content
                wenda_robot_task_obj.status = 6

                models.RobotAccountLog.objects.create(
                    wenda_robot_task=wenda_robot_task_obj,
                    status=2,
                    phone_num="人工发布",
                )

                tongji_objs = models.TongjiKeywords.objects.filter(run_task=wenda_robot_task_obj)
                if tongji_objs:
                    tongji_objs.update(
                        content=content,
                        is_update=False,
                        is_pause=False,
                        update_date=datetime.datetime.now()
                    )
                else:
                    models.TongjiKeywords.objects.create(
                        task_id=wenda_robot_task_obj.task.id,
                        title=obj.title,
                        content=obj.content,
                        url=obj.url,
                        run_task=wenda_robot_task_obj,
                    )
                obj.save()
                wenda_robot_task_obj.save()

                response.status = True
                response.message = "人工完成成功"

        # 添加人工完成当前不存在的任务
        elif oper_type == "rengong_add":
            response = pub.BaseResponse()

            task_id = request.POST.get('task_id')           # 任务id
            edit_id = request.POST.get('edit_id')           # 编辑id
            zhidao_url = request.POST.get('zhidao_url')     # 知道链接
            title = request.POST.get('title')               # 标题
            content = request.POST.get('content')           # 内容

            task_obj = models.Task.objects.get(id=task_id)

            wenda_robot_task_objs = models.WendaRobotTask.objects.filter(
                task__release_user_id=task_obj.id,
                wenda_url=zhidao_url
            )
            if wenda_robot_task_objs:
                response.status = False
                response.message = "链接已经存在"

            if response.status:
                wenda_robot_task_obj = models.WendaRobotTask.objects.create(
                    task_id=task_id,
                    title=title,
                    content=content,
                    wenda_url=zhidao_url,
                    release_platform=1,
                    wenda_type=2,
                    status=6,
                    next_date=datetime.datetime.now()
                )
                print(wenda_robot_task_obj.id)

                edit_task_management_obj = models.EditTaskManagement.objects.filter(task__task__id=task_id)
                models.EditPublickTaskManagement.objects.create(
                    task_id=edit_task_management_obj[0].id,
                    url=zhidao_url,
                    title=title,
                    content=content,
                    status=3,
                    run_task=wenda_robot_task_obj
                )

                models.TongjiKeywords.objects.create(
                    task_id=task_id,
                    title=title,
                    content=content,
                    url=zhidao_url,
                    run_task=wenda_robot_task_obj
                )

                response.status = True
                response.message = "添加成功"

        # 渠道角色下载报表
        elif oper_type == "download":
            objs = models.EditPublickTaskManagement.objects.filter(task__edit_user_id=user_id)
            file_name = os.path.join("statics", "upload_files", str(int(time.time() * 1000)) + ".xlsx")

            data_list = []
            for obj in objs:
                data_list.append({
                    "title": obj.title,
                    "content": obj.content,
                    "url": obj.url,
                    "status": obj.get_status_display(),
                    "create_date": obj.create_date.strftime("%Y-%m-%d %H:%M:%S"),
                    "update_date": obj.update_date.strftime("%Y-%m-%d %H:%M:%S")
                })
            status_choices = models.EditPublickTaskManagement.status_choices
            tasks.EditPublickTaskManagementWriteExcel.delay(file_name, data_list)

            response.status = True
            response.message = "导出成功"
            response.download_url = "/" + file_name


        return JsonResponse(response.__dict__)

    else:
        # 查看历史修改数据
        if oper_type == "edit_history":
            objs = models.EditTaskLog.objects.filter(edit_public_task_management_id=o_id)
            return render(request, 'wenda/edit_content_detail/edit_content_detail_modal_edit_history.html', locals())

        # 人工回答
        elif oper_type == "rengong":
            objs = models.EditPublickTaskManagement.objects.get(id=o_id)
            return render(request, 'wenda/edit_content_detail/edit_content_detail_modal_rengong.html', locals())

        # 添加人工完成当前不存在的任务
        elif oper_type == "rengong_add":
            task_objs = models.Task.objects.filter(release_platform=1, wenda_type=2)

            # 内部编辑
            bianji_objs = models.UserProfile.objects.filter(role_id=13)
            return render(request, 'wenda/edit_content_detail/edit_content_detail_modal_rengong_add.html', locals())

