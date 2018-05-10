#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author:zhangcong
# Email:zc_92@sina.com


from django.shortcuts import render, HttpResponse
from webadmin.views_dir import pub

from webadmin import models

import json

from django.db.models import Q

import datetime


# 客户日覆盖数
@pub.is_login
def client_day_covering_num(request):

    if "type" in request.GET and request.GET["type"] == "ajax_json":
        length = int(request.GET.get("length"))
        start = int(request.GET.get("start"))

        # 排序
        column_list = ["id", "client_id", "date", "covering_number", "covering_number_zhiding", "covering_number_wenti", "oper"]
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

        objs = models.ClientCoveringNumber.objects.filter(q).order_by(order_column)

        result_data = {
            "recordsFiltered": objs.count(),
            "recordsTotal": objs.count(),
            "data": []
        }

        for index, obj in enumerate(objs[start: (start + length)], start=1):
            date = obj.date.strftime("%Y-%m-%d")

            result_data["data"].append(
                [
                    index,
                    obj.client.username,
                    date,
                    obj.covering_number,
                    "{zhiding_total_num} / {zhiding_pc_num} / {zhiding_wap_num}".format(
                        zhiding_total_num=obj.covering_zhiding_number_pc + obj.covering_zhiding_number_wap,
                        zhiding_pc_num=obj.covering_zhiding_number_pc,
                        zhiding_wap_num=obj.covering_zhiding_number_wap
                    ),
                    "{wenti_total_num} / {wenti_pc_num} / {wenti_wap_num}".format(
                        wenti_total_num=obj.covering_wenti_number_pc + obj.covering_wenti_number_wap,
                        wenti_pc_num=obj.covering_wenti_number_pc,
                        wenti_wap_num=obj.covering_wenti_number_wap
                    ),
                    ""
                ]
            )

        return HttpResponse(json.dumps(result_data))

    wendaClientUserObjs = models.UserProfile.objects.filter(role_id=5, is_delete=False)
    if "_pjax" in request.GET:
        return render(request, 'wenda/client_day_covering_num/client_day_covering_num_pjax.html', locals())
    return render(request, 'wenda/client_day_covering_num/client_day_covering_num.html', locals())

