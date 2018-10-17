#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author:zhangcong
# Email:zc_92@sina.com


import requests
import json
import time
import os
import sys
import datetime


class WeChatPublicSendMsg(object):

    def __init__(self, wechat_data_path=None):
        if wechat_data_path:
            self.wechat_data_path = wechat_data_path
        else:
            self.wechat_data_path = os.path.join(os.getcwd(), "webadmin", "modules", "wechat_data.json")

        print(wechat_data_path)
        with open(self.wechat_data_path, "r", encoding="utf8") as f:
            data = json.loads(f.read())

            self.APPID = data["APPID"]
            self.APPSECRET = data["APPSECRET"]
            self.access_token = data["access_token"]
            self.create_datetime = data["create_datetime"]

            if not self.create_datetime or (int(time.time()) - self.create_datetime) > 7200:
                # print(type(self.create_datetime), self.create_datetime)
                # print(time.time())
                # print((int(time.time()) - self.create_datetime))

                self.get_access_token()

        self.get_users()

    def get_access_token(self):
        print("-" * 30 + "获取 access_token" + "-" * 30)
        url = "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={APPID}&secret={APPSECRET}".format(
            APPID=self.APPID,
            APPSECRET=self.APPSECRET
        )

        ret = requests.get(url)
        print(ret.text)
        self.access_token = json.loads(ret.text).get('access_token')
        print(self.access_token)

        data = {
            "APPID": self.APPID,
            "APPSECRET": self.APPSECRET,
            "access_token": self.access_token,
            "create_datetime": int(time.time())
        }
        print(data)
        with open(self.wechat_data_path, "w", encoding="utf8") as f:
            f.write(json.dumps(data))

        print("\n" * 3)

    # 获取所有用户的 openid
    def get_users(self):
        print("-" * 30 + "获取用户 openid" + "-" * 30)
        url = "https://api.weixin.qq.com/cgi-bin/user/get?access_token={ACCESS_TOKEN}".format(
            ACCESS_TOKEN=self.access_token
        )
        ret = requests.get(url)

        print(ret.text)

        ret_json = json.loads(ret.text)
        if "errcode" in ret_json and ret_json["errcode"] == 40001:
            self.get_access_token()

        print("\n" * 3)

    # 生成二维码
    def generate_qrcode(self, user_id):
        print("-" * 30 + "生成二维码" + "-" * 30)
        url = "https://api.weixin.qq.com/cgi-bin/qrcode/create?access_token={TOKENPOST}".format(
            TOKENPOST=self.access_token
        )
        post_data = {
            "expire_seconds": 604800,
            "action_name": "QR_STR_SCENE",
            "action_info": {
                "scene": {
                    "scene_str": json.dumps(
                        {
                            "user_id": user_id
                        }
                    )
                }
            }
        }

        ret = requests.post(url, data=json.dumps(post_data))
        print(ret.text)
        print(json.loads(ret.text))

        ticket = json.loads(ret.text).get('ticket')

        url = "https://mp.weixin.qq.com/cgi-bin/showqrcode?ticket={TICKET}".format(
            TICKET=ticket
        )
        print("\n" * 3)
        return url
        # ret = requests.get(url)
        # print(ret.text)

    # 发送模板消息
    def sendTempMsg(self, post_data):
        url = "https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={ACCESS_TOKEN}".format(
            ACCESS_TOKEN=self.access_token
        )

        # post_data = {
        #     "touser": "o7Xw_0YmQrxqcYsRhFR2y7yQPBMU",
        #     "template_id": "REblvLGT0dVxwzyrp28mBaXKF6XnHhP2_b7hXjUyI2A",
        #     "url": "http://wenda.zhugeyingxiao.com/",
        #     "data": {
        #         "first": {
        #             "value": "问答任务异常！",
        #             "color": "#173177"
        #         },
        #         # "keyword1": {
        #         #     "value": "修改问答任务",
        #         #     "color": "#173177"
        #         # },
        #         "keyword2": {
        #             "value": datetime.datetime.now().strftime("%y-%m-%d %H:%M:%S"),
        #             "color": "#173177"
        #         },
        #         # "keyword3": {
        #         #     "value": "发布失败",
        #         #     "color": "#173177"
        #         # },
        #         # "keyword4": {
        #         #     "value": "请修改",
        #         #     "color": "#173177"
        #         # },
        #         "remark": {
        #             "value": "问题:嘻嘻嘻\n答案:嘻嘻嘻",
        #             "color": "#173177"
        #         }
        #     }
        # }

        ret = requests.post(url, data=json.dumps(post_data))
        print(ret.text)

    # 创建菜单
    def createMenu(self, menu_data):
        url = "https://api.weixin.qq.com/cgi-bin/menu/create?access_token={ACCESS_TOKEN}".format(
            ACCESS_TOKEN=self.access_token
        )
        # post_data = {
        #     "button": [
        #         {
        #             "name": "诸葛问答",
        #             "sub_button": [
        #                 {
        #                     "type": "view",
        #                     "name": "查看诸葛问答效果",
        #                     "url": "http://www.bjhzkq.com",
        #                 }
        #             ]
        #         }
        #     ]
        # }

        # print(parse.urlencode())
        post_data_json = json.dumps(menu_data, ensure_ascii=False).encode()
        print(post_data_json)
        ret = requests.post(url, data=post_data_json)

        print(ret.text)

    # 创建个性化菜单
    def createCustomMenu(self, menu_data):
        url = "https://api.weixin.qq.com/cgi-bin/menu/addconditional?access_token={ACCESS_TOKEN}".format(
            ACCESS_TOKEN=self.access_token
        )

        post_data_json = json.dumps(menu_data, ensure_ascii=False).encode()
        print(post_data_json)
        ret = requests.post(url, data=post_data_json)

        print(ret.text)

    # 删除自定义菜单
    def delMenu(self):
        print("=" * 50 + "删除自定义菜单" + "=" * 50)
        url = "https://api.weixin.qq.com/cgi-bin/menu/delete?access_token={ACCESS_TOKEN}".format(
            ACCESS_TOKEN=self.access_token
        )

        ret = requests.get(url)
        print(ret.text)

    # 获取自定义菜单
    def getMenu(self):
        url = "https://api.weixin.qq.com/cgi-bin/menu/get?access_token={ACCESS_TOKEN}".format(
            ACCESS_TOKEN=self.access_token
        )
        ret = requests.get(url)
        print(ret.text)

    # 创建标签
    def create_tag(self, tag_name):
        url = "https://api.weixin.qq.com/cgi-bin/tags/create?access_token={ACCESS_TOKEN}".format(
            ACCESS_TOKEN=self.access_token
        )

        post_data = {
            "tag": {"name": tag_name}
        }

        ret = requests.post(url, data=json.dumps(post_data, ensure_ascii=False).encode())
        return ret.text

    # 查看已经创建的所有标签
    def get_tags(self):
        url = "https://api.weixin.qq.com/cgi-bin/tags/get?access_token={ACCESS_TOKEN}".format(
            ACCESS_TOKEN=self.access_token
        )
        ret = requests.get(url)
        return ret.text

    # 给用户关联标签
    def batch_tagging(self, openid, tag_id):
        """
        :param openid:  用户公众号的id
        :param tag_id:  公众号标签的id
        :return:
        """
        print("给用户关联标签")
        url = "https://api.weixin.qq.com/cgi-bin/tags/members/batchtagging?access_token={ACCESS_TOKEN}".format(
            ACCESS_TOKEN=self.access_token
        )

        post_data = {
            "openid_list": [
                openid
            ],
            "tagid": tag_id
        }
        print("post_data -->", post_data)

        ret = requests.post(url, data=json.dumps(post_data, ensure_ascii=False).encode())
        print(ret.text)


