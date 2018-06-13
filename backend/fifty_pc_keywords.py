import binascii
import struct
import sys
import time
import hashlib
from time import sleep
from json import loads
from kombu.utils import json
from selenium import webdriver
from bs4 import BeautifulSoup
import requests
import random, os
import base64

project_dir = os.path.dirname(os.path.dirname(os.getcwd()))
sys.path.append(project_dir)
print(project_dir)
os.environ['DJANGO_SETTINGS_MODULE'] = 'wenda.settings'
import django

django.setup()


class GuanJianCi:

    # 初始化文件
    def __init__(self, data):
        print('进入爬虫接口==================================')
        # self.dr = webdriver.Chrome('./chromedriver_2.36.exe')
        self.data = data
        self.options = webdriver.ChromeOptions()
        # 设置中文
        self.options.add_argument('lang=zh_CN.UTF-8')
        # 更换头部
        self.options.add_argument(
            'user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 9_3_4 like Mac OS X) AppleWebKit/601.1.46 (KHTML, like Gecko) Mobile/13G35 QQ/6.5.3.410 V1_IPH_SQ_6.5.3_1_APP_A Pixel/750 Core/UIWebView NetType/2G Mem/117')
        self.browser = webdriver.Chrome('./chromedriver_2.36.exe', chrome_options=self.options)
        self.browser.maximize_window()  # 全屏
        self.url = 'https://m.baidu.com'
        # 判断是否为自己的链接 url
        # self.panduan_url = 'http://wenda.zhugeyingxiao.com/api/check_zhidao_url'
        self.panduan_url = 'http://127.0.0.1:8006/api/check_zhidao_url'

    # 随机数 增加装饰器 该函数有self属性
    @property
    def rand(self):
        return random.randint(1, 5)

    # 获取输入框  输入关键词 查询
    def data_url(self, user_id, keyword, guanjianci_id):
        # 获取输入框  输入 关键词 并查询
        print('-----------输入数据-----------')
        self.browser.get(self.url)
        self.browser.find_element_by_id('index-kw').send_keys(keyword)
        sleep(self.rand)
        self.browser.find_element_by_id('index-bn').click()
        self.unit()
        guanjianci_num = 0
        soup = BeautifulSoup(self.browser.page_source, 'lxml')
        results = soup.find('div', class_='results')
        data_list = []
        for result in results:
            try:
                lianjie = result['data-log']
                # print('lianjie - - -- >',lianjie)
                if lianjie:
                    dict_lianjie = eval(lianjie)
                    order = dict_lianjie['order']
                    zhidao_url = dict_lianjie['mu']
                    # print('---判断是否为百度知道链接---')
                    # 判断以zhidao开头的链接
                    if zhidao_url.startswith('https://zhidao.baidu') or zhidao_url.startswith('http://zhidao.baidu'):
                        # print('---此链接为百度知道链接---')
                        # 获取当前url
                        data_temp = {
                            'client_user_id': user_id,
                            'is_pause': 0,
                            'url': zhidao_url
                        }
                        ret_panduan = requests.post(self.panduan_url, data=data_temp)
                        ret_json = ret_panduan.content.decode()
                        str_ret = json.loads(ret_json)
                        # print('---判断答案---')
                        if str_ret['status']:
                            print('答案一致')
                            print('user_id 为: ', user_id)
                            # print('zhidao_url -- -- --- > ',zhidao_url )
                            print('order - -  > ', order)
                            daan_str = str_ret['data']['content']
                            ret = requests.get(zhidao_url)
                            ret.encoding = 'gbk'
                            soup = BeautifulSoup(ret.text, 'lxml')
                            div_tag = soup.find('div', class_='layout-wrap')
                            div_line = div_tag.find('div', class_='line content')
                            zhidao_daan = div_line.find('pre').get_text()
                            print('----知道答案----', zhidao_daan)
                            print('----自己答案----', daan_str[0])
                            if daan_str[0] in zhidao_daan:
                                # # 获取坐标 js下拉
                                print('---下拉--截第一张屏---')
                                # """  //*[@id="results"]/div[1] """
                                if order == '1':
                                    div_tag = self.browser.find_element_by_xpath('//*[@id="results"]')
                                else:
                                    div_tag = self.browser.find_element_by_xpath(
                                        '//*[@id="results"]/div[%d]' % int(order))
                                # selenium下拉
                                self.browser.execute_script("window.scrollBy(0,{})".format(div_tag.location['y']))
                                sleep(self.rand)
                                # js下拉
                                # js = "document.documentElement.scrollbottom={}".format(int(div_tag.location['y']))
                                # self.browser.execute_script(js)
                                # print('路径 - -- >',keyword + '--1--' + '{guanjianci_num}.png'.format(guanjianci_num=guanjianci_num))
                                self.browser.get_screenshot_as_file(
                                    './picture/' + keyword + '--1--' + '{guanjianci_num}.png'.format(
                                        guanjianci_num=guanjianci_num))
                                print('---下拉--标红截图第二张---')
                                js = """$("div[order='%d']").css({"border":"3px solid red"})""" % int(order)
                                sleep(self.rand)
                                self.browser.execute_script(js)
                                sleep(self.rand)
                                self.browser.get_screenshot_as_file(
                                    './picture/' + keyword + '--2--' + '{guanjianci_num}.png'.format(
                                        guanjianci_num=guanjianci_num))
                                self.browser.get(zhidao_url)
                                print('---下拉--截第三张截图---')
                                js = """$(".best-answer-container").css({"border":"3px solid red"})"""
                                self.browser.execute_script(js)
                                sleep(self.rand)
                                self.browser.get_screenshot_as_file(
                                    './picture/' + keyword + '--3--' + '{guanjianci_num}.png'.format(
                                        guanjianci_num=guanjianci_num))
                                sleep(3)

                                jieping_url = "http://127.0.0.1:8006/api/fifty_guanjianci_fabu"
                                jieping_1 = open('./picture/' + keyword + '--1--' + '{guanjianci_num}.png'.format(
                                    guanjianci_num=guanjianci_num), 'rb').read()

                                jieping_2 = open('./picture/' + keyword + '--2--' + '{guanjianci_num}.png'.format(
                                    guanjianci_num=guanjianci_num), 'rb').read()

                                jieping_3 = open('./picture/' + keyword + '--3--' + '{guanjianci_num}.png'.format(
                                    guanjianci_num=guanjianci_num), 'rb').read()
                                print('len(jieping_1) - ->', len(jieping_1))
                                base64_tupian1 = base64.b64encode(jieping_1)
                                base64_tupian2 = base64.b64encode(jieping_2)
                                base64_tupian3 = base64.b64encode(jieping_3)
                                print('len(b64encode) - ->', len(base64_tupian1))
                                data_temp = {
                                    "keyword": keyword,
                                    "guanjianci_num": guanjianci_num,
                                    "guanjianci_id": guanjianci_id,
                                    "jieping_1": base64_tupian1,
                                    "jieping_2": base64_tupian2,
                                    "jieping_3": base64_tupian3
                                }
                                ret = requests.post(jieping_url, data=data_temp)
                                print('ret == > ', ret)
                                sleep(2)
                                self.browser.back()
                                guanjianci_num += 2
                        else:
                            print('---链接对--答案不对---')
                else:
                    continue
            except Exception as e:
                print('错误----> ', e)

    def __del__(self):
        sleep(3)
        self.browser.close()

        # 定位窗口句柄

    def unit(self):
        # 定位到当前窗口句柄
        sreach_window = self.browser.current_window_handle
        all_handels = self.browser.window_handles
        new_handel = None
        for handle in all_handels:
            if handle != sreach_window:
                new_handel = handle
                break
        return new_handel

    def run(self):
        user_id = self.data['user_id']
        keyword = self.data['guanjianci']
        guanjianci_id = self.data['guanjianci_id']
        print('user_id --- guanjianci --> ', user_id, keyword, guanjianci_id)

        self.data_url(user_id, keyword, guanjianci_id)


# 获取关键词调用爬虫数据
def huoqu_guanjianci():
    while True:
        # url = 'http://wenda.zhugeyingxiao.com/api/fifty_guanjianci_fabu'
        url = "http://127.0.0.1:8006/api/fifty_guanjianci_fabu"
        ret = requests.get(url)
        json_ret = ret.content.decode()
        str_ret = json.loads(json_ret)
        print('str_ret  - ->', str_ret)
        if str_ret['data']:
            ret_data = str_ret['data']
            GuanJianCi(ret_data).run()
            sleep(2)
        else:
            print('====当前无任务====')
            sleep_time = 60 * 5
            sleep(sleep_time)
            print('===重新执行===')


huoqu_guanjianci()
