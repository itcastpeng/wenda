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
from webadmin.forms.form_cover_update_jifei import jifeiupdateForm
from django.db.models import F
from django.db.models import Q
from webadmin.views_dir.wenda.message import AddMessage
from django.db.models import Count,Sum
import os
import time
from wenda_celery_project import tasks
import datetime


# 顾问对接
@pub.is_login
def guwen_duijie(request):
    role_names = models.Role.objects.values_list("id", "name")
    status_choices = models.UserProfile.status_choices
    if "type" in request.GET and request.GET["type"] == "ajax_json":
        length = int(request.GET.get("length"))
        start = int(request.GET.get("start"))

        # 排序
        column_list = [ "id", "market__xiaoshou", "bianji", "kehu_username__username", "shiji_daozhang", "fugai_count",
                       "jifeishijian_start", "jifeishijian_stop"]
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
                if field in ["status"]:
                    q.add(Q(**{field: request.GET[field]}), Q.AND)
                elif field == "role_names":
                    print(request.GET[field])
                    q.add(Q(**{"role_id": request.GET[field]}), Q.AND)
                else:
                    q.add(Q(**{field + "__contains": request.GET[field]}), Q.AND)

        user_profile_objs = models.YingXiaoGuWen_DuiJie.objects.select_related("market","kehu_username").filter(kehu_username__is_delete=False).filter(
            q).order_by(order_column)

        print('user = = => ',user_profile_objs)

        result_data = {
            "recordsTotal": user_profile_objs.count(),
            "data": []
        }

        for index, obj in enumerate(user_profile_objs[start: (start + length)], start=1):
            bianji = obj.bianji.username
            xiaoshou = obj.market.username
            daozhang = obj.shiji_daozhang
            kehu_name = obj.kehu_username.username
            fugai = obj.fugai_count
            user_id = obj.id
            kaishi_jifei = obj.jifeishijian_start.strftime('%Y-%m-%d')
            tingbiao = obj.jifeishijian_stop.strftime('%Y-%m-%d')

            print('asdhjksankljf ',bianji , xiaoshou, daozhang, kehu_name, fugai,kaishi_jifei,tingbiao)
            oper = ''
            oper += "<a href='beizhu_botton/{user_id}/' data-toggle='modal' data-target='#exampleFormModal'>备注</a>".format(
                user_id=user_id)
            oper += "----<a href='outer_update/{user_id}/' data-toggle='modal' data-target='#exampleFormModal'>修改</a>".format(user_id=user_id)
            oper += "----<a href='outer_delete/{user_id}/' data-toggle='modal' data-target='#exampleFormModal'>删除</a>".format(user_id=user_id)



            result_data["data"].append(
                [index,user_id, kehu_name, xiaoshou, bianji, daozhang, fugai,kaishi_jifei,tingbiao, oper ,1])

        return HttpResponse(json.dumps(result_data))
    if "_pjax" in request.GET:
        return render(request, 'wenda/guwen_Docking_table/guwen_duijie_biao_pjax.html', locals())
    return render(request, 'wenda/guwen_Docking_table/guwen_duijie_biao.html', locals())


