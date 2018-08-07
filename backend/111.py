#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author:zhangcong
# Email:zc_92@sina.com

import os
import sys

project_dir = os.path.dirname(os.getcwd())

sys.path.append(project_dir)
print(sys.path)

os.environ['DJANGO_SETTINGS_MODULE'] ='wenda.settings'
import django
django.setup()

from webadmin import models
import datetime
import xlrd


task_objs = models.Task.objects.filter(id__in=[1749, 1748, 1769])  # 状态为发布中,且发布用户为机器人
for obj in task_objs:

    file_path = obj.task_result_file_path
    if not file_path:
        file_path = obj.task_demand_file_path

    # 从excel 表格中读取数据
    filename = os.path.join(project_dir, file_path)
    print(filename)
    book = xlrd.open_workbook(filename=filename)
    sh = book.sheet_by_index(0)

    for row in range(2, sh.nrows):
        url = sh.cell_value(rowx=row, colx=0)
        title = sh.cell_value(rowx=row, colx=1)
        content = sh.cell_value(rowx=row, colx=2)
        img_content = sh.cell_value(rowx=row, colx=3)   # 图片编写内容

        ooo_obj = models.WendaRobotTask.objects.filter(
            task=obj,
            wenda_url=url,
            title=title,
        )
        if ooo_obj:
            continue
        status = 1
        if obj.wenda_type == 2:
            status = 2

        edit_task_management_objs = models.EditTaskManagement.objects.filter(
            task__task=obj,
            edit_user__role_id=14,  # 编辑角色为 外部编辑-商务通渠道
        )
        if edit_task_management_objs:  # 如果编辑角色为外部编辑-商务通渠道,则任务状态直接改为已完成
            status = 6

        wenda_robot_task_obj = models.WendaRobotTask.objects.create(
            task=obj,
            wenda_url=url,
            title=title,
            content=content,
            img_content=img_content,
            release_platform=obj.release_platform,
            wenda_type=obj.wenda_type,
            next_date=datetime.datetime.now() + datetime.timedelta(minutes=30),
            status=status,
            add_map=obj.add_map
        )
        try:
            t_id = sh.cell_value(rowx=row, colx=4)
            edit_publick_task_management_obj = models.EditPublickTaskManagement.objects.get(id=t_id)
            edit_publick_task_management_obj.run_task = wenda_robot_task_obj
            edit_publick_task_management_obj.save()
        except IndexError:
            pass

