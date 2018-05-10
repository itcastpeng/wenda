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

from django.db.models import F, Q


# 财务管理
@pub.is_login
def financial_management(request):
    user_id = request.session["user_id"]
    role_id = models.UserProfile.objects.get(id=user_id).role_id

    type_choices = models.BalanceDetail.type_choices
    if "type" in request.GET and request.GET["type"] == "ajax_json":

        length = int(request.GET.get("length"))
        start = int(request.GET.get("start"))

        # 排序
        column_list = ["id", "user_id", "account_type", "money", "balance", "zbalance", "create_date", "remark", "oper_user_id", "stop_date", "username"]
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
                if field == "account_type":
                    q.add(Q(**{field: request.GET[field]}), Q.AND)
                elif field == "create_date":
                    q.add(Q(**{field + "__gte": request.GET[field]}), Q.AND)
                elif field == "stop_date":
                    q.add(Q(**{"create_date__lte": request.GET[field]}), Q.AND)
                elif field == "username":
                    q1 = Q()
                    q1.connector = 'OR'
                    q1.children.append(("user__username__contains", request.GET[field]))
                    q1.children.append(("oper_user__username__contains", request.GET[field]))
                    q.add(q1, Q.AND)
                else:
                    q.add(Q(**{field + "__contains": request.GET[field]}), Q.AND)

        balance_detail_objs = models.BalanceDetail.objects.select_related('user', 'oper_user').filter(user__is_delete=False).filter(q).order_by(order_column)

        result_data = {
            "recordsFiltered": balance_detail_objs.count(),
            "recordsTotal": balance_detail_objs.count(),
            "data": []
        }

        for index, obj in enumerate(balance_detail_objs[start: (start + length)], start=1):

            # 创建时间
            if obj.create_date:
                create_date = obj.create_date.strftime("%Y-%m-%d %H:%M:%S")
            else:
                create_date = ""

            # 类型
            account_type = ""
            for i in type_choices:
                if i[0] == obj.account_type:
                    account_type = i[1]
                    break

            obj_data = [index, obj.user.username, account_type, obj.money, obj.balance, obj.zbalance, create_date, obj.remark, obj.oper_user.username]
            result_data["data"].append(obj_data)

        return HttpResponse(json.dumps(result_data))

    if "_pjax" in request.GET:
        return render(request, 'myadmin/financial_management/financial_management_pjax.html', locals())
    return render(request, 'myadmin/financial_management/financial_management.html', locals())