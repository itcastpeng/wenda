#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author:zhangcong
# Email:zc_92@sina.com


from __future__ import absolute_import, unicode_literals

from celery import Celery
from celery.schedules import crontab

app = Celery(
    broker='redis://192.168.10.104:6379/0',
    backend='redis://192.168.10.104:6379/0',
    include=['wenda_celery_project.tasks'],
)

app.conf.beat_schedule = {

    # 配置每隔一个小时执行一次
    'CheckWenda': {                                           # 此处的命名不要用 tasks 开头,否则会报错
        'task': 'wenda_celery_project.tasks.CheckWenda',                      # 要执行的任务函数名
        'schedule': crontab("*", '*', '*', '*', '*'),       # 此处跟 linux 中 crontab 的格式一样
        # 'args': (2, 2),                                     # 传递的参数
    },

    # 给机器人分配任务
    'ToRobotTask': {  # 此处的命名不要用 tasks 开头,否则会报错
        'task': 'wenda_celery_project.tasks.ToRobotTask',  # 要执行的任务函数名
        'schedule': crontab("*", '*', '*', '*', '*'),  # 此处跟 linux 中 crontab 的格式一样
        # 'args': (2, 2),                                     # 传递的参数
    },

    # 将机器人操作完的任务返还到任务中
    'RobotTaskToTask': {  # 此处的命名不要用 tasks 开头,否则会报错
        'task': 'wenda_celery_project.tasks.RobotTaskToTask',  # 要执行的任务函数名
        'schedule': crontab("*", '*', '*', '*', '*'),  # 此处跟 linux 中 crontab 的格式一样
        # 'args': (2, 2),                                     # 传递的参数
    },

    'CheckTaskYichang': {
        'task': 'wenda_celery_project.tasks.CheckTaskYichang',
        'schedule': crontab("0", '*', '*', '*', '*'),
    },

    # 更新客户当日覆盖信息
    'UpdateClientDayCover': {
        'task': 'wenda_celery_project.tasks.update_client_day_cover',
        'schedule': crontab("0", '*', '*', '*', '*'),
    },

    # 生成指定首页关键词覆盖报表
    'KeywordsTopPageCoverExcel': {
        'task': 'wenda_celery_project.tasks.keywords_top_page_cover_excel',
        'schedule': crontab("0", '*/2', '*', '*', '*'),
    },

    # 统计3天未操作的客户,然后将客户名发送给对应的营销顾问
    'TongjiKehuShiyong': {
        'task': 'wenda_celery_project.tasks.tongji_kehu_shiyong',
        'schedule': crontab('0', '1', '*', '*', '*'),
    },

    # 生成客户日覆盖报表 - (老问答覆盖模式)
    'UserprofileKeywordsCover': {
        'task': 'wenda_celery_project.tasks.userprofile_keywords_cover',
        'schedule': crontab('*/2', '*', '*', '*', '*'),
    },

    # 每天提醒客户报表已经查完  10-20 点每个小时执行一遍
    'SendCoverInfo': {
        'task': 'wenda_celery_project.tasks.send_cover_info',
        'schedule': crontab('0', '2-12', '*', '*', '*'),
    },

    # # 缓存指定首页关键词中的数据
    # 'cache_keywords_top_set_init_data': {
    #     'task': 'wenda_celery_project.tasks.cache_keywords_top_set_init_data',
    #     'schedule': crontab('*', '*', '*', '*', '*'),
    # }

    # 定时更新覆盖报表中的数据
    'update_client_covering_data': {
        'task': 'wenda_celery_project.tasks.update_client_covering_data',
        'schedule': crontab('*/5', '*', '*', '*', '*'),
    },

    # 插入养账号新问答任务
    'yangzhanghao_task': {
        'task': 'wenda_celery_project.tasks.yangzhanghao_task',
        'schedule': crontab('*/5', '*', '*', '*', '*'),
    },

    # 将最近6个小时使用的 ip 地址缓存到redis 中
    'cached_ipaddr_list': {
        'task': 'wenda_celery_project.tasks.cached_ipaddr_list',
        'schedule': crontab('*', '*', '*', '*', '*'),
    },

    # 更新问答库编辑编写数据
    'update_wendaku_bianjibianxie': {
        'task': 'wenda_celery_project.tasks.update_wendaku_bianjibianxie',
        'schedule': crontab('*/10', '*', '*', '*', '*'),
    }
}


# Optional configuration, see the application user guide.
app.conf.update(
    result_expires=3600,
)

if __name__ == '__main__':
    app.start()

