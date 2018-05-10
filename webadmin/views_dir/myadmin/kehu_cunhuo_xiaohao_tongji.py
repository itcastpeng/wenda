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


# 客户存活消耗统计
@pub.is_login
def kehu_cunhuo_xiaohao_tongji(request):

    role_names = models.Role.objects.values_list("id", "name")
    status_choices = models.UserProfile.status_choices

    if "type" in request.GET and request.GET["type"] == "ajax_json":
        length = int(request.GET.get("length"))
        start = int(request.GET.get("start"))

        # 排序
        column_list = ["id", "client_id", "hezuo_num", "shengyu_num", "create_date", "remark", "oper_user_id", "oper", "client__username"]
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
                if field == "client__username":
                    q.add(Q(**{field + "__contains": request.GET[field]}), Q.AND)
                else:
                    q.add(Q(**{field: request.GET[field]}), Q.AND)

        data_objs = models.KehuCunhuoXiaohaoTongji.objects.select_related("client", 'oper_user').filter(q).order_by(order_column)

        result_data = {
            "recordsFiltered": data_objs.count(),
            "recordsTotal": data_objs.count(),
            "data": []
        }

        status_choices = models.UserProfile.status_choices

        for index, obj in enumerate(data_objs[start: (start + length)], start=1):

            if obj.create_date:
                create_date = obj.create_date.strftime("%Y-%m-%d %H:%M:%S")
            else:
                create_date = ""

            oper = """
                <a class="btn btn-round btn-sm bg-success" aria-hidden="true" href="add_child/{obj_id}/" data-toggle="modal" data-target="#exampleFormModal"><i class="icon wb-plus" aria-hidden="true"></i>添加子项</a>
                <a class="btn btn-round btn-sm bg-primary" aria-hidden="true" href="search_detail/{obj_id}/" data-toggle="modal" data-target="#exampleFormModal"><i class="icon wb-search" aria-hidden="true"></i>查看详情</a>
                <a class="btn btn-round btn-sm bg-danger" aria-hidden="true" href="delete/{obj_id}/" data-toggle="modal" data-target="#exampleFormModal"><i class="icon fa-remove" aria-hidden="true"></i>删除</a>
            """.format(obj_id=obj.id)

            result_data["data"].append([index, obj.client.username, obj.hezuo_num, obj.shengyu_num, create_date, obj.remark, obj.oper_user.username, oper])

        return HttpResponse(json.dumps(result_data))

    client_obj = models.UserProfile.objects.filter(is_delete=False, role_id=5)
    if "_pjax" in request.GET:
        return render(request, 'myadmin/kehu_cunhuo_xiaohao_tongji/kehu_cunhuo_xiaohao_tongji_pjax.html', locals())
    return render(request, 'myadmin/kehu_cunhuo_xiaohao_tongji/kehu_cunhuo_xiaohao_tongji.html', locals())


@pub.is_login
def kehu_cunhuo_xiaohao_tongji_oper(request, oper_type, o_id):
    user_id = request.session["user_id"]
    response = pub.BaseResponse()

    if request.method == "POST":
        # 添加
        if oper_type == "create":
            client_id = request.POST.get("client_id")
            hezuo_num = request.POST.get("hezuo_num")
            remark = request.POST.get("remark")

            if not client_id:
                response.status = False
                response.message = "请选择用户"

            if response.status and (not hezuo_num or not hezuo_num.isdigit()):
                response.status = False
                response.message = "合作数量格式不对"

            if response.status:
                models.KehuCunhuoXiaohaoTongji.objects.create(
                    client_id=client_id,
                    hezuo_num=hezuo_num,
                    shengyu_num=hezuo_num,
                    oper_user_id=user_id,
                    remark=remark
                )

                response.status = True
                response.message = "添加成功"

        # 添加子项
        elif oper_type == "add_child":
            fabu_num = request.POST.get("fabu_num")
            jifei_num = request.POST.get("jifei_num")
            remark = request.POST.get("remark")

            if not fabu_num or not fabu_num.isdigit():
                response.status = False
                response.message = "发布数量格式不对"

            if response.status and (not jifei_num or not jifei_num.isdigit()):
                response.status = False
                response.message = "计费数量格式不对"

            if response.status:
                fabu_num = int(fabu_num)
                jifei_num = int(jifei_num)
                obj = models.KehuCunhuoXiaohaoTongji.objects.get(id=o_id)
                obj.shengyu_num -= jifei_num
                obj.save()

                models.KehuCunhuoXiaohaoTongjiInfo.objects.create(
                    kehu_cunhuo_xiaohao_tongji=obj,
                    fabu_num=fabu_num,
                    jifei_num=jifei_num,
                    oper_user_id=user_id,
                    remark=remark
                )

                response.status = True
                response.message = "添加成功"

        elif oper_type == "delete":
            models.KehuCunhuoXiaohaoTongji.objects.filter(id=o_id).delete()
            response.status = True
            response.message = "删除成功"

        return JsonResponse(response.__dict__)
    else:
        client_obj = models.UserProfile.objects.filter(role_id=5, is_delete=False)
        # 添加
        if oper_type == "create":
            return render(request, 'myadmin/kehu_cunhuo_xiaohao_tongji/kehu_cunhuo_xiaohao_tongji_modal_create.html', locals())

        # 添加子项
        elif oper_type == "add_child":
            client_username = models.KehuCunhuoXiaohaoTongji.objects.select_related('client').get(id=o_id).client.username
            return render(request, 'myadmin/kehu_cunhuo_xiaohao_tongji/kehu_cunhuo_xiaohao_tongji_modal_add_child.html', locals())

        # 查看详情
        elif oper_type == "search_detail":
            obj = models.KehuCunhuoXiaohaoTongji.objects.select_related('client').get(id=o_id)
            info_objs = obj.kehucunhuoxiaohaotongjiinfo_set.select_related('oper_user').all()
            return render(request, 'myadmin/kehu_cunhuo_xiaohao_tongji/kehu_cunhuo_xiaohao_tongji_modal_search_detail.html', locals())

        # 删除
        elif oper_type == "delete":
            obj = models.KehuCunhuoXiaohaoTongji.objects.select_related('client').get(id=o_id)
            return render(request, 'myadmin/kehu_cunhuo_xiaohao_tongji/kehu_cunhuo_xiaohao_tongji_modal_delete.html', locals())
