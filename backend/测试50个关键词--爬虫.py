import binascii
import struct
import sys
import time
import hashlib
from time import sleep
from json import loads
import json
from selenium import webdriver
from bs4 import BeautifulSoup
import requests
import random, os
import base64

project_dir = os.path.dirname(os.path.dirname(os.getcwd()))
sys.path.append(project_dir)
print(project_dir)
os.environ['DJANGO_SETTINGS_MODULE'] = 'wenda.settings'
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.touch_actions import TouchActions

class GuanJianCi:
    # 初始化文件
    def __init__(self, data):
        print('-----------进入爬虫-----------')
        self.data = data
        self.options = webdriver.ChromeOptions()
        mobileEmulation = {'deviceName': 'iPhone 6'}
        self.options.add_experimental_option('mobileEmulation', mobileEmulation)
        self.browser = webdriver.Chrome('./chromedriver_2.36.exe', chrome_options=self.options)
        self.browser.maximize_window()  # 全屏
        self.url = 'https://m.baidu.com'
        # 判断是否为自己的链接 url
        # self.panduan_url = 'http://wenda.zhugeyingxiao.com/test/api/check_zhidao_url'
        # self.panduan_url = 'http://wenda.zhugeyingxiao.com/api/check_zhidao_url'
        self.panduan_url = 'http://127.0.0.1:8006/api/check_zhidao_url'

    # 随机数
    def timesleep(self):
        time.sleep(random.randint(2, 5))
    # 获取输入框  输入关键词 查询
    def data_url(self, user_id, keyword, guanjianci_id):
        # 获取输入框  输入 关键词 并查询
        print('-----------输入数据-----',keyword)
        self.browser.get(self.url)
        self.browser.find_element_by_id('index-kw').send_keys(keyword)
        self.timesleep()
        self.browser.find_element_by_id('index-bn').send_keys(Keys.ENTER)
        self.unit()
        self.timesleep()
        guanjianci_num = 0
        soup = BeautifulSoup(self.browser.page_source, 'lxml')
        self.timesleep()
        results = soup.find('div', class_='results')
        print('-----------------')
        for result in results:
            try:
                lianjie = result['data-log']
                if lianjie:
                    # 固定搜索框 ---
                    js = """$("#page-hd").css({"z-index":"1000"})"""
                    self.browser.execute_script(js)
                    js = """$("#page-hd").css({"position":"fixed"})"""
                    self.browser.execute_script(js)
                    js = """$("#page").css({"padding-top":"146px"})"""
                    self.browser.execute_script(js)
                    # 转换 字典 eval
                    dict_lianjie = eval(lianjie)
                    order = dict_lianjie['order']
                    zhidao_url = dict_lianjie['mu']
                    # 判断以zhidao开头的链接 ---判断是否为百度知道链接---
                    if zhidao_url.startswith('https://zhidao.baidu') or zhidao_url.startswith('http://zhidao.baidu'):
                        print('与自己链接匹配的知道url 与order============= > ', zhidao_url, order)
                        daan_list = []
                        ret = requests.get(zhidao_url)
                        self.timesleep()
                        ret.encoding = 'gbk'
                        soup = BeautifulSoup(ret.text, 'lxml')
                        self.timesleep()
                        div_tag = soup.find('div', class_='layout-wrap')
                        div_line = div_tag.find('div', class_='line content')
                        zhidao_daan = div_line.find('pre').get_text().strip()
                        daan_list.append(zhidao_daan)
                        wgt_div = div_tag.find('div',class_='wgt-answers')
                        span_alls = wgt_div.find_all('span',class_='con')
                        for span_all in span_alls:
                            zhidao_daan = span_all.get_text().strip()
                            daan_list.append(zhidao_daan)

                        daan_str = '六小龄童(1959年4月12日-) ，本名章金莱，是六龄童章宗义的儿子。'
                        if daan_str in daan_list:
                            Action = TouchActions(self.browser)
                            print('daan_list ===========> ',daan_list)
                            if order == '1':
                                div_tag = self.browser.find_element_by_xpath('//*[@id="results"]')
                            else:
                                div_tag = self.browser.find_element_by_xpath('// *[ @ id = "results"] / div[%d]' % int(order))

                            print('---下拉--截第一张屏---')
                            self.timesleep()
                            js = "window.scrollTo(0,{})".format(int(div_tag.location['y']))
                            # self.browser.execute_script("window.scrollBy(0,{})".format(int(div_tag.location['y']) - 20))
                            self.browser.execute_script(js)
                            self.timesleep()
                            self.browser.get_screenshot_as_file(
                                './picture/' + keyword + '--1--' + '{guanjianci_num}.png'.format(
                                    guanjianci_num=guanjianci_num))


                            print('---下拉--标红截图第二张---')
                            js = """$("div[order='%d']").css({"border":"3px solid red"})""" % int(order)
                            self.timesleep()
                            self.browser.execute_script(js)
                            self.timesleep()
                            self.browser.get_screenshot_as_file(
                                './picture/' + keyword + '--2--' + '{guanjianci_num}.png'.format(
                                    guanjianci_num=guanjianci_num))


                            ret = self.browser.get(zhidao_url)
                            print('ret ====== > ',ret)
                            # BeautifulSoup()
                            print('---截第三张截图---')
                            js = """$(".best-answer-container").css({"border":"3px solid red"})"""
                            self.browser.execute_script(js)
                            self.timesleep()
                            self.browser.get_screenshot_as_file(
                                './picture/' + keyword + '--3--' + '{guanjianci_num}.png'.format(
                                    guanjianci_num=guanjianci_num))
                            sleep(3)

                            jieping_1 = open('./picture/' + keyword + '--1--' + '{guanjianci_num}.png'.format(
                                guanjianci_num=guanjianci_num), 'rb').read()

                            jieping_2 = open('./picture/' + keyword + '--2--' + '{guanjianci_num}.png'.format(
                                guanjianci_num=guanjianci_num), 'rb').read()

                            jieping_3 = open('./picture/' + keyword + '--3--' + '{guanjianci_num}.png'.format(
                                guanjianci_num=guanjianci_num), 'rb').read()
                            base64_tupian1 = base64.b64encode(jieping_1)
                            base64_tupian2 = base64.b64encode(jieping_2)
                            base64_tupian3 = base64.b64encode(jieping_3)
                            data_temp = {
                                "keyword": keyword,
                                "guanjianci_num": guanjianci_num,
                                "guanjianci_id": guanjianci_id,
                                "jieping_1": base64_tupian1,
                                "jieping_2": base64_tupian2,
                                "jieping_3": base64_tupian3
                            }
                            # jieping_url = "http://127.0.0.1:8006/api/fifty_guanjianci_fabu"
                            # print('请求数据----> ', data_temp)
                            # requests.post(jieping_url, data=data_temp)
                            sleep(2)
                            self.browser.back()
                            guanjianci_num += 2


                        #     else:
                        #         # print('---链接对--答案不对---')
                        #         pass
                        # else:
                        #     # print('--为知道链接---链接不对---')
                        #     pass
                    else:
                        # print('--无百度知道链接---')
                        pass
                else:
                    continue
            except Exception as e:
                # print('错误----> ', e)
                pass


    # 定位窗口句柄=
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
        self.data_url(user_id, keyword, guanjianci_id)
