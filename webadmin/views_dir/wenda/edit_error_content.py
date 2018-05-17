#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author:zhangcong
# Email:zc_92@sina.com


from django.shortcuts import render, HttpResponse
from webadmin.views_dir import pub

from webadmin import models
from django.http import JsonResponse
from django.db.models import Q

from bson.objectid import ObjectId

from django.views.decorators.csrf import csrf_exempt

import datetime
import random

import json


@csrf_exempt
def edit_error_content(request, o_id):

    # 任务对应状态id
    title_update_id_list = [22, 30, 40]
    content_update_id_list = [20]

    if request.method == "POST":
        response = pub.BaseResponse()

        content = request.POST.get("content")
        title = request.POST.get("title")
        add_map = request.POST.get("addMap", default="false")

        if not title:
            response.status = False
            response.message = "问题不能为空"
        elif not content:
            response.status = False
            response.message = "答案不能为空"
        else:
            objs = models.EditPublickTaskManagement.objects.filter(
                content=content,
                title=title
            ).exclude(id=o_id)
            obj = models.EditPublickTaskManagement.objects.get(id=o_id)
            if obj.content == content and obj.title == title:
                response.status = False
                response.message = "未修改,请修改后提交"

            elif objs.count() > 0:
                response.status = False
                response.message = "提交内容存在,请修改后在进行提交"
            else:
                # 问题敏感词列表
                SensitiveWordTitle_list = [i[0] for i in models.SensitiveWordLibrary.objects.filter(w_type=1).values_list('name')]

                # 答案敏感词列表
                SensitiveWordContent_list = [i[0] for i in models.SensitiveWordLibrary.objects.filter(w_type=2).values_list('name')]

                title_err_name_list = []  # 问题中包含的敏感词列表
                content_err_name_list = []  # 答案中包含的敏感词列表
                for name in SensitiveWordTitle_list:
                    if name in title:
                        title_err_name_list.append(name)

                for name in SensitiveWordContent_list:
                    if name in content:
                        content_err_name_list.append(name)

                if title_err_name_list or content_err_name_list:
                    response.status = False
                    response.data = {
                        "title_err_name_list": title_err_name_list,
                        "content_err_name_list": content_err_name_list
                    }
                    response.message = "问题或答案中包含敏感词,已标红"

                if response.status:
                    obj = models.EditPublickTaskManagement.objects.get(id=o_id)
                    obj.status = 1
                    obj.content = content
                    obj.title = title
                    obj.submit_num += 1
                    obj.is_select_cover_back = False
                    obj.save()
                    models.EditTaskLog.objects.create(
                        bianji_dahui_update=2,
                        title=obj.title,
                        content=obj.content,
                        edit_public_task_management_id=o_id
                    )


                    wenda_robot_task_obj = models.WendaRobotTask.objects.get(id=obj.run_task.id)
                    if wenda_robot_task_obj.status in content_update_id_list:   # 回复异常
                        wenda_robot_task_obj.content = content
                        wenda_robot_task_obj.status = 2

                        tongji_keywords_objs = models.TongjiKeywords.objects.filter(run_task=wenda_robot_task_obj)
                        if tongji_keywords_objs:
                            tongji_keywords_objs.update(is_update=True)

                    elif wenda_robot_task_obj.status in title_update_id_list:   # 回复异常, 标题过长, 链接失效
                        wenda_robot_task_obj.title = title
                        wenda_robot_task_obj.status = 1

                    if add_map == "true":
                        wenda_robot_task_obj.add_map = 1
                    else:
                        wenda_robot_task_obj.add_map = 2

                    wenda_robot_task_obj.update_date = datetime.datetime.now()
                    wenda_robot_task_obj.save()

                    response.status = True
                    response.message = "修改成功, 发布中。。。"
        return JsonResponse(response.__dict__)

    else:
        obj = models.EditPublickTaskManagement.objects.get(id=o_id)
        wenda_robot_task_obj = models.WendaRobotTask.objects.get(id=obj.run_task.id)

        if wenda_robot_task_obj.task.release_user.map_search_keywords and wenda_robot_task_obj.task.release_user.map_match_keywords:
            map_flag = True
        else:
            map_flag = False

        return render(request, 'wenda/edit_error_content/edit_error_content.html', locals())
