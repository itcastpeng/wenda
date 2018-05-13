#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author:zhangcong
# Email:zc_92@sina.com


from django.shortcuts import render, HttpResponse
from webadmin.views_dir import pub

from webadmin import models
from django.http import JsonResponse

from webadmin.forms.task_list import TaskListCreateForm, TaskListUpdateForm
import json
import datetime
from django.db.models import F
from django.db.models import Q
from django.db.models import Sum


# 任务管理
@pub.is_login
def bianxiebaobiao(request):
    user_id = request.session["user_id"]

    if "type" in request.GET and request.GET["type"] == "ajax_json":
        start_time = request.GET.get('start_time')
        stop_time = request.GET.get('stop_time')
        xuantian = request.GET.get('xuantian')
        # print('start--stop -->',start_time,stop_time)
        # print('request-->',request.GET)

        column_list = ['id', 'xiangmu', 'oper_user_id', 'create_date', 'edit_count','oper','start_time','stop_time','xuantian']
        q = Q()
        for index, field in enumerate(column_list):
            if field in request.GET and request.GET[field]:     # 如果该字段存在并且不为空
                # 起始时间和结束时间
                if field == 'start_time':
                    q.add(Q(**{"create_date__gte": request.GET[field]}), Q.AND)
                elif field == 'stop_time':
                    q.add(Q(**{"create_date__lt": request.GET[field]}), Q.AND)
                # 天数查询
                elif field == 'xuantian':

                    if xuantian == '1':
                        start_time = datetime.datetime.today().strftime('%Y-%m-%d')
                        stop_time = datetime.datetime.today().strftime('%Y-%m-%d')

                    elif xuantian == '2':
                        start_time = (datetime.date.today() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
                        stop_time = (datetime.date.today() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')

                    elif xuantian == '3':
                        start_time = (datetime.date.today() - datetime.timedelta(days=7)).strftime('%Y-%m-%d')
                        stop_time = datetime.datetime.now().strftime('%Y-%m-%d')

                    elif xuantian == '4':
                        start_time = (datetime.date.today() - datetime.timedelta(days=30)).strftime('%Y-%m-%d')
                        stop_time = datetime.datetime.now().strftime('%Y-%m-%d')
                    q.add(Q(**{"create_date__gte": start_time}), Q.AND)
                    q.add(Q(**{"create_date__lte": stop_time}), Q.AND)
                else:
                    q.add(Q(**{field + "__contains": request.GET[field]}), Q.AND)
        print('q-->',q)
        task_list_objs = models.BianXieBaoBiao.objects.filter(q)
        print('task_count---:>', task_list_objs.count())


        result_data = {
            "recordsFiltered": task_list_objs.count(),
            "option": []
        }
        # user_data = models.UserProfile.objects.filter(is_delete=False, role_id__in=[6, 7]).values_list('username')
        user_data = models.UserProfile.objects.filter(is_delete=False).values_list('username')
        user_data = [i[0] for i in user_data]

        xiangmu_data = ["总数据"]
        xiangmu_data.extend([i[1] for i in models.BianXieBaoBiao.xiangmu_choices])
        series_data = []
        objs = task_list_objs.values('xiangmu','oper_user__username').annotate(Sum('edit_count'))
        temp_dict = {}
        for obj in objs:
            username = obj['oper_user__username']
            xiangmu = obj['xiangmu']
            count = obj['edit_count__sum']

            if username not in temp_dict:
                temp_dict[username] = [0] * 7
            # 项目为索引 哪个项目就是第几个元素
            temp_dict[username][xiangmu] = count

        for k,v in temp_dict.items():
            v[0] = sum(v)
            series_data.append({
                    'data': v,
                    'type': 'line',
                    'smooth': True,
                    'name': k
            })


        print('进入的数据----->',series_data)
        option = {
            'xAxis': {
                'type': 'category',
                'data': xiangmu_data
            },
            'yAxis': {
                'type': 'value'
            },

            'title': {
                'title': '编辑编写量统计图'
            },
            'tooltip': {
                'trigger': 'axis'
            },
            'grid': {
                'left': '3%',
                'right': '4%',
                'bottom': '3%',
                'containLabel': True
            },

            'legend': {
                'data': user_data
            },
            'series': series_data,

        }

        result_data['option'] = option

        # for index, obj in enumerate(task_list_objs[start: (start + length)], start=1):
        #
        #     if obj.create_at:
        #         create_date = obj.create_at.strftime("%Y-%m-%d %H:%M:%S")
        #     else:
        #         create_date = ""
        #
        #     if obj.update_at:
        #         update_at = obj.update_at.strftime("%Y-%m-%d %H:%M:%S")
        #     else:
        #         update_at = ""
        #
        #     status = ""
        #     for i in status_choices:
        #         if i[0] == obj.status:
        #             status = i[1]
        #             break
        #
        #     search_engine = ""
        #     for i in search_engine_choices:
        #         if i[0] == obj.search_engine:
        #             search_engine = i[1]
        #             break
        #
        #     # 排名变化
        #     ranking_change = ""
        #
        #     # 成功点击数
        #     success_click_numbers = ""
        #
        #     oper = ""
        #
        #     if obj.status == 1:     # 当前状态显示在线
        #         oper += """<a class="btn btn-round btn-sm bg-warning" aria-hidden="true" href="offline/{obj_id}/" data-toggle="modal" data-target="#exampleFormModal"><i class="icon fa-cloud-download" aria-hidden="true"></i>下线</a>"""
        #
        #     else:   # 当前状态显示离线
        #         oper += """<a class="btn btn-round btn-sm bg-success" aria-hidden="true" href="online/{obj_id}/" data-toggle="modal" data-target="#exampleFormModal"><i class="icon fa-cloud-upload" aria-hidden="true"></i>上线</a>"""
        #
        #     oper += """
        #         <a class="btn btn-round btn-sm bg-primary" aria-hidden="true" href="update/{obj_id}/" data-toggle="modal" data-target="#modal-width-700"><i class="icon fa-pencil-square-o"></i>修改</a>
        #         <a class="btn btn-round btn-sm bg-danger" aria-hidden="true" href="delete/{obj_id}/" data-toggle="modal" data-target="#exampleFormModal"><i class="fa fa-trash-o fa-fw"></i>删除</a>
        #     """
        #
        #     if user_obj.role.id in admin_role_list:
        #         oper += """<a class="btn btn-round btn-sm bg-info" aria-hidden="true" href="update/{obj_id}/" data-toggle="modal" data-target="#modal-width-700"><i class="icon fa-search" aria-hidden="true"></i>详情</a>"""
        #
        #     oper=oper.format(obj_id=obj.id)
        #
        #     # 管理员看到的字段和普通员工看到的字段不一样
        #     if user_obj.role.id in admin_role_list:
        #         table_data = [index, obj.keywords, obj.url, search_engine, obj.first_ranking, obj.now_ranking, ranking_change, obj.day_click_number, success_click_numbers, create_date, update_at, status, oper]
        #     else:
        #         table_data = [index, obj.keywords, obj.url, search_engine, obj.first_ranking, obj.now_ranking, ranking_change, create_date, status, oper]
        #     result_data["data"].append(table_data)

        print('result_data -->', json.dumps(result_data))
        return HttpResponse(json.dumps(result_data))

    if "_pjax" in request.GET:
        return render(request, '../../wenda/templates/wenda/bianxiebaobiao/bianxiebaobiao_pjax.html', locals())
    return render(request, '../../wenda/templates/wenda/bianxiebaobiao/bianxiebaobiao.html', locals())



