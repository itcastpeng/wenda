#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author:zhangcong
# Email:zc_92@sina.com


import sys
import os

# project_dir 是
project_dir = os.path.dirname(os.getcwd())
sys.path.append(project_dir)

print(project_dir)
os.environ['DJANGO_SETTINGS_MODULE'] ='wenda.settings'
import django
django.setup()

from webadmin import models
import datetime
import xlrd


task_objs = models.Task.objects.filter(
    is_delete=False,
    is_check=False,
    status__gte=6,
    release_user__is_delete=False,
    publish_task_result_file_path__isnull=False
).exclude(status=11)

for obj in task_objs:
    print(obj.id, obj.name)
    file_name = os.path.join(project_dir, obj.publish_task_result_file_path)
    book = xlrd.open_workbook(file_name)
    sh = book.sheet_by_index(0)

    query = []

    for row in range(2, sh.nrows):
        url = sh.cell_value(rowx=row, colx=1)

        wenda_link_objs = models.WendaLink.objects.filter(url=url)
        if wenda_link_objs.count() > 0:  # 如果该链接已经存在,则跳过
            continue

        query.append(
            models.WendaLink(
                task=obj,
                url=url,
                check_date=datetime.datetime.now() - datetime.timedelta(days=3),
            )
        )

    models.WendaLink.objects.bulk_create(query)
    obj.is_check = True
    obj.save()

