#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author:zhangcong
# Email:zc_92@sina.com


from django.shortcuts import render, HttpResponse
from webadmin.views_dir import pub

from webadmin import models
from django.http import JsonResponse

from webadmin.forms import user
import json

from django.db.models import F
from django.db.models import Q
from webadmin.views_dir.wenda.message import AddMessage
import datetime

import os
import time

from wenda_celery_project import tasks


# 排名数据
@pub.is_login
def rank_data(request):
    user_id = request.session["user_id"]
    role_id = request.session["role_id"]

    if "type" in request.GET and request.GET["type"] == "ajax_json":
        length = int(request.GET.get("length"))
        start = int(request.GET.get("start"))

        # 排序
        column_list = ["id", "keywords__client_user_id", "keywords__keywords", "rank", "task_type", "create_date", "insert_type", "rank_type", "department"]
        order_column = request.GET.get('order[0][column]', 1)  # 第几列排序
        order = request.GET.get('order[0][dir]')  # 正序还是倒序
        order_column = column_list[int(order_column)]
        if order == "desc":
            order_column = "-{order_column}".format(order_column=order_column)
        else:
            order_column = order_column

        print(order_column)
        if order_column.endswith("create_date"):
            order_column = (order_column, "keywords", "-task_type")
        else:
            order_column = (order_column, )

        q = Q()
        # if request.GET.get("create_date"):
        #     q.add(Q(**{"create_date": now_date}), Q.AND)

        for index, field in enumerate(column_list):
            if field in request.GET and request.GET.get(field):  # 如果该字段存在并且不为空
                if field in ["keywords__keywords"]:
                    q.add(Q(**{field + "__contains": request.GET[field]}), Q.AND)
                elif field == "insert_type":
                    q.add(Q(**{"keywords__type": request.GET[field]}), Q.AND)
                elif field == "rank_type":
                    q.add(Q(**{"task_type": request.GET[field]}), Q.AND)
                elif field == "department":     # 科室
                    hospital_information_data = models.HospitalInformation.objects.filter(department_id=request.GET[field]).values_list("user_id")
                    user_id_list = [i[0] for i in hospital_information_data]
                    q.add(Q(**{"keywords__client_user_id__in": user_id_list}), Q.AND)
                else:
                    q.add(Q(**{field: request.GET[field]}), Q.AND)

        if role_id == 5:

            objs = models.SearchKeywordsRankLog.objects.select_related("keywords", "keywords__client_user").filter(keywords__client_user_id=user_id).filter(q).order_by(*order_column)
        else:
            objs = models.SearchKeywordsRankLog.objects.select_related("keywords", "keywords__client_user").filter(q).order_by(*order_column)

        result_data = {
            "recordsFiltered": objs.count(),
            "recordsTotal": objs.count(),
            "data": []
        }

        type_choices = models.SearchKeywordsRankLog.type_choices

        for index, obj in enumerate(objs[start: (start + length)], start=1):

            if obj.create_date:
                create_date = obj.create_date.strftime("%Y-%m-%d")
            else:
                create_date = ""

            # task_type = obj.get_task_type_display() + "(" + obj.get_data_type_display() + ")"
            task_type = obj.get_task_type_display()

            # keywords_type = ""
            # for i in keywords_type_choices:
            #     if i[0] == obj.keywords.type:
            #         keywords_type = i[1]
            #         break

            keywords = """
                <a href="{search_url}" target="_blank">{keywords}</a>
            """.format(search_url=obj.search_url, keywords=obj.keywords.keywords)

            result_data["data"].append(
                [index, obj.keywords.client_user.username, keywords, obj.rank, task_type, create_date]
            )

        return HttpResponse(json.dumps(result_data))

    status_choices = models.UserProfile.status_choices
    wendaClientUserObjs = models.UserProfile.objects.filter(
        is_delete=False,
        status=1,
        role_id=5
    ).values('id', 'username')
    rank_type_choices = models.SearchKeywordsRankLog.type_choices

    department_data = models.Department.objects.all().values("id", "name")

    if "_pjax" in request.GET:
        return render(request, 'wenda/rank_data/rank_data_pjax.html', locals())
    return render(request, 'wenda/rank_data/rank_data.html', locals())


def rank_data_oper(request, oper_type, o_id):
    user_id = request.session["user_id"]

    response = pub.BaseResponse()

    if request.method == "POST":
        if oper_type == "download":
            user_id = request.POST.get("user_id")
            if not user_id:
                response.status = False
                response.message = "请选择导出用户名称"
            else:

                file_name = os.path.join("statics", "upload_files", str(int(time.time() * 1000)) + ".xlsx")

                search_objs = models.SearchKeywordsRank.objects.select_related('client_user').filter(client_user_id=user_id)

                data_list = []
                for obj in search_objs:
                    for i in obj.searchkeywordsranklog_set.select_related('keywords').exclude(task_type=2):
                        data_list.append({
                            "username": obj.client_user.username,
                            "create_date": i.create_date,
                            "task_type": i.get_task_type_display(),
                            "keywords": i.keywords.keywords,
                            "rank": i.rank,
                            "type": i.keywords.get_type_display()
                        })

                tasks.rank_data_generate_excel.delay(file_name, data_list)

                response.status = True
                response.message = "导出成功"
                response.download_url = "/" + file_name

        return JsonResponse(response.__dict__)
    else:
        if oper_type == "download":
            wenda_type_choices = models.WendaRobotTask.wenda_type_choices
            wendaClientUserObjs = models.UserProfile.objects.filter(
                is_delete=False,
                status=1,
                role_id=5
            ).values('id', 'username')

            return render(request, "wenda/rank_data/rank_data_modal_download.html", locals())