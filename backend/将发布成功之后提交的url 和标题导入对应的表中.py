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
import datetime
import xlrd

from django.db.utils import IntegrityError


task_objs = models.Task.objects.select_related('publish_user').filter(
    is_delete=False,
    is_check=False,
    status=7,
    release_user__is_delete=False,
    publish_user__isnull=False,
    publish_task_result_file_path__isnull=False,
)
print(task_objs.count())
for obj in task_objs:
    # 先清空该任务在回链表中的所有链接
    models.WendaLink.objects.filter(task=obj).delete()

    # 将提交的 excel 表格中的数据读出
    print(obj.name)
    book = xlrd.open_workbook(os.path.join(project_dir, obj.publish_task_result_file_path))
    sh = book.sheet_by_index(0)

    query = []

    for row in range(2, sh.nrows):
        url = sh.cell_value(rowx=row, colx=0)
        keywords = sh.cell_value(rowx=row, colx=1)

        wenda_link_objs = models.WendaLink.objects.filter(url=url)
        if wenda_link_objs.count() == 0:  # 如果该链接已经存在,则跳过
            query.append(
                models.WendaLink(
                    task=obj,
                    url=url,
                    check_date=datetime.datetime.now() + datetime.timedelta(days=3),
                )
            )
        try:
            models.SearchKeywordsRank.objects.create(
                client_user_id=obj.release_user.id,
                task=obj,
                keywords=keywords,
                type=2,
                oper_user_id=8
            )
        except IntegrityError:
            continue

    models.WendaLink.objects.bulk_create(query)
    obj.is_check = True
    obj.save()

