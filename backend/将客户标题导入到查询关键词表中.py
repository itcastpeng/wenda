#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author:zhangcong
# Email:zc_92@sina.com


import os
import sys

project_dir = os.path.dirname(os.getcwd())

sys.path.append(project_dir)

os.environ['DJANGO_SETTINGS_MODULE'] ='wenda.settings'
import django
django.setup()

from webadmin import models

import xlrd
import datetime

task_obj = models.Task.objects.filter(
    release_user__is_delete=False,
    is_delete=False,
    release_platform=1,
    publish_task_result_file_path__isnull=False,
).exclude(
    status=11,
)
for obj in task_obj:
    # if obj.release_user_id == 51:
    keywords_count = models.SearchKeywordsRank.objects.filter(task=obj).count()
    link_count = models.WendaLink.objects.filter(task=obj).count()
    print(obj.id, obj.release_user.username, keywords_count, link_count)
    continue
    if obj.release_user_id == 48:
        continue
    if obj.publish_task_result_file_path:
        if link_count == 0:

            print(obj.publish_task_result_file_path)

            file_path = os.path.join(project_dir, obj.publish_task_result_file_path)
            book = xlrd.open_workbook(filename=file_path)
            sh = book.sheet_by_index(0)

            for row in range(2, sh.nrows):
                link = sh.cell_value(rowx=row, colx=0)
                # title = sh.cell_value(rowx=row, colx=1)
                # content = sh.cell_value(rowx=row, colx=2)
                print(link)
                # continue
                models.WendaLink.objects.create(
                    task=obj,
                    url=link,
                    status=10,
                    # check_date=datetime.datetime(2018, 1, 11, 7, 42, 52)
                )

        continue
    else:
        continue
    if models.SearchKeywordsRank.objects.filter(task=obj).count() > 0:  # 如果已经存在,则跳过
        continue

    if not obj.publish_task_result_file_path:
        continue

    print(obj.id, obj.name, obj.is_delete, obj.publish_task_result_file_path)

    # 从excel 表格中读取数据
    filename = os.path.join(project_dir, obj.publish_task_result_file_path)

    # 如果文件不存在,则跳过当次任务
    if not os.path.exists(filename):
        continue
    print(filename)
    book = xlrd.open_workbook(filename=filename)
    sh = book.sheet_by_index(0)

    query = []
    for row in range(2, sh.nrows):
        title = sh.cell_value(rowx=row, colx=1)
        if title.startswith("http"):
            title = sh.cell_value(rowx=row, colx=0).rstrip("_百度知道")

            if title.startswith("http"):
                print("失败: ", obj.name)
                print(sh.cell_value(rowx=row, colx=0))
                exit()

        s_obj = models.SearchKeywordsRank.objects.filter(
            client_user_id=obj.release_user.id,
            keywords=title,
        )
        if not s_obj:

            models.SearchKeywordsRank.objects.create(
                task=obj,
                client_user_id=obj.release_user.id,
                keywords=title,
                type=2,
                oper_user_id=2
            )


