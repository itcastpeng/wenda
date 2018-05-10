#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author:zhangcong
# Email:zc_92@sina.com


import sys
import os

# project_dir 是
project_dir = os.path.dirname(os.getcwd())

sys.path.append(project_dir)

os.environ['DJANGO_SETTINGS_MODULE'] ='wenda.settings'
import django
django.setup()

from webadmin import models
import datetime

import xlrd


# 将分配给机器人的任务加入到机器人任务表中
def ToRobotTask():
    robot_ids = [i[0] for i in models.UserProfile.objects.filter(role_id=10).values_list('id')]

    task_objs = models.Task.objects.filter(status=6, publish_user_id__in=robot_ids) # 状态为发布中,且发布用户为机器人
    for obj in task_objs:
        wenda_robot_task_obj = models.WendaRobotTask.objects.filter(task=obj)
        if wenda_robot_task_obj:
            continue

        file_path = obj.task_result_file_path
        if not file_path:
            file_path = obj.task_demand_file_path

        # 从excel 表格中读取数据
        print(os.path.join(project_dir, file_path))
        book = xlrd.open_workbook(filename=os.path.join(project_dir, file_path))
        sh = book.sheet_by_index(0)

        query = []
        for row in range(2, sh.nrows):
            title = sh.cell_value(rowx=row, colx=1)
            content = sh.cell_value(rowx=row, colx=2)
            query.append(models.WendaRobotTask(
                task=obj,
                title=title,
                content=content,
                release_platform=obj.release_platform,
                wenda_type=obj.wenda_type
            ))

        models.WendaRobotTask.objects.bulk_create(query)


if __name__ == '__main__':
    ToRobotTask()