# 获取关键词调用爬虫数据
def huoqu_guanjianci():
    print('开始')
    url = "http://127.0.0.1:8006/api/fifty_guanjianci_fabu"
    ret = requests.get(url)
    if ret:
        json_ret = ret.content.decode()
        str_ret = json.loads(json_ret)
        print(str_ret)
        if str_ret['data']:
            ret_data = str_ret['data']
            GuanJianCi(ret_data).run()
            print(input('按任意键结束任务----->:'))

    # while True:
        # url = 'http://wenda.zhugeyingxiao.com/test/api/fifty_guanjianci_fabu'
        # url = 'http://wenda.zhugeyingxiao.com/api/fifty_guanjianci_fabu'
        # url = "http://127.0.0.1:8006/api/fifty_guanjianci_fabu"
        # url = 'http://wenda.zhugeyingxiao.com/test/api/fifty_guanjianci_fabu?canshu=2'
        # url = 'http://wenda.zhugeyingxiao.com/api/fifty_guanjianci_fabu?canshu=2'
        # canshu_url = "http://127.0.0.1:8006/api/fifty_guanjianci_fabu?canshu=2"
        # ret = requests.get(url)
        # if ret:
        #     print('=====请求任务=====')
        #     json_ret = ret.content.decode()
        #     str_ret = json.loads(json_ret)
        #     # print('str_ret ============ >',str_ret)
        #     if str_ret['data']:
        #         ret_data = str_ret['data']
        #         GuanJianCi(ret_data).run()
        #
        #     else:
        #         # print('===== canshu=2 =====')
        #         ret = requests.get(canshu_url)
        #         if ret:
        #             json_ret = ret.content.decode()
        #             str_ret = json.loads(json_ret)
        #             # print('str_ret  - ->', str_ret)
        #             if str_ret['data']:
        #                 ret_data = str_ret['data']
        #                 GuanJianCi(ret_data).run()
        #         sleep_time = 60 * 5
        #         sleep(sleep_time)
        #         # print('===重新执行===')
        #
        # else:
        #     # print('===== canshu=2 =====')
        #     ret = requests.get(canshu_url)
        #     if ret:
        #         json_ret = ret.content.decode()
        #         str_ret = json.loads(json_ret)
        #         # print('str_ret  - ->', str_ret)
        #         if str_ret['data']:
        #             ret_data = str_ret['data']
        #             GuanJianCi(ret_data).run()
        #     sleep_time = 60 * 5
        #     sleep(sleep_time)
            # print('===重新执行===')
huoqu_guanjianci()