@pub.is_login
def guwen_duijie_oper(request, oper_type, o_id):
    role_id = request.session.get("role_id")
    response = pub.BaseResponse()
    print('user',o_id)
    if request.method == "POST":
        # 外层添加
        if oper_type == "outer_create":
            data_temp = {}
            q = Q()
            yonghuming_id = request.POST.get('yonghuming')
            xiaoshou_id = request.POST.get('xiaoshou')
            bianji_id = request.POST.get('bianji')
            daozhang = request.POST.get('daozhang')
            fugailiang = request.POST.get('fugailiang')
            start_time = request.POST.get('start_time')
            stop_time = request.POST.get('stop_time')
            print('--',yonghuming_id,xiaoshou_id,bianji_id,daozhang,fugailiang,start_time,stop_time)
            q.add(Q(xiaoshou_id=xiaoshou_id)|Q(id=yonghuming_id),Q.AND)
            objs =  models.UserProfile.objects.filter(q)
            if objs:
                obj = models.YingXiaoGuWen_DuiJie.objects.filter(kehu_username_id=yonghuming_id)
                if obj:
                    obj.update(
                        kehu_username_id=yonghuming_id,  # 客户名
                        market_id=xiaoshou_id,  # 销售
                        shiji_daozhang=daozhang,  # 实际到账
                        fugai_count=fugailiang,  # 覆盖总数
                        jifeishijian_start=start_time,  # 计费开始
                        jifeishijian_stop=stop_time,  # 结束计费
                        bianji_id=bianji_id  # 编辑
                    )
                else:
                    models.YingXiaoGuWen_DuiJie.objects.create(
                        market_id=xiaoshou_id,              # 销售
                        kehu_username_id=yonghuming_id,       # 客户名
                        shiji_daozhang=daozhang,        # 实际到账
                        fugai_count=fugailiang,         # 覆盖总数
                        jifeishijian_start=start_time,  # 计费开始
                        jifeishijian_stop=stop_time,    # 结束计费
                        bianji_id=bianji_id             # 编辑
                    )
            response.message = "添加成功"

        # 备注
        elif oper_type =='beizhuy_oper':
            panduan_xinwenda = request.POST.get('panduan_xinwenda')
            xuanchuan = request.POST.get('xuanchuanyaoqiu')
            shangwutong = request.POST.get('shangwutong')
            wendageshu = request.POST.get('wendageshu')
            obj = models.YingXiaoGuWen_DuiJie.objects.filter(id=o_id)
            if obj:
                if panduan_xinwenda and wendageshu:
                    obj.update(
                        shangwutong=shangwutong,
                        xuanchuanyaoqiu=xuanchuan,
                        wenda_geshu=wendageshu,
                        xinwenda=True,
                    )
                else:
                    obj.update(
                        shangwutong=shangwutong,
                        xuanchuanyaoqiu=xuanchuan,
                        xinwenda=False,
                    )

                response.message = '备注成功'
            else:
                response.message = '用户错误    '

        # 外层修改
        elif oper_type == 'outer_update':
            yonghuming_id = request.POST.get('yonghuming')
            xiaoshou_id = request.POST.get('xiaoshou')
            bianji_id = request.POST.get('bianji')
            daozhang = request.POST.get('daozhang')
            fugailiang = request.POST.get('fugailiang')
            start_time = request.POST.get('start_time')
            stop_time = request.POST.get('stop_time')
            print('=================', yonghuming_id, xiaoshou_id, bianji_id, daozhang, fugailiang, start_time, stop_time)



        return JsonResponse(response.__dict__)

    else:

        pass
        # 外层添加
        if oper_type == "outer_create":
            client_objs = models.UserProfile.objects.filter(is_delete=False, role_id=5)
            xiaoshous = models.UserProfile.objects.filter(role_id=12)
            bianjis = models.UserProfile.objects.filter(role_id=6)
            return render(request, 'wenda/guwen_Docking_table/guwen_outer_create.html', locals())

        # 备注按钮
        elif oper_type == 'beizhu_botton':
            return render(request, 'wenda/guwen_Docking_table/guwen_beizhu_button.html', locals())
        # 外层修改
        elif oper_type == 'outer_update':
            obj = models.YingXiaoGuWen_DuiJie.objects.filter(id=o_id)
            if obj:
                bianjiming = obj[0].bianji.username
                xiaoshouming = obj[0].market
                shangwutong = obj[0].shangwutong
                jifeishijian_start = obj[0].jifeishijian_start.strftime('%Y-%m-%d')
                jifeishijian_stop = obj[0].jifeishijian_stop.strftime('%Y-%m-%d')
                daozhang = obj[0].shiji_daozhang
                fugai = obj[0].fugai_count
                xuanchuan = obj[0].xuanchuanyaoqiu
                wendageshu = obj[0].wenda_geshu
                panduan_xinwenda = obj[0].xinwenda
                xiaoshous = models.UserProfile.objects.filter(role_id=12)
                bianjis = models.UserProfile.objects.filter(role_id=6)
            return render(request,'wenda/guwen_Docking_table/guwen_outer_update.html',locals())

        # 外层删除
        elif oper_type == 'outer_delete':
            o_id = o_id
            return render(request,'wenda/guwen_Docking_table/guwen_outer_delete.html',locals())




