#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author:zhangcong
# Email:zc_92@sina.com


from django.shortcuts import render, HttpResponse
import json
import hashlib
import os
from django.views.decorators.csrf import csrf_exempt

import xml.dom.minidom
from webadmin import models

from webadmin.modules import WeChat
import datetime

def checkSignature(timestamp, nonce, token, signature):

    tmp_str = "".join(sorted([timestamp, nonce, token]))
    hash_obj = hashlib.sha1()
    hash_obj.update(tmp_str.encode('utf-8'))
    if hash_obj.hexdigest() == signature:
        return True
    else:
        return False


@csrf_exempt
def index(request):
    signature = request.GET.get("signature")
    timestamp = request.GET.get("timestamp")
    nonce = request.GET.get("nonce")
    echostr = request.GET.get("echostr")

    wechat_data_path = os.path.join(os.getcwd(), "webadmin/modules/wechat_data.json")
    with open(wechat_data_path, "r", encoding="utf8") as f:
        wechat_data = json.loads(f.read())
        token = wechat_data["token"]
        EncodingAESKey = wechat_data["EncodingAESKey"]

    check_result = checkSignature(timestamp, nonce, token, signature)

    if check_result:
        if request.method == "GET":
            return HttpResponse(echostr)
        else:
            body_text = str(request.body, encoding="utf8")
            print('body_text -->', body_text)

            # 使用minidom解析器打开 XML 文档
            DOMTree = xml.dom.minidom.parseString(body_text)
            collection = DOMTree.documentElement
            print('collection -->', collection)

            # 事件类型
            event = collection.getElementsByTagName("Event")[0].childNodes[0].data
            print("event -->", event)

            # 用户的 openid
            from_user_name = collection.getElementsByTagName("FromUserName")[0].childNodes[0].data

            wechat_data_path = "webadmin/modules/wechat_data.json"
            we_chat_public_send_msg_obj = WeChat.WeChatPublicSendMsg(wechat_data_path)

            # 扫描带参数的二维码
            if event in ["subscribe", "SCAN"]:
                # subscribe = 首次关注
                # SCAN = 已关注
                # 事件 Key 值
                event_key = collection.getElementsByTagName("EventKey")[0].childNodes[0].data
                if event == "subscribe":
                    event_key = event_key.split("qrscene_")[-1]
                event_key = json.loads(event_key)
                user_id = event_key["user_id"]
                print('event_key -->', event_key)

                # 保证1个微信只能够关联1个账号
                if models.UserProfile.objects.filter(openid=from_user_name).count() == 0:
                    obj = models.UserProfile.objects.get(id=user_id)
                    print(obj.username)
                    obj.openid = from_user_name
                    obj.save()

            # 取消关注
            elif event == "unsubscribe":
                models.UserProfile.objects.filter(openid=from_user_name).update(openid=None)

            # 用户点击菜单
            elif event == "CLICK":
                event_key = collection.getElementsByTagName("EventKey")[0].childNodes[0].data
                # user_profile_obj = models.UserProfile.objects.get(openid=from_user_name)

                print(event_key)

                post_data = {
                    "touser": from_user_name,
                    "template_id": "ksNf6WiqO5JEqd3bY6SUqJvWeL2-kEDqukQC4VeYVvw",
                    "url": "http://wenda.zhugeyingxiao.com",
                    "data": {
                        "first": {
                            "value": "",
                            "color": "#173177"
                        },
                        "keyword1": {
                            "value": datetime.datetime.now().strftime("%y-%m-%d %H:%M:%S"),
                        },
                        "keyword2": {
                            "value": "诸葛问答",
                        },

                        "remark": {
                            "value": "点击查看详细数据",
                        }
                    }
                }

                if event_key == "show_wenda_cover_num":    # 问答覆盖量查询
                    post_data["data"]["first"]["value"] = "问答覆盖量查询结果"
                    post_data["url"] = "http://wenda.zhugeyingxiao.com/show_wenda_cover_num/{from_user_name}/".format(
                        from_user_name=from_user_name
                    )

                elif event_key == "show_wenda_publish_num":     # 问答发布量查询
                    post_data["data"]["first"]["value"] = "问答发布量查询结果"
                    post_data["url"] = "http://wenda.zhugeyingxiao.com/show_wenda_publish_num/{from_user_name}/".format(
                        from_user_name=from_user_name
                    )

                we_chat_public_send_msg_obj.sendTempMsg(post_data)

            return HttpResponse("")

    else:
        return HttpResponse(False)


