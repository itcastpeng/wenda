#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author:zhangcong
# Email:zc_92@sina.com


import requests
import random
import json
import time
import datetime

from bs4 import BeautifulSoup

import os
from requests.exceptions import ConnectionError, ReadTimeout


class ADSL(object):
    """
    ADSL拨号，断开连接
    """

    def __init__(self, adsl_username, adsl_pwd):
        """
        初始化adsl名称、用户名、密码
        """
        self.name = "宽带连接"  # ADSL名称
        self.username = adsl_username  # ADSL用户名
        self.password = adsl_pwd  # ADSL密码

    def connect(self):
        """
        宽带拨号
        :return: None
        """
        cmd_str = "rasdial %s %s %s" % (self.name, self.username, self.password)
        print(cmd_str)
        os.system(cmd_str)
        time.sleep(10)

    def disconnect(self):
        """
        断开宽带连接
        :return: None
        """
        cmd_str = "rasdial %s /disconnect" % self.name
        print(cmd_str)
        os.system(cmd_str)
        time.sleep(2)

    def reconnect(self):
        """
        重新进行拨号
        :return: None
        """
        self.disconnect()
        self.connect()


# 检查问答反链的状态
class CheckWendaUrlStatus(object):
    def __init__(self):
        self.token = None

        self.adsl_username = '057746320048'
        self.adsl_password = '760224'

    # VPS 签到
    def vpsQiandao(self):
        params_data = {
            "vpsName": "122.228.7.41:20681",
            "task_name": "问答查询反链"
        }
        url = "http://websiteaccount.bjhzkq.com/api/vpsServer"
        ret = requests.get(url, params=params_data)
        print(ret.text)

    # 登录
    def login(self):
        print(datetime.datetime.now(), "*" * 10, " --> 登录")
        url = "http://wenda.zhugeyingxiao.com/api/login/"
        data = {
            "username": "查反链状态",
            "password": "wenda123"
        }
        ret = requests.post(url, data=data, timeout=5)
        result = json.loads(ret.text)
        if result["status"]:
            self.token = result["data"]["token"]
        else:
            print("登录异常 --> self.login")

    # 获取任务
    def getTask(self):
        print(datetime.datetime.now(), "*" * 10, " --> 获取任务")
        url = "http://wenda.zhugeyingxiao.com/api/check_wenda_link/"

        params = {
            'token': self.token,
        }
        print(self.token)

        ret = requests.get(url, params=params, timeout=5)
        result = json.loads(ret.text)
        print(result)
        if result["status"]:
            url = result['data']['url']
            tid = result['data']['tid']
            return url, tid

        else:
            print(result['message'])

    # 提交任务
    def postTask(self, tid, status):
        print(datetime.datetime.now(), "*" * 10, " --> 提交任务")

        url = "http://wenda.zhugeyingxiao.com/api/check_wenda_link/"

        params = {
            'token': self.token,
        }

        data = {
            'tid': tid,
            'status': status
        }

        print(params, data)

        ret = requests.post(url, params=params, data=data, timeout=5)
        result = json.loads(ret.text)
        if result["status"]:
            print(result["message"])
        else:
            print(result['message'])

    # 检查任务状态
    def checkTask(self, url):
        print(datetime.datetime.now(), "*" * 10, " --> 检查任务状态")

        liulanqi = ["Mozilla/5.0 (Windows NT 5.1; rv:6.0.2) Gecko/20100101 Firefox/6.0.2",
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_5) AppleWebKit/537.17 (KHTML, like Gecko) "
                    "Chrome/24.0.1312.52 Safari/537.17",

                    "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN; rv:1.9.1.16) Gecko/20101130 Firefox/3.5.16",
                    "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; .NET CLR 1.1.4322)",
                    "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0)",
                    "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/45.0.2454.99 Safari/537.36",

                    "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 1.1.4322)",
                    "Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.2)",
                    "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.13 (KHTML, like Gecko) Chrome/24.0.1290.1 Safari/537.13",
                    "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)",
                    "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36",
                    "Mozilla/5.0 (Windows; U; Windows NT 5.2; zh-CN; rv:1.9.0.19) Gecko/2010031422 Firefox/3.0.19 "
                    "(.NET CLR 3.5.30729)",

                    "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.2)",
                    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.17 (KHTML, like Gecko) "
                    "Chrome/24.0.1312.57 Safari/537.17",

                    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/31.0.1650.63 Safari/537.36",

                    "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:24.0) Gecko/20100101 Firefox/24.0",
                    "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:2.0b13pre) Gecko/20110307 Firefox/4.0b13"]

        num = random.randint(1, len(liulanqi) - 1)
        headers = {'User-Agent': liulanqi[num]}

        ret = requests.get(url, headers=headers, timeout=5)
        ret.encoding = "gbk"

        # print(ret.text)

        soup = BeautifulSoup(ret.text, 'lxml')
        ask_title = soup.find(class_='ask-title')
        status = 2  # 默认正常
        if ask_title:
            answer_title = soup.find(class_='answer-title')
            if answer_title and '最佳答案' in ret.text:  # 有最佳答案
                status = 2

            else:  # 没有最佳答案
                status = 5

                bd_wrap = soup.find(class_='bd-wrap')
                if not bd_wrap:  # 表示无答案
                    status = 4
        elif "本回答被提问者采纳" in ret.text:
            status = 2
        else:
            status = 3  # 链接失效

        return status

    # 添加百度知道问题
    def add_zhidaohuida(self):
        print("养账号 --> 添加百度知道任务")
        liulanqi = [
            "Mozilla/5.0 (Windows NT 5.1; rv:6.0.2) Gecko/20100101 Firefox/6.0.2",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_5) AppleWebKit/537.17 (KHTML, like Gecko) "
            "Chrome/24.0.1312.52 Safari/537.17",

            "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN; rv:1.9.1.16) Gecko/20101130 Firefox/3.5.16",
            "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; .NET CLR 1.1.4322)",
            "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0)",
            "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/45.0.2454.99 Safari/537.36",

            "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 1.1.4322)",
            "Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.2)",
            "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.13 (KHTML, like Gecko) Chrome/24.0.1290.1 Safari/537.13",
            "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)",
            "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36",
            "Mozilla/5.0 (Windows; U; Windows NT 5.2; zh-CN; rv:1.9.0.19) Gecko/2010031422 Firefox/3.0.19 "
            "(.NET CLR 3.5.30729)",

            "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.2)",
            "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.17 (KHTML, like Gecko) "
            "Chrome/24.0.1312.57 Safari/537.17",

            "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/31.0.1650.63 Safari/537.36",

            "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:24.0) Gecko/20100101 Firefox/24.0",
            "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:2.0b13pre) Gecko/20110307 Firefox/4.0b13"
        ]

        headers = {
            'User-Agent': liulanqi[random.randint(0, len(liulanqi) - 1)],
        }
        req = requests.session()
        req.get("https://zhidao.baidu.com", headers=headers)

        headers["Referer"] = "https://zhidao.baidu.com/"

        get_url_list = [
            "https://zhidao.baidu.com/list?cid=107",  # 体育运动
            "https://zhidao.baidu.com/list?cid=110",  # 电脑网络
            "https://zhidao.baidu.com/list?cid=102",  # 企业管理
            "https://zhidao.baidu.com/list?cid=108",  # 文化艺术
            "https://zhidao.baidu.com/list?cid=111",  # 娱乐休闲
            "https://zhidao.baidu.com/list?cid=113",  # 地区
        ]
        random.shuffle(get_url_list)

        ret = req.get(get_url_list[0], headers=headers)
        ret.encoding = "gbk"

        soup = BeautifulSoup(ret.text, "lxml")

        div_tag = soup.find("div", id="j-question-list-pjax-container")

        li_tag_list = div_tag.find_all("li")

        for li_tag in li_tag_list:
            title_tag = li_tag.find("a", class_="title-link")
            title = title_tag.get_text().strip()
            url = title_tag.attrs["href"]

            # 添加采集的问答
            post_data = {
                "title": title,
                "url": url,
            }

            while True:
                try:
                    # 添加任务
                    url = "{domain}/api/add_zhidaohuida".format(domain="http://wenda.zhugeyingxiao.com")
                    print(url, post_data)
                    ret = requests.post(url, data=post_data)
                    ret_json = json.loads(ret.text)
                    print(ret_json)
                    break
                except:
                    break

    def check_qudao_cunhuo(self):
        api_url = "http://wenda.zhugeyingxiao.com/api/qudao_shangwutong_cunhuo"
        ret = requests.get(api_url)
        result_data = ret.json()
        print(result_data)
        if not result_data['data']:
            return
        baidu_link = result_data['data']['url']
        content = result_data['data']['content']
        print('content -->', content)
        ret = requests.get(baidu_link)
        ret.encoding = "gbk"

        soup = BeautifulSoup(ret.text, 'lxml')
        div_tags = soup.find_all("div", class_="line content")

        flag = False
        for tag in div_tags:
            print('-' * 100)
            span_tag = tag.find('span', class_="con")
            pre_tag = tag.find('pre', class_="best-text mb-10")
            div_tag = tag.find('div', class_="answer-text mb-10 ")

            if span_tag or pre_tag or div_tag:
                if span_tag:
                    page_keywords_list = span_tag.strings
                elif div_tag:
                    a_tag = div_tag.find('a')
                    if a_tag:
                        a_tag.extract()
                    page_keywords_list = div_tag.strings
                else:
                    page_keywords_list = pre_tag.strings

                print(div_tag)
                for page_keywords in page_keywords_list:
                    if not page_keywords.strip():
                        continue
                    else:
                        if page_keywords.strip() not in content:
                            print('page_keywords -->', page_keywords)
                            flag = False
                            break
                        else:
                            print('Tpage_keywords -->', page_keywords)
                            flag = True
                if flag:
                    break
            else:
                tag_text = tag.get_text()
                print(tag_text)
                if content in tag_text:
                    flag = True
                    break
                elif len(content.split()) > 1:
                    if content.split()[0] in tag_text and content.split()[-1] in tag_text:
                        flag = True
        if flag:
            print("匹配到答案 -->")
            data = {
                'tid': result_data['data']['tid'],
                'status': '1'
            }


        else:
            data = {
                'tid': result_data['data']['tid'],
                'status': '0'
            }

        requests.post(api_url, data=data)

    def start(self):
        while True:
            try:
                # 添加养账号任务
                ADSL(self.adsl_username, self.adsl_password).reconnect()
                self.add_zhidaohuida()
                self.vpsQiandao()

                # 检测渠道存活任务
                count = 0
                while True:
                    count += 1
                    if count > 5:
                        break
                    ADSL(self.adsl_username, self.adsl_password).reconnect()
                    while True:
                        try:
                            self.check_qudao_cunhuo()
                            break
                        except ConnectionError:
                            pass
                ADSL(self.adsl_username, self.adsl_password).reconnect()
                self.login()
                result = self.getTask()
                if result:
                    url, tid = result
                    if url:
                        status = self.checkTask(url)
                    else:
                        status = 11
                    self.postTask(tid, status)
                else:
                    print("无任务, 休息60秒")
                    time.sleep(60)

            except ConnectionError as e:
                pass

            except ReadTimeout as e:
                pass


CheckWendaUrlStatus().start()
