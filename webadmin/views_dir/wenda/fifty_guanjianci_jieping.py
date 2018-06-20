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
from django.db.models import Q ,Count
from webadmin.forms import  guwen_duijie_biao

# 关键词截屏
@pub.is_login
def guanjianci_jieping(request):
    status_choices = models.UserProfile.status_choices
    client_data = models.UserProfile.objects.filter(is_delete=False, role_id=5).values('username', 'id')
    # print('client_data --- -- -<>',client_data)

    if "type" in request.GET and request.GET["type"] == "ajax_json":
        length = int(request.GET.get("length"))
        start = int(request.GET.get("start"))

        column_list = ["id", "yonghu_user_id", "yonghu_user","jieping_time"]
        order_column = request.GET.get('order[0][column]', 1)  # 第几列排序
        order = request.GET.get('order[0][dir]')  # 正序还是倒序
        order_column = column_list[int(order_column)]


        if order == "desc":
            order_column = "-{order_column}".format(order_column=order_column)
        else:
            order_column = order_column
        # print('order = = > ', order)
        # print('order_column = = > ', order_column)
        q = Q()
        for index, field in enumerate(column_list):
            # print('field = =  >', field)
            if field in request.GET and request.GET.get(field):  # 如果该字段存在并且不为空
                if field == 'client_user':
                    print('field ==== client_user')
                    q.add(Q(**{'yonghu_user': request.GET[field]}), Q.AND)
                else:
                    q.add(Q(**{field + "__contains": request.GET[field]}), Q.AND)

        objs = ''
        client_user = request.GET.get('client_user')
        if client_user:
            objs = models.GuanJianCiFifty.objects.filter(q).filter(yonghu_user=client_user).order_by(order_column)
        else:
            objs = models.GuanJianCiFifty.objects.filter(q).all().order_by(order_column)
        result_data = {'data': []}
        result_data = {
            "recordsFiltered": objs.count(),
            "recordsTotal": objs.count(),
            "data": []}
        for index,obj in enumerate(objs[start: (start + length)], start=0):
            oper = ''
            oper += "<a href='guanjianci_jieping/{user_id}/' id='chakan_jieping' data-toggle='modal' data-target='#exampleFormModal'>查看截屏</a>".format(user_id=obj.id)
            oper += "----<a href='update_guanjianci/{user_id}/' data-toggle='modal' data-target='#exampleFormModal'>修改</a>".format(user_id=obj.id)
            oper += "----<a href='delete_guanjianci/{user_id}/' data-toggle='modal' data-target='#exampleFormModal'>删除</a>".format(user_id=obj.id)
            result_data['data'].append({
                'oper':oper,
                'kehu_name':obj.yonghu_user.username,
                'user_id':obj.id,
                'guanjianci':obj.guanjianci,
                'index':index + 1,
            })
        return HttpResponse(json.dumps(result_data))
    if "_pjax" in request.GET:
        return render(request, 'wenda/fifty_guanjianci_jieping/fifty_guanjianci_jieping_pjax.html', locals())
    return render(request, 'wenda/fifty_guanjianci_jieping/fifty_guanjianci_jieping.html', locals())


@pub.is_login
def guanjianci_jieping_oper(request, oper_type, o_id):
    role_id = request.session.get("role_id")
    response = pub.BaseResponse()
    if request.method == "POST":
        # 添加50个关键词
        if oper_type == "create_guanjianci":
            yonghu_id = request.POST.get('yonghuming')
            guanjianci_create = request.POST.get('guanjianci_create')
            print('guanjianci_create =  == = == = >',guanjianci_create )
            guanjianci_list = set(guanjianci_create.splitlines())
            # 数据库查询条数
            objs = models.GuanJianCiFifty.objects.filter(yonghu_user=yonghu_id).values('yonghu_user_id').annotate(Count('id'))
            # 输入的条数
            len_guanjianci = len(guanjianci_list)
            print('输入的条数 - -- - -> ',len_guanjianci )
            if objs:
                print('数据库条数 - -- - -> ',objs[0]['id__count'] )
                print('数据库条数 + 输入的条数 - -- - -> ',objs[0]['id__count'] + len_guanjianci )
                if objs[0]['id__count'] + len_guanjianci > 50:
                    response.status=False
                    response.message='数据库大于50条,请删除部分关键词'
                elif len_guanjianci > 50:
                    response.status=False
                    response.message='关键字超出50条,请检查!'
                else:
                    obj = models.UserProfile.objects.filter(id=yonghu_id)
                    if obj:
                        print('查询user成功 = = = = 》')
                        for guanjianci in guanjianci_list:
                            print('关键词入库 -- -- - - 》',  guanjianci)
                            print('用户id ------ 》 ',yonghu_id    )
                            models.GuanJianCiFifty.objects.create(
                                guanjianci=guanjianci,
                                yonghu_user=obj[0]
                            )
                        response.status=False
                        response.message='添加成功'
            else:
                response.status = False
                response.message = '添加数据异常'

        # 修改关键词
        elif oper_type == 'update_guanjianci':
            guanjianci = request.POST.get('guanjianci')
            print('guanjianci  - -- -  >',guanjianci )
            if guanjianci:
                objs = models.GuanJianCiFifty.objects.filter(id=o_id)
                if objs:
                    objs.update(
                        guanjianci=guanjianci
                    )
                    response.status=True
                    response.message='修改成功'
            else:
                response.status=False
                response.message='修改失败'

        # 删除关键词
        elif oper_type == 'delete_guanjianci':
            print('o_id - - -> ',o_id)
            obj = models.GuanJianCiFifty.objects.get(id=o_id)
            if obj:
                obj.delete()
                response.status = True
                response.message = '删除成功'
            else:
                response.status = False
                response.message = '删除失败'

        # 查看关键词截屏
        elif oper_type == 'guanjianci_jieping':
            pass

        return JsonResponse(response.__dict__)


    else:
        # 添加50个关键词
        if oper_type == "create_guanjianci":
            client_objs = models.UserProfile.objects.filter(is_delete=False, role_id=5)
            return render(request, 'wenda/fifty_guanjianci_jieping/fifty_guanjianci_create.html', locals())

        # 修改关键词
        elif oper_type == 'update_guanjianci':
            client_objs = models.UserProfile.objects.filter(is_delete=False,role_id=5)
            obj = models.GuanJianCiFifty.objects.get(id=o_id)
            guanjianci_name = obj.guanjianci
            guanjianci_id = obj.id
            return render(request, 'wenda/fifty_guanjianci_jieping/fifty_guanjianci_update.html/',locals())

        # 删除关键词
        elif oper_type == 'delete_guanjianci':
            obj = models.GuanJianCiFifty.objects.get(id=o_id)
            guanjianci = obj.guanjianci
            return render(request, 'wenda/fifty_guanjianci_jieping/fifty_guanjianci_delete.html',locals())

        # 查看关键词截屏
        elif oper_type == 'guanjianci_jieping':
            objs = models.GetKeywordsJiePing.objects.filter(guanjianci_id=o_id)
            data_list = []
            for obj in objs:
                picture = obj.picture_path
                print('picture- - -> ', picture)
                data_list.append(picture)
            return render(request,'wenda/fifty_guanjianci_jieping/fifty_guanjianci_jieping_pjax.html',locals())





