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


# 案例库
@pub.is_login
def case_library(request):
    role_id = request.session.get("role_id")
    user_id = request.session.get("user_id")
    now_date = datetime.datetime.now().strftime("%Y-%m-%d")

    if "type" in request.GET and request.GET["type"] == "ajax_json":
        length = int(request.GET.get("length"))
        start = int(request.GET.get("start"))

        # 排序
        column_list = [
            "index", "keywords__client_user__username", "keywords__keyword", "title",
            "page_type", "rank", "create_date", 'keywords__client_user_id', 'search_keyword', 'task_type','keywords__client_user__status','shangwutong'
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
                if field == "create_date":
                    tomorrow_dt = datetime.datetime.strptime(request.GET[field], "%Y-%m-%d") + datetime.timedelta(days=1)
                    q.add(Q(**{field + "__gte": request.GET[field]}), Q.AND)
                    q.add(Q(**{field + "__lt": tomorrow_dt}), Q.AND)

                elif field == "search_keyword":
                    q.add(Q(**{"keywords__keyword__contains": request.GET[field]}), Q.AND)
                elif field == 'keywords__client_user__status':
                    q.add(Q(**{'keywords__client_user__status':request.GET[field]}),Q.AND)
                elif field == 'shangwutong':
                    q.add(Q(**{'keywords__is_shangwutong':request.GET[field]}),Q.AND)
                else:
                    q.add(Q(**{field: request.GET[field]}), Q.AND)

        if not request.GET.get('create_date'):
            q.add(Q(**{"create_date__gte": now_date}), Q.AND)

        if request.GET.get("department_id"):
            department_id = request.GET.get("department_id")
            print('department_id= ==========> ',department_id)
            user_id_list = [i[0] for i in models.HospitalInformation.objects.filter(
                department_id=department_id,
                # user__status=1,
                user__is_delete=False,
                user__role_id=5
            ).values_list('user_id')]
            print('user_id_list -->', user_id_list)
            q.add(Q(**{'keywords__client_user_id__in': user_id_list}), Q.AND)

        objss = models.KeywordsCover.objects.filter(keywords__client_user_id__in=[37, 63, 66, 80, 104, 112, 113, 127])
        print("objss -->", objss.count())
        print('q -->', q)

        # 成都美尔贝不显示
        objs = models.KeywordsCover.objects.select_related('keywords', 'keywords__client_user').filter(q).exclude(keywords__client_user_id=175)
        if role_id == 12:
            objs = objs.exclude(keywords__client_user__username__contains='YZ-', keywords__client_user__company=1)

        objs = objs.order_by(order_column)
        print("01-->", datetime.datetime.now())
        count = objs.count()
        print(objs.query)
        print("0-->", datetime.datetime.now())

        result_data = {
            "recordsFiltered": count,
            "recordsTotal": count,
            "data": []
        }

        print("1-->", datetime.datetime.now())
        for index, obj in enumerate(objs[start: (start + length)], start=1):
            # 创建时间
            if obj.create_date:
                create_date = obj.create_date.strftime("%Y-%m-%d")
            else:
                create_date = ""

            if obj.task_type == 1:
                keyword = "<a href='{url}' target='_blank'>{keyword}</a>"
            else:   # obj.task_type == 2
                keyword = "<a href='{url}' target='_blank'>{keyword} <span class='badge badge-warning'>地图</span></a>"

            # if obj.task_type == 2 and obj.keywords.is_shangwutong:
            #     keyword = "<a href='{url}' target='_blank'>{keyword}<span class='badge badge-warning'>地图</span> <span class='badge badge-warning'>商务通</span></a>"
            # else:
            #     if obj.task_type == 2:
            #         keyword = "<a href='{url}' target='_blank'>{keyword}<span class='badge badge-warning'>地图</span></a>"
            #     elif obj.keywords.is_shangwutong:
            #         keyword = "<a href='{url}' target='_blank'>{keyword}<span class='badge badge-warning'>商务通</span></a>"
            #     else:
            #         keyword = "<a href='{url}' target='_blank'>{keyword}</a>"

            if obj.page_type == 1:  # pc
                url = 'https://www.baidu.com/s?wd={keyword}'.format(keyword=obj.keywords.keyword)
            else:   # 移动
                url = 'https://m.baidu.com/s?word={keyword}'.format(keyword=obj.keywords.keyword)

            keyword = keyword.format(url=url, keyword=obj.keywords.keyword)

            wenda_robot_task_objs = models.WendaRobotTask.objects.filter(wenda_url=obj.url, task__release_user_id=obj.keywords.client_user.id)
            title = wenda_robot_task_objs[0].title
            # title = '测试'
            # ["index", "keywords__client_user_id", "keywords__keywords", "page_type", "rank", "create_date", "oper"]
            result_data["data"].append([
                index, obj.keywords.client_user.username, keyword, title,
                obj.get_page_type_display(), obj.rank, create_date
            ])
        print("2-->", datetime.datetime.now())
        return HttpResponse(json.dumps(result_data))

    page_type_choices = models.KeywordsCover.page_type_choices
    task_type_choices = models.KeywordsCover.task_type_choices
    qiyong_status = models.UserProfile.status_choices
    user_objs = models.UserProfile.objects.filter(
        role_id=5,
        # status=1,
        is_delete=False
     )
    if role_id in [12, '12']:
        user_objs = user_objs.exclude(username__contains='YZ-', company=2)

    department_objs = models.Department.objects.all()
    print('department_objs-->',department_objs)
    if "_pjax" in request.GET:
        return render(request, 'wenda/case_library/case_library_pjax.html', locals())
    return render(request, 'wenda/case_library/case_library.html', locals())


@pub.is_login
def case_library_oper(request, oper_type, o_id):
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








