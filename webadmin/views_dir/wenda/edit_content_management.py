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


# 编辑内容管理
@pub.is_login
def edit_content_management(request):
    role_id = request.session.get('role_id')
    role_names = models.Role.objects.values_list("id", "name")
    status_choices = models.UserProfile.status_choices

    if "type" in request.GET and request.GET["type"] == "ajax_json":
        length = int(request.GET.get("length"))
        start = int(request.GET.get("start"))

        # 排序
        column_list = [
            "id", "client_user__username", "number", "status", "reference_file_path", "remark",
            "create_user__username", "create_date", "complete_date", "oper", "client_user_id"
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

        objs = models.EditContentManagement.objects.select_related("client_user").filter(
            is_delete=False,
        ).exclude(status=10).filter(q).order_by(order_column)

        result_data = {
            "recordsFiltered": objs.count(),
            "recordsTotal": objs.count(),
            "data": []
        }

        status_choices = models.EditContentManagement.status_choices

        for index, obj in enumerate(objs[start: (start + length)], start=1):

            if obj.create_date:
                create_date = obj.create_date.strftime("%Y-%m-%d %H:%M:%S")
            else:
                create_date = ""

            if obj.complete_date:
                complete_date = obj.complete_date.strftime("%Y-%m-%d %H:%M:%S")
            else:
                complete_date = ""

            reference_file_path = ""
            if obj.reference_file_path:
                reference_file_path = """
                    <a href='{reference_file_path}' download="{client_username}">下载参考资料</a>
                """.format(
                    reference_file_path=obj.reference_file_path,
                    client_username=obj.client_user.username
                )

            oper = ""

            # 如果是等待分配状态,则可以进行分配操作
            if obj.status == 1 and role_id == 7:
                oper += """
                    <a class="btn btn-round btn-sm bg-success" aria-hidden="true" href="task_allotment/{obj_id}/" data-toggle="modal" data-target="#exampleFormModal">
                    <i class="icon fa-flag" aria-hidden="true"></i> 任务分配
                    </a>
                """.format(obj_id=obj.id)

            # 查看任务分配详情
            if obj.status >= 2:
                oper += """
                    <a class="btn btn-round btn-sm bg-success" aria-hidden="true" href="task_allotment_detail/{obj_id}/" data-toggle="modal" data-target="#exampleFormModal">
                    <i class="icon fa-search" aria-hidden="true"></i> 任务分配详情
                    </a>
                """.format(obj_id=obj.id)

            # 进入发布队列
            if obj.status == 3 and role_id == 7:
                oper += """
                    <a class="btn btn-round btn-sm bg-primary" aria-hidden="true" href="robot_pub/{obj_id}/" data-toggle="modal" data-target="#exampleFormModal">
                    <i class="icon fa-code-fork" aria-hidden="true"></i> 进入发布队列
                    </a>
                """.format(obj_id=obj.id)

            if obj.status > 2:
                oper += """
                    <a class="btn btn-round btn-sm bg-info" aria-hidden="true" href="task_edit_detail/{obj_id}/" data-toggle="modal" data-target="#exampleFormModal">
                    <i class="icon fa-search" aria-hidden="true"></i> 查看编写问题答案
                    </a>
                """.format(obj_id=obj.id)

            # oper += """
            #     <a class="btn btn-round btn-sm bg-primary" aria-hidden="true" href="update/{obj_id}/" data-toggle="modal" data-target="#exampleFormModal"><i class="icon fa-pencil-square-o"></i>修改</a>
            #     <a class="btn btn-round btn-sm bg-danger" aria-hidden="true" href="delete/{obj_id}/" data-toggle="modal" data-target="#exampleFormModal"><i class="fa fa-trash-o fa-fw"></i>删除</a>
            # """.format(obj_id=obj.id)

            result_data["data"].append(
                [
                    index, obj.client_user.username, obj.number, obj.get_status_display(), reference_file_path,
                    obj.remark, obj.create_user.username, create_date, complete_date, oper
                ]
            )

        return HttpResponse(json.dumps(result_data))

    status_choices = models.EditContentManagement.status_choices
    username_list = models.UserProfile.objects.filter(role_id=5, is_delete=False).values_list('id', 'username')
    if "_pjax" in request.GET:
        return render(request, 'wenda/edit_content_management/edit_content_management_pjax.html', locals())
    return render(request, 'wenda/edit_content_management/edit_content_management.html', locals())


@pub.is_login
def edit_content_management_oper(request, oper_type, o_id):
    user_id = request.session["user_id"]
    response = pub.BaseResponse()

    status_choices = models.EditContentManagement.status_choices

    if request.method == "POST":
        # 任务分配
        if oper_type == "task_allotment":
            print(request.POST)

            task_obj = models.EditContentManagement.objects.get(id=o_id)

            panduan_map = request.POST.get('panduan_map')
            if panduan_map:
                # obj = models.EditContentManagement.objects.filter(id=o_id)
                # obj[0].task.add_map = True
                # obj[0].save()
                obj = models.Task.objects.get(id=task_obj.task_id)
                obj.add_map = True
                obj.save()

            flag = True
            task_allotment_data = {}
            total = 0
            for i in dict(request.POST):
                if i.startswith("bianji"):
                    pub_num = request.POST.get(i)
                    if (pub_num.isdigit() and int(pub_num) >= 0) or not pub_num:      # 如果是整数类型并且大于等于0 或者为空
                        if pub_num:
                            total += int(pub_num)
                    else:
                        flag = False

                    task_allotment_data[int(i.replace("bianji_", ""))] = request.POST.get(i)

            if not flag or total != task_obj.number:
                response.status = False
                response.message = "分配任务有误"

            else:
                user_id_str = ""
                for edit_user_id, number in task_allotment_data.items():
                    if int(number) == 0:
                        continue

                    print(task_allotment_data, task_allotment_data.values())
                    models.EditTaskManagement.objects.create(
                        task=task_obj,
                        edit_user_id=edit_user_id,
                        number=number,
                        status=1,
                    )

                    # 将需要接收微信通知的用户的微信号统计出来
                    user_obj = models.UserProfile.objects.get(id=edit_user_id)
                    weixin_id = user_obj.weixin_id
                    if not weixin_id:   # 如果没有填写微信id 则告知 zhangcong
                        # 发送微信通知

                        now_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        text = "通知时间: {now_datetime} \n通知平台:诸葛问答\n用户 {username} 未设置微信id".format(
                            now_datetime=now_datetime,
                            username=user_obj.username
                        )
                        tasks.send_msg.delay("zhangcong", text)

                        continue

                    if user_id_str:
                        user_id_str = user_id_str + "|" + weixin_id
                    else:
                        user_id_str = weixin_id

                # 发送微信通知
                now_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                text = "通知时间: {now_datetime} \n您有新的口碑任务等待编写,请前往口碑后台 - 我的任务-编辑 功能中查看"
                tasks.send_msg.delay(user_id_str, text)

                task_obj.status = 2
                task_obj.save()
                response.status = True
                response.message = "分配成功"

        # 进入发布队列
        elif oper_type == "robot_pub":

            edit_content_management_obj = models.EditContentManagement.objects.get(id=o_id)
            task_obj = models.Task.objects.get(id=edit_content_management_obj.task.id)

            file_name = task_obj.name + '.' + "xls"
            file_save_path = "/".join(["statics", "task_excel", "result", file_name])

            tasks.edit_content_management_create_excel.delay(
                o_id,
                os.path.join(os.getcwd(), file_save_path),
                task_obj.wenda_type
            )

            # 编辑提交任务结果
            models.TaskProcessLog.objects.create(
                task=task_obj,
                status=3,
                oper_user_id=user_id
            )

            if task_obj.wenda_type == 2:    # 老问答
                task_obj.status = 6
                task_obj.publish_user_id = 8

                message1 = "您的任务 {task_name} 已经被平台派单员 [{paidan_name}] 指定编辑进行完成".format(
                    task_name=task_obj.name,
                    paidan_name=models.UserProfile.objects.get(id=user_id).username,
                    bianji_name="小明"
                )

                message2 = "平台派单员 [{paidan_name}] 分配给您新的任务 [{task_name}] , 请注意查看".format(
                    paidan_name=models.UserProfile.objects.get(id=user_id).username,
                    task_name=task_obj.name,
                )

                AddMessage(request, task_obj.release_user.id, message1)
                AddMessage(request, 8, message2)

                # 分配任务日志
                models.TaskProcessLog.objects.create(
                    task=task_obj,
                    status=2,
                    oper_user_id=user_id,
                    remark="任务分配给: %s" % "小明"
                )

                response.message = "开始发布!"
            else:
                task_obj.status = 3

                message = "您的任务 [{task_name}] 编辑已经提交结果,请前去查看,并审核".format(
                    task_name=task_obj.name,
                )

                AddMessage(request, task_obj.release_user.id, message)
                response.message = "进入发布队列成功!"

            task_obj.task_result_file_path = file_save_path

            task_obj.update_date = datetime.datetime.now()
            task_obj.save()

            edit_content_management_obj.status = 4
            edit_content_management_obj.save()

            response.status = True

        return JsonResponse(response.__dict__)

    else:
        roles_dict = models.Role.objects.all().values("id", "name")
        # 任务分配
        if oper_type == "task_allotment":
            user_objs = models.UserProfile.objects.filter(is_delete=False, role_id=13).values('id', 'username')
            task_obj = models.EditContentManagement.objects.get(id=o_id)
            map_status = task_obj.task.add_map
            return render(request, 'wenda/edit_content_management/edit_content_management_modal_task_allotment.html', locals())

        # 任务分配详情
        elif oper_type == "task_allotment_detail":
            detail_objs = models.EditTaskManagement.objects.select_related('edit_user').filter(task_id=o_id)
            return render(request, 'wenda/edit_content_management/edit_content_management_modal_task_allotment_detail.html', locals())

        # 机器人发布
        elif oper_type == "robot_pub":
            detail_objs = models.EditContentManagement.objects.get(id=o_id)
            return render(request, 'wenda/edit_content_management/edit_content_management_modal_robot_pub.html', locals())

        # 查看编辑编写的问题和答案的详细情况
        elif oper_type == "task_edit_detail":
            objs = models.EditPublickTaskManagement.objects.select_related('task__edit_user').filter(task__task_id=o_id)
            return render(request, 'wenda/edit_content_management/edit_content_management_modal_task_edit_detail.html', locals())

