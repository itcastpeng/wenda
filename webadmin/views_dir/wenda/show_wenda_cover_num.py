#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author:zhangcong
# Email:zc_92@sina.com


from django.shortcuts import render, HttpResponse
from webadmin.views_dir import pub

from webadmin import models
from django.http import JsonResponse

import json

from django.db.models import Q
from django.db.models import Count
import os
import time
from wenda_celery_project import tasks
import datetime


# 覆盖报表(公众号)
def show_wenda_cover_num(request, openid):
    print("show_wenda_cover_num")
    obj = models.UserProfile.objects.get(openid=openid)

    role_id = obj.role.id
    user_id = obj.id

    result_data = {
        "role_id": role_id
    }
    # 客户
    filter_dict = {}
    if role_id == 5:    # 客户角色
        filter_dict["keywords__client_user"] = user_id
        keywords_top_set_obj = models.KeywordsTopSet.objects.filter(client_user=user_id)
        total_cover_num = models.KeywordsCover.objects.filter(keywords__client_user=user_id).count()
        result_data["total_cover_num"] = total_cover_num    # 总覆盖数
        result_data["total_keywords_num"] = keywords_top_set_obj.count()    # 总关键词数

        data_objs = models.UserprofileKeywordsCover.objects.filter(
            client_user_id=user_id
        ).order_by('-create_date')

        table_data = []
        for index, obj in enumerate(data_objs, start=1):
            date_format = obj.create_date.strftime("%Y-%m-%d")
            table_data.append({
                "index": index,
                "date_format": date_format,
                "cover_num": obj.cover_num,
                "statement_path": "/" + obj.statement_path
            })

        result_data["table_data"] = table_data

    elif role_id in [1, 4]:     # 管理员或超级管理员

        data_objs = models.KeywordsCover.objects.select_related(
            "keywords__client_user",
            "keywords"
        ).filter(**filter_dict).values("keywords__client_user__username", "keywords__client_user_id").annotate(
            Count('keywords'))

        result_data = []
        for index, obj in enumerate(data_objs, start=1):

            keywords_topset_obj = models.KeywordsTopSet.objects.filter(
                client_user_id=obj["keywords__client_user_id"],
                is_delete=False
            )
            keyword_count = keywords_topset_obj.count()  # 关键词总数

            now_date = datetime.datetime.now().strftime("%Y-%m-%d")
            q = Q(Q(update_select_cover_date__isnull=True) | Q(update_select_cover_date__lt=now_date))
            keyword_select_count = keywords_topset_obj.filter(q).count()  # 未查询的关键词数

            if keyword_select_count > 0:
                keyword_count_str = "%s / %s" % (keyword_count, keyword_select_count)
                select_status = "查询中"
            else:
                keyword_count_str = keyword_count
                select_status = "查询完成"

            oper = ""
            result_data.append(
                {
                    "index": index,
                    "id": obj["keywords__client_user_id"],
                    "username": obj["keywords__client_user__username"],
                    "cover_total": obj["keywords__count"],
                    "select_status": select_status,
                    "keyword_count": keyword_count_str,
                    "oper": oper,
                }
            )
    result_data = json.dumps(result_data)
    print(result_data)
    return render(request, 'wenda/show_wenda_cover_num/show_wenda_cover_num.html', locals())


def show_wenda_cover_num_oper(request, openid, date):
    print("show_wenda_cover_num_oper")

    obj = models.UserProfile.objects.get(openid=openid)
    user_id = obj.id

    objs = models.KeywordsCover.objects.select_related('keywords').filter(
        keywords__client_user=user_id,
        create_date__year=date.split("-")[0],
        create_date__month=date.split("-")[1],
        create_date__day=date.split("-")[2]
    )
    table_data = []
    for index, obj in enumerate(objs, start=1):
        table_data.append({
            "index": index,
            "keywords": obj.keywords.keyword,
            "page_type": obj.get_page_type_display(),
            "rank": obj.rank,
            "url": obj.url,
        })

    result_data = {
        "date": date,
        "total_cover": objs.count(),
        "table_data": table_data
    }

    result_data = json.dumps(result_data)

    return render(request, 'wenda/show_wenda_cover_num/show_wenda_cover_num_oper.html', locals())