def include_django():

    project_dir = os.path.dirname(os.path.dirname(os.getcwd()))
    sys.path.append(project_dir)
    os.environ['DJANGO_SETTINGS_MODULE'] = 'wenda.settings'
    import django
    django.setup()


if __name__ == '__main__':
    wechat_data_path = "wechat_data.json"
    we_chat_public_send_msg_obj = WeChatPublicSendMsg(wechat_data_path)
    we_chat_public_send_msg_obj.get_users()
    # we_chat_public_send_msg_obj.sendTempMsg()

    # # 查看所有用户标签
    # tags = we_chat_public_send_msg_obj.get_tags()
    # print(tags)
    #
    # # 查看自定义菜单
    # we_chat_public_send_msg_obj.getMenu()
    #
    #
    # # 给用户打标签
    # we_chat_public_send_msg_obj.batch_tagging("o7Xw_0SOcSZvgPO7vgt4thfPdAWs", 102)


    post_data = {
        "touser": "o7Xw_0UI33YPrBRb9zRnRul3CbtQ",
        "template_id": "ksNf6WiqO5JEqd3bY6SUqJvWeL2-kEDqukQC4VeYVvw",
        "url": "http://websiteaccount.bjhzkq.com/web/vpsServer",
        "data": {
            "first": {
                "value": "vps异常,请及时处理",
                "color": "#173177"
            },
            "keyword1": {
                "value": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                # "color": "#173177"
            },
            "keyword2": {
                "value": "诸葛问答",
            },
            # "keyword3": {
            #     "value": "发布失败",
            #     "color": "#173177"
            # },
            # "keyword4": {
            #     "value": "请修改",
            #     "color": "#173177"
            # },
            # "remark": {
            #     "value": "问题:嘻嘻嘻\n答案:嘻嘻嘻",
            #     "color": "#173177"
            # }
        }
    }

    we_chat_public_send_msg_obj.sendTempMsg(post_data)

    # # 删除自定义菜单
    # we_chat_public_send_msg_obj.delMenu()

    # # 普通菜单
    # menu_data = {
    #     "button": [
    #         {
    #             "name": "诸葛问答",
    #             "type": "view",
    #             "url": "http://wenda.zhugeyingxiao.com/"
    #         },
    #         {
    #             "name": "诸葛口碑",
    #             "type": "view",
    #             "url": "http://koubei.zhugeyingxiao.com/"
    #         }
    #     ]
    # }
    # we_chat_public_send_msg_obj.createMenu(menu_data)

    # # 超级管理员看到的菜单
    # menu_100 = {
    #     "button": [
    #         {
    #             "name": "诸葛问答",
    #             "sub_button": [
    #                 {
    #                     "type": "click",
    #                     "name": "发布量查询",
    #                     "key": "show_wenda_publish_num"
    #                 },
    #                 {
    #                     "type": "click",
    #                     "name": "覆盖量查询",
    #                     "key": "show_wenda_cover_num"
    #                 },
    #             ]
    #         },
    #         {
    #             "name": "诸葛口碑",
    #             "sub_button": [
    #                 {
    #                     "type": "view",
    #                     "name": "发布量查询",
    #                     "url": "http://koubei.zhugeyingxiao.com/"
    #                 }
    #             ]
    #         }
    #     ],
    #     "matchrule": {
    #         "tag_id": "100"
    #     }
    # }
    # we_chat_public_send_msg_obj.createCustomMenu(menu_100)

    # # 问答客户菜单
    # menu_102 = {
    #     "button": [
    #         {
    #             "name": "诸葛问答",
    #             "sub_button": [
    #                 {
    #                     "type": "click",
    #                     "name": "覆盖量查询",
    #                     "key": "show_wenda_cover_num"
    #                 },
    #             ]
    #         }
    #     ],
    #     "matchrule": {
    #         "tag_id": "102"
    #     }
    # }

    # we_chat_public_send_msg_obj.createCustomMenu(menu_102)

    # include_django()
    # from webadmin import models
    #
    # objs = models.UserProfile.objects.select_related("role").filter(openid__isnull=False)
    # for obj in objs:
    #     print(obj.username)
    #     we_chat_public_send_msg_obj.batch_tagging(obj.openid, obj.role.tag_id)

    # # 给角色关联公众号标签id
    # for i in json.loads(tags)["tags"]:
    #     if "-" in i["name"]:
    #         name = i["name"].split("-")[1]
    #         tag_id = i["id"]
    #         print(name, tag_id)
    #         models.Role.objects.filter(name=name).update(tag_id=tag_id)
    #     else:
    #         continue

    # # 创建角色标签
    # objs = models.Role.objects.filter(tagid__isnull=True)
    # for obj in objs:
    #     tag_name = "角色-" + obj.name
    #     print(tag_name)
    #     result = we_chat_public_send_msg_obj.create_tag(tag_name)
    #     print(result)

    # tag_name = "角色-口碑&问答客户"
    # result = we_chat_public_send_msg_obj.create_tag(tag_name)
    # print(result)












