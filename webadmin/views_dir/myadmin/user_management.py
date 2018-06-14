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


# 用户管理
@pub.is_login
def user_management(request):
    role_names = models.Role.objects.values_list("id", "name")
    status_choices = models.UserProfile.status_choices

    if "type" in request.GET and request.GET["type"] == "ajax_json":
        length = int(request.GET.get("length"))
        start = int(request.GET.get("start"))

        # 排序
        column_list = ["id", "username", "role", "status", "balance", "xie_wenda_money", "fa_wenda_money", "create_date", "last_login_date", "oper", "role_names","guanzhu_status"]
        order_column = request.GET.get('order[0][column]', 1)  # 第几列排序
        order = request.GET.get('order[0][dir]')  # 正序还是倒序
        order_column = column_list[int(order_column)]
        if order == "desc":
            order_column = "-{order_column}".format(order_column=order_column)
        else:
            order_column = order_column

        q = Q()
        for index, field in enumerate(column_list):
            print('field - - ->',field)
            if field in request.GET and request.GET.get(field):  # 如果该字段存在并且不为空
                if field in ["status"]:
                    q.add(Q(**{field: request.GET[field]}), Q.AND)
                elif field == "role_names":
                    print(request.GET[field])
                    q.add(Q(**{"role_id": request.GET[field]}), Q.AND)
                elif field == 'guanzhu_status':
                    print(type(request.GET[field]))
                    if request.GET[field]=='1':
                        q.add(Q(openid__isnull=False),Q.AND)
                    if request.GET[field]=='2':
                        q.add(Q(openid__isnull=True), Q.AND)
                else:
                    q.add(Q(**{field + "__contains": request.GET[field]}), Q.AND)

        user_profile_objs = models.UserProfile.objects.select_related("role").filter(is_delete=False).filter(q).order_by(order_column)

        result_data = {
            "recordsFiltered": user_profile_objs.count(),
            "recordsTotal": user_profile_objs.count(),
            "data": []
        }

        status_choices = models.UserProfile.status_choices

        for index, obj in enumerate(user_profile_objs[start: (start + length)], start=1):

            if obj.create_date:
                create_date = obj.create_date.strftime("%Y-%m-%d %H:%M:%S")
            else:
                create_date = ""

            if obj.last_login_date:
                last_login_date = obj.last_login_date.strftime("%Y-%m-%d %H:%M:%S")
            else:
                last_login_date = ""

            status = ""
            for i in status_choices:
                if i[0] == obj.status:
                    status = i[1]
                    break

            username = obj.username
            if not obj.openid:
                username = "<p>{username} <span style='color: red'>(未关注)<span><p>".format(
                    username=obj.username
                )

            oper = """
                <a class="btn btn-round btn-sm bg-success" aria-hidden="true" href="recharge/{obj_id}/" data-toggle="modal" data-target="#exampleFormModal"><i class="fa fa-jpy" aria-hidden="true"></i>充值</a>
                <a class="btn btn-round btn-sm bg-primary" aria-hidden="true" href="update/{obj_id}/" data-toggle="modal" data-target="#exampleFormModal"><i class="icon fa-pencil-square-o"></i>修改</a>
                <a class="btn btn-round btn-sm bg-danger" aria-hidden="true" href="delete/{obj_id}/" data-toggle="modal" data-target="#exampleFormModal"><i class="fa fa-trash-o fa-fw"></i>删除</a>
            """.format(obj_id=obj.id)

            result_data["data"].append([index, username, obj.role.name, status, obj.balance, obj.xie_wenda_money, obj.fa_wenda_money, create_date, last_login_date, oper])

        return HttpResponse(json.dumps(result_data))

    if "_pjax" in request.GET:
        return render(request, 'myadmin/user_management/user_management_pjax.html', locals())
    return render(request, 'myadmin/user_management/user_management.html', locals())


