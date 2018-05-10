#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author:zhangcong
# Email:zc_92@sina.com

from django.shortcuts import redirect

import hashlib

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
import time

from webadmin import models


class BaseResponse(object):
    def __init__(self):
        self.status = True
        self.message = None
        self.data = None
        self.error = {}


class ApiResponse(object):
    def __init__(self):
        self.status = True
        self.message = ""
        self.data = ""


# 用户输入的密码加密
def str_encrypt(pwd):
    """
    :param pwd: 密码
    :return:
    """
    pwd = str(pwd)
    hash = hashlib.md5()
    hash.update(pwd.encode())
    return hash.hexdigest()


def get_ip(request):
    ipaddress = request.META['REMOTE_ADDR']
    return ipaddress


# 装饰器 判断是否登录
def is_login(func):

    def inner(request, *args, **kwargs):
        # return redirect("/statics/err_page/wzwhz.html")
        is_login = request.session.get("is_login", False)  # 从session中获取用户的username对应的值
        if not is_login:
            return redirect("/account/login/")
        return func(request, *args, **kwargs)
    return inner


def paging(objs, start,  length):
    """
    分页取数据
    :param objs:    所有的数据,query_set
    :param start:   从哪个位置开始
    :param length:  每页显示多少条
    :return:
    """
    page_num = int(start) // int(length) + 1
    p = Paginator(objs, length)
    try:
        data_objs = p.page(page_num)
    except PageNotAnInteger:
        data_objs = p.page(1)
    except EmptyPage:
        data_objs = p.page(p.num_pages)
    return data_objs


def combining_data(objs, request, column_list):
    """
    获取表格传过来的参数
    :param objs:  models对象
    :param request:
    :param column_list: 表中要显示的数据列字段
    :return:
    """
    order_column = request.GET.get('order[0][column]')  # 第几列排序
    order = request.GET.get('order[0][dir]')  # 正序还是倒序
    search_value = request.GET.get('search[value]')  # 搜索字段
    order_column = column_list[int(order_column)]
    if order == "desc":
        order_column = "-{order_column}".format(order_column=order_column)
    else:
        order_column = order_column
    q = Q()
    for index, column in enumerate(column_list):
        key = "columns[{index}][searchable]".format(index=index)
        if request.GET.get(key) == "true":
            q.add(Q(**{column+"__contains": search_value}), Q.OR)
    data_objs = objs.filter(q).order_by(order_column)
    return data_objs


def is_valid_date(now_time, time_format):
    """
    判断是否是一个有效的日期字符串
    :param now_time:
    :return:
    """

    try:
        time.strptime(now_time, time_format)
        return True
    except:
        return False


# 判断是否具有该功能的权限
def is_auth(func):
    def inner(request, *args, **kwargs):
        user_id = request.session['user_id']
        user_obj = models.UserProfile.objects.get(id=user_id)
        access_rules_to_rule_obj = models.AccessRulesToRole.objects.select_related().filter(role=user_obj.role,
                                                                                            access_rules__is_function=1)

        path_url = request.path
        # for obj in access_rules_to_rule_obj:
        #     print(obj.access_rules.name, obj.access_rules.url_path)
        # print(path_url)
        if path_url in ["/sales_list_individual/", "/sales_list_team/"]:
            company_name = request.session["company_name"]
            sales_list_permission = models.Company.objects.get(name=company_name).sales_list_permission
            if str("u_{id}".format(id=user_id)) in sales_list_permission:
                return func(request, *args, **kwargs)

        if not access_rules_to_rule_obj.filter(access_rules__url_path=path_url):
            return redirect("/")

        return func(request, *args, **kwargs)

    return inner