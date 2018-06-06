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

    if "type" in request.GET and request.GET["type"] == "ajax_json":
        client_user = request.GET.get('client_user')
        # print('client_user ---------- >',client_user)
        result_data={'data':[]}
        objs = models.GuanJianCiFifty.objects.filter(yonghu_user=client_user)
        # print('objs - - - -- 》 ',objs )
        for index,obj in enumerate(objs):
            oper = ''
            oper += "<a href='update_guanjianci/{user_id}/' data-toggle='modal' data-target='#exampleFormModal'>修改</a>".format(user_id=obj.id)
            oper += "----<a href='delete_guanjianci/{user_id}/' data-toggle='modal' data-target='#exampleFormModal'>删除</a>".format(user_id=obj.id)
            result_data['data'].append({
                'oper':oper,
                'kehu_name':obj.yonghu_user.username,
                'user_id':obj.id,
                'index':index + 1,
                'guanjianci':obj.guanjianci
            })
        # print('result_data  ------ >',result_data['data'])
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
                    # print('查询user成功 = = = = 》')
                    for guanjianci in guanjianci_list:
                        # print('关键词入库 -- -- - - 》',  guanjianci)
                        # print('用户id ------ 》 ',yonghu_id    )
                        models.GuanJianCiFifty.objects.create(
                            guanjianci=guanjianci,
                            yonghu_user=obj[0]
                        )
                    response.status=True
                    response.message='添加成功'

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





