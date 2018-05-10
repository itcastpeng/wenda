#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author:zhangcong
# Email:zc_92@sina.com

from django.shortcuts import redirect

from webadmin import models


class AuthPermissionsMiddleware(object):
    def process_request(self, request):

        if request.path == "/" or request.path.startswith("/account") or request.path.startswith("/api"):
            pass
        else:
            print(dict(request.session))
            role_id = request.session.get("role_id")

            access_rules = models.Role.objects.get(id=role_id).access_rules
            access_rules_list = access_rules.split(',')
            url_path_list = [i[0] for i in models.AccessRules.objects.filter(id__in=access_rules_list).values_list("url_path")]

            flag = False
            for url_path in url_path_list:

                if url_path == request.path or url_path in request.path:
                    flag = True     # 如果有权限则为 True
                    break

            if not flag:    # 如果没有权限,则跳转到主目录
                return redirect('/')