@pub.is_login
def user_management_oper(request, oper_type, o_id):
    user_id = request.session["user_id"]
    response = pub.BaseResponse()

    if request.method == "POST":
        # 添加
        if oper_type == "create":

            response.status = True
            response.message = "添加成功"
            username = request.POST.get('username')
            xiaoshou_id = request.POST.get('xiaoshou_id')
            print('username ,xiaoshou_id - -- ->',username ,xiaoshou_id)

            form_obj = user.UserProfileCreateForm(request.POST)
            if form_obj.is_valid():
                form_obj.cleaned_data["oper_user_id"] = user_id
                user_obj = models.UserProfile.objects.create(**form_obj.cleaned_data)
                models.YingXiaoGuWen_DuiJie.objects.create(
                    kehu_username_id=user_obj.id,
                    market=user_obj.xiaoshou
                )
            else:
                response.status = False
                for i in ["username", "password", "role_id", "guwen_id", "xiaoshou_id"]:
                    if i in form_obj.errors:
                        response.message = form_obj.errors[i]
                        break

        # 修改
        elif oper_type == "update":
            response.status = True
            response.message = "修改成功"
            print(request.POST.get("id"))

            shouyi_role_ids = [8, 9, 6]
            uid = request.POST.get("id")
            role_id = models.UserProfile.objects.select_related('role').get(id=uid).role.id

            post_data = {}
            for k, v in dict(request.POST).items():
                post_data[k] = v[0]

            print(post_data)
            if role_id not in shouyi_role_ids:
                post_data["xie_wenda_money"] = ''
                post_data["fa_wenda_money"] = ''

            if role_id != 5:
                post_data["map_search_keywords"] = ''
                post_data["map_match_keywords"] = ''

            form_obj = user.UserProfileUpdateForm(post_data)

            if form_obj.is_valid():
                if not form_obj.cleaned_data["password"]:
                    del form_obj.cleaned_data["password"]

                print(form_obj.cleaned_data)
                department_id = request.POST.get('department_id')
                if department_id:
                    models.HospitalInformation.objects.filter(user_id=o_id).update(department_id=department_id)

                print(form_obj.cleaned_data)
                models.UserProfile.objects.filter(id=request.POST.get("id")).update(**form_obj.cleaned_data)
            else:
                response.status = False
                print(form_obj.errors)
                for i in ["username", "password", "role_id", "guwen_id", "xiaoshou_id", "xie_wenda_money", "fa_wenda_money"]:
                    if i in form_obj.errors:
                        response.message = form_obj.errors[i]
                        break

        # 删除用户
        elif oper_type == "delete":
            user_profile_obj = models.UserProfile.objects.get(id=o_id)
            user_profile_obj.is_delete = True
            user_profile_obj.save()

            response.status = True
            response.message = "删除成功"

        # 充值
        elif oper_type == "recharge":
            balance = request.POST.get("balance")
            zbalance = request.POST.get("zbalance")
            remark = request.POST.get("remark")

            if not balance or not balance.lstrip('-').isdigit():
                response.status = False
                response.message = "充值金额有误"

            if zbalance and not zbalance.lstrip('-').isdigit():
                response.status = False
                response.message = "赠送金额有误"

            elif not zbalance:
                zbalance = 0
            else:
                zbalance = int(zbalance)

            if response.status:
                sum_moeny = int(balance) + int(zbalance)
                user_profile_obj = models.UserProfile.objects.select_related("oper_user").get(id=o_id)
                # .update(balance=F("balance") + int(balance))
                user_profile_obj.balance += sum_moeny
                user_profile_obj.save()

                models.BalanceDetail.objects.create(
                    user_id=o_id,
                    account_type=1,
                    money=sum_moeny,
                    balance=balance,
                    zbalance=zbalance,
                    oper_user_id=user_id,
                    remark=remark
                )

                message = "【充值】{username} 为您充值 {moeny} 问答币 ".format(
                    username=models.UserProfile.objects.get(id=user_id).username,
                    moeny=sum_moeny
                )

                AddMessage(request, user_profile_obj.id, message)

                response.status = True
                response.message = "充值成功"

        return JsonResponse(response.__dict__)

    else:
        roles_dict = models.Role.objects.all().values("id", "name")

        # 添加用户
        if oper_type == "create":
            guwen_objs = models.UserProfile.objects.filter(role_id=7, is_delete=False)
            xiaoshou_objs = models.UserProfile.objects.filter(role_id=12, is_delete=False)

            return render(request, 'myadmin/user_management/user_management_modal_create.html', locals())

        # 修改用户
        elif oper_type == "update":
            user_profile_obj = models.UserProfile.objects.select_related("role").get(id=o_id)
            guwen_objs = models.UserProfile.objects.filter(role_id=7, is_delete=False)
            xiaoshou_objs = models.UserProfile.objects.filter(role_id=12, is_delete=False)

            # 问答编辑、问答渠道、兼职发帖角色的id
            print(user_profile_obj.role.id)
            shouyi_role_ids = [8, 9, 6]

            department_objs = models.Department.objects.all()
            hospital_infomation_objs = models.HospitalInformation.objects.filter(user_id=o_id)
            if hospital_infomation_objs:
                hospital_infomation_obj = hospital_infomation_objs[0]

            return render(request, 'myadmin/user_management/user_management_modal_update.html', locals())

        # 删除用户
        elif oper_type == "delete":
            user_profile_obj = models.UserProfile.objects.get(id=o_id)
            return render(request, 'myadmin/user_management/user_management_modal_delete.html', locals())

        # 充值
        elif oper_type == "recharge":
            return render(request, 'myadmin/user_management/user_management_modal_recharge.html', locals())
