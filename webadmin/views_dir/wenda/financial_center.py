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

from django.db.models import Count, Min, Max, Sum


# 财务中心
@pub.is_login
def financial_center(request):
    user_id = request.session["user_id"]
    tixian_objs = models.TiXian.objects.filter(user_id=user_id, status=1)

    type_choices = models.BalanceDetail.type_choices
    balance_detail_objs = models.BalanceDetail.objects.select_related('oper_user').filter(user_id=user_id)

    user_profile_obj = models.UserProfile.objects.get(id=user_id)
    balance = user_profile_obj.balance   # 可用余额

    tixian_role_ids = [6, 8, 9]     # 可以提现的角色id

    # 消费金额
    total_consumption = balance_detail_objs.filter(account_type=2).values('money')

    refunds_money = balance_detail_objs.filter(account_type=5).values('money')
    if total_consumption:

        refunds_money = sum([i["money"] for i in refunds_money])

        total_consumption = sum([i["money"] for i in total_consumption]) - refunds_money

    else:
        total_consumption = 0

    if "type" in request.GET and request.GET["type"] == "ajax_json":
        length = int(request.GET.get("length"))
        start = int(request.GET.get("start"))

        column_list = ['id', 'account_type', 'money', 'create_date', 'oper_user']

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

        balance_detail_objs = balance_detail_objs.filter(q).order_by(order_column)

        # ##### 排序加搜索 ##### ↑↑↑↑↑↑↑↑↑↑↑

        result_data = {
            "recordsFiltered": balance_detail_objs.count(),
            "data": []
        }

        for index, obj in enumerate(balance_detail_objs[start: (start + length)], start=1):

            if obj.create_date:
                create_date = obj.create_date.strftime("%Y-%m-%d %H:%M:%S")
            else:
                create_date = ""

            account_type = ""
            for i in type_choices:
                if i[0] == obj.account_type:
                    account_type = i[1]
                    break

            table_data = [index, account_type, obj.money, create_date, obj.oper_user.username]
            result_data["data"].append(table_data)

        return HttpResponse(json.dumps(result_data))

    if "_pjax" in request.GET:
        return render(request, 'wenda/financial_center/financial_center_pjax.html', locals())
    return render(request, 'wenda/financial_center/financial_center.html', locals())


def financial_center_oper(request, oper_type, o_id):
    user_id = request.session["user_id"]
    user_profile_obj = models.UserProfile.objects.get(id=user_id)

    if request.method == "POST":
        response = pub.BaseResponse()

        tixian_moeny = request.POST["tixian_moeny"]     # 提现金额
        tixian_name = request.POST["tixian_name"]   # 提现姓名
        tixian_zhanghao = request.POST["tixian_zhanghao"]   # 提现账户

        if not tixian_moeny or not tixian_moeny.isdigit():
            response.status = False
            response.message = "提现金额有误"
        elif user_profile_obj.balance == 0:
            response.status = False
            response.message = "无可提现金额"

        elif int(tixian_moeny) > user_profile_obj.balance:
            response.status = False
            response.message = "提现金额已超出可提现金额"

        if response.status and not tixian_name:
            response.status = False
            response.message = "支付宝姓名不能为空"

        if response.status and not tixian_zhanghao:
            response.status = False
            response.message = "提现账户不能为空"

        if response.status:
            user_profile_obj.tixian_name = tixian_name
            user_profile_obj.tixian_zhanghao = tixian_zhanghao
            user_profile_obj.save()

            models.TiXian.objects.create(
                user_id=user_id,
                money=tixian_moeny,
            )

            response.status = True
            response.message = "提现申请已提交"

        return JsonResponse(response.__dict__)


    else:
        if oper_type == "tixian":

            tixian_objs = models.TiXian.objects.filter(user_id=user_id, status=1)

            return render(request, 'wenda/financial_center/financial_center_modal_tixian.html', locals())

