#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author:zhangcong
# Email:zc_92@sina.com


from django.shortcuts import render, HttpResponse, redirect, reverse
from webadmin.views_dir import pub

from webadmin import models
from django.http import JsonResponse

from webadmin.forms.my_task import MyTaskCreateForm
import json

from django.db.models import F
from django.db.models import Q

from webadmin.views_dir.wenda.message import AddMessage

import datetime

import os


# 提现管理
@pub.is_login
def tixian_management(request):

    user_id = request.session["user_id"]

    status_choices = models.TiXian.status_choices

    if "type" in request.GET and request.GET["type"] == "ajax_json":

        length = int(request.GET.get("length"))
        start = int(request.GET.get("start"))

        # 排序
        column_list = ["id", "user_id", "money", "status", "tixian_name", "tixian_zhanghao" "remark", "create_date", "complete_date", "oper"]
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
                if field in ["status", "release_platform", "wenda_type"]:
                    q.add(Q(**{field: request.GET[field]}), Q.AND)
                else:
                    q.add(Q(**{field + "__contains": request.GET[field]}), Q.AND)

        tixian_objs = models.TiXian.objects.select_related('user').filter(q).order_by(order_column)

        result_data = {
            "recordsFiltered": tixian_objs.count(),
            "recordsTotal": tixian_objs.count(),
            "data": []
        }

        status_choices = models.TiXian.status_choices

        for index, obj in enumerate(tixian_objs[start: (start + length)], start=1):

            # 创建时间
            if obj.create_date:
                create_date = obj.create_date.strftime("%Y-%m-%d %H:%M:%S")
            else:
                create_date = ""

            # 编辑完成时间
            if obj.complete_date:
                complete_date = obj.complete_date.strftime("%Y-%m-%d %H:%M:%S")
            else:
                complete_date = ""

            # 状态
            status = ""
            for i in status_choices:
                if i[0] == obj.status:
                    status = i[1]
                    break

            tixian_name = obj.user.tixian_name
            tixian_zhanghao = obj.user.tixian_zhanghao

            oper = ""

            if obj.status == 1:
                oper += """
                    <a class="btn btn-round btn-sm bg-primary" aria-hidden="true" href="dakuan_confirm/{obj_id}/" data-toggle="modal" data-target="#exampleFormModal">确认打款</a>
                """.format(obj_id=obj.id)

            result_data["data"].append([index, obj.user.username, obj.money, tixian_name, tixian_zhanghao, status, obj.remark, create_date, complete_date, oper])

        return HttpResponse(json.dumps(result_data))

    if "_pjax" in request.GET:
        return render(request, 'myadmin/tixian_management/tixian_management_pjax.html', locals())
    return render(request, 'myadmin/tixian_management/tixian_management.html', locals())


@pub.is_login
def tixian_management_oper(request, oper_type, o_id):
    user_id = request.session["user_id"]
    response = pub.BaseResponse()

    if request.method == "POST":
        # 确认打款
        if oper_type == "dakuan_confirm":

            remark = request.POST["remark"]
            if not remark:
                response.status = False
                response.message = "打款信息不能为空"
            else:
                tixian_obj = models.TiXian.objects.select_related('user').get(id=o_id)

                tixian_obj.remark = remark
                tixian_obj.status = 2
                tixian_obj.complete_date = datetime.datetime.now()
                tixian_obj.save()

                message = "提现金额 {moeny} 已成功支付,请注意查收".format(
                    moeny=tixian_obj.money,
                )
                AddMessage(request, tixian_obj.user.id, message)

                # 记录消费明细
                models.BalanceDetail.objects.create(
                    user=tixian_obj.user,
                    account_type=4,
                    money=tixian_obj.money,
                    oper_user_id=user_id,
                    remark=remark
                )

                user_profile_obj = models.UserProfile.objects.get(id=tixian_obj.user.id)
                user_profile_obj.balance -= tixian_obj.money
                user_profile_obj.save()

                response.status = True
                response.message = "提交成功"

        return JsonResponse(response.__dict__)

    else:

        # 确认打款
        if oper_type == "dakuan_confirm":

            tixian_obj = models.TiXian.objects.get(id=o_id)
            return render(request, 'myadmin/tixian_management/tixian_management_modal_dakuan_confirm.html', locals())
