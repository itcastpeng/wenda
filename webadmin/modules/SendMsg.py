#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author:zhangcong
# Email:zc_92@sina.com

# 使用微信企业号发送消息


import requests
import json
import datetime


class SendMsg(object):

    def __init__(self):
        self.corpid = "ww3bcb9cc053d30b61"
        self.corpsecret = "kU_omJV1pokWV8nUCJD2o267Ur3W3cmCprrNRuOyZNo"
        self.access_token = ""
        self.agentId = "1000003"

        self.get_access_token()

    # 获取
    def get_access_token(self):
        url = "https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={corpid}&corpsecret={corpsecret}".format(
            corpid=self.corpid,
            corpsecret=self.corpsecret
        )

        ret = requests.get(url)
        result = json.loads(ret.text)
        if "access_token" in result:
            self.access_token = result["access_token"]
        else:
            self.get_access_token()

    # 获取部门信息
    def get_department(self, department_id=None):
        """
        :param department_id:   部门id,如果为空,表示获取所有部门
        :return:
        """
        url = "https://qyapi.weixin.qq.com/cgi-bin/department/list?access_token={access_token}&id={department_id}".format(
            access_token=self.access_token,
            department_id=department_id
        )

        ret = requests.get(url)
        # 根目录id = 1

    # 获取部门所有成员
    def get_users(self, department_id, fetch_child=0):
        """
        :param department_id:   部门id
        :param fetch_child:     是否递归, 0=不递归  1=递归
        :return:
        """
        url = "https://qyapi.weixin.qq.com/cgi-bin/user/simplelist?access_token={access_token}&department_id={department_id}&fetch_child={fetch_child}".format(
            access_token=self.access_token,
            department_id=department_id,
            fetch_child=fetch_child
        )

        ret = requests.get(url)
        print(ret.text)

    # 获取标签列表
    def get_tags(self):
        url = "https://qyapi.weixin.qq.com/cgi-bin/tag/list?access_token={access_token}".format(
            access_token=self.access_token
        )
        ret = requests.get(url)
        print(ret.text)

    def send_text_msg(self, user_id, text):
        wx_url = "https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={access_token}".format(
            access_token=self.access_token
        )

        print(self.access_token)

        post_data = {
           "touser": user_id,
           "msgtype": "text",
           "agentid": self.agentId,
           "text": {
               "content": text,
           },
           "safe": 0
        }
        print(post_data)

        ret = requests.post(wx_url, data=json.dumps(post_data, ensure_ascii=False).encode("utf-8"))
        print(ret.text)

    # 发送卡片类型消息
    def send_card_msg(self, user_id, description, url):
        wx_url = "https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={access_token}".format(
            access_token=self.access_token
        )

        print(self.access_token)

        post_data = {
           "touser": user_id,
           "msgtype": "textcard",
           "agentid": self.agentId,
           "textcard": {
               "title": "口碑任务发布失败",
                "description": description,
                "url": url,
                # "btntxt": "更多"
           },
           "safe": 0
        }
        print(post_data)

        ret = requests.post(wx_url, data=json.dumps(post_data, ensure_ascii=False).encode("utf-8"))
        print(ret.text)


if __name__ == '__main__':
    send_msg_obj = SendMsg()
    # send_msg_obj.get_department()
    # send_msg_obj.get_users(1, 1)

    # send_msg_obj.get_tags()

    now_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    description = """
        <div class="gray">通知时间: {now_datetime}</div>
        <div class="normal">编写内容: {content}</div>
        <div class="highlight">失败原因: {yuanyin}</div>
    """.format(
        now_datetime=now_datetime,
        content="",
        yuanyin=""
    )

    # url = "http://koubei.zhugeyingxiao.com/edit_error_tent/183/"
    # send_msg_obj.send_card_msg("zhangcong", description, url)

    text = "消息测试,请勿理会"
    send_msg_obj.send_text_msg("zhangcong|zhaoshanglu|xunmeng|lijia|xuyan", text)
