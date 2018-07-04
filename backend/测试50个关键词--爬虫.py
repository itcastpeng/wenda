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
from selenium.common.exceptions import InvalidSelectorException
from selenium.common.exceptions import WebDriverException

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
        self.panduan_url = 'http://wenda.zhugeyingxiao.com/api/check_zhidao_url'
        # self.panduan_url = 'http://127.0.0.1:8006/api/check_zhidao_url'

        # self.jieping_url = "http://wenda.zhugeyingxiao.com/test/api/fifty_guanjianci_fabu"
        self.jieping_url = "http://wenda.zhugeyingxiao.com/api/fifty_guanjianci_fabu"
        # self.jieping_url = "http://127.0.0.1:8006/api/fifty_guanjianci_fabu"

    # 随机数
    def timesleep(self):
        time.sleep(random.randint(2, 5))
    # 获取输入框  输入关键词 查询
    def data_url(self, user_id, keyword, guanjianci_id):
        # 获取输入框  输入 关键词 并查询
        print('-----=============------输入数据关键词{keyword}-------==============-------'.format(keyword=keyword))
        self.browser.get(self.url)
        self.browser.find_element_by_id('index-kw').send_keys(keyword)
        self.timesleep()
        self.browser.find_element_by_id('index-bn').send_keys(Keys.ENTER)
        self.unit()
        self.timesleep()
        guanjianci_num = 0
        soup_browser = BeautifulSoup(self.browser.page_source, 'lxml')
        self.timesleep()
        results = soup_browser.find('div', id='results')
        sleep(1)
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
                        print('匹配的百度知道链接 ------------ ',zhidao_url,order)
                        # 获取当前url
                        data_temp = {
                            'client_user_id': user_id,
                            'is_pause': 0,
                            'url': zhidao_url
                        }
                        # 请求接口判断是否为自己的链接 如果是自己的链接 返回答案
                        ret_panduan = requests.post(self.panduan_url, data=data_temp)
                        if ret_panduan:
                            print('与自己链接匹配的知道url 与order=============----> ', zhidao_url, order)
                            ret_json = ret_panduan.content.decode()
                            str_ret = json.loads(ret_json)
                            daan_str = str_ret['data']['content'][0]
                            daan_list = []
                            if daan_str:
                                # 如果返回答案 请求知道链接
                                ret = requests.get(zhidao_url)
                                self.timesleep()
                                ret.encoding = 'gbk'
                                soup = BeautifulSoup(ret.text, 'lxml')
                                self.timesleep()
                                # 获取知道链接 最佳答案
                                div_tag_wrap = soup.find('div', class_='line content')
                                zhidao_zuijia_daan = div_tag_wrap.find('pre').get_text().strip()
                                daan_list.append(zhidao_zuijia_daan)
                                # 获取知道链接 其他答案
                                div_bd_tag = soup.find('div', id='wgt-answers')
                                div_tags = div_bd_tag.find_all('span', class_='con')
                                for div_tag in div_tags:
                                    zhidao_daan = div_tag.get_text().strip()
                                    daan_list.append(zhidao_daan)
                                print('自己的答案 ----- ------------ >',str(daan_str))

                            if daan_str in [i for i in daan_list]:
                                get_text = result.find('h3').get_text()
                                print('获取标题元素定位 ----  ---  --- > ',get_text)
                                print('---下拉--截第一张屏---')
                                if order == 1:
                                    self.browser.get_screenshot_as_file(
                                        './picture/' + keyword + '--1--' + '{guanjianci_num}.png'.format(
                                            guanjianci_num=guanjianci_num))
                                else:
                                    print('else ----- ')
                                    sleep(2)
                                    location_y = self.browser.find_element_by_link_text(get_text)
                                    print('第一张截屏 y轴 --------- >',location_y.location['y'])
                                    js = "window.scrollTo(0,{})".format(int(location_y.location['y'] - 180))
                                    self.browser.execute_script(js)
                                    sleep(1)
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


                                # 请求链接 --------
                                self.timesleep()
                                self.browser.get(zhidao_url)

                                sleep(2)

                                try:
                                    print('删除为什么')
                                    js = "document.getElementsByClassName('fold-num-why-btn')[0].remove()"
                                    self.browser.execute_script(js)
                                except WebDriverException:
                                    print('没有为什么')
                                sleep(2)
                                print('判断是否有更多回答，有则点击')
                                try:
                                    Action = TouchActions(self.browser)
                                    # div_tag = driver.find_element_by_class_name('show-more-replies wgt-replies-entry-btn')
                                    div_tag = self.browser.find_element_by_class_name('wgt-replies-entry')
                                    time.sleep(2)
                                    Action.tap(div_tag).perform()
                                except InvalidSelectorException:
                                    print("没有找到更多回答的按钮")

                                sleep(2)
                                try:
                                    print('删除为什么')
                                    js = "document.getElementsByClassName('fold-num-why-btn')[0].remove()"
                                    self.browser.execute_script(js)
                                except WebDriverException:
                                    print('没有为什么')

                                sleep(2)
                                try:
                                    Action = TouchActions(self.browser)
                                    # div_tag = driver.find_element_by_class_name('show-more-replies wgt-replies-entry-btn')
                                    div_tag = self.browser.find_element_by_class_name('wgt-replies-entry')
                                    sleep(2)
                                    Action.tap(div_tag).perform()
                                except InvalidSelectorException:
                                    print("没有找到更多回答的按钮")
                                sleep(2)
                                try:
                                    print('判断是否有折叠回答')
                                    Action = TouchActions(self.browser)
                                    div_tags = self.browser.find_element_by_class_name('wgt-replies-entry')
                                    sleep(2)
                                    Action.tap(div_tags).perform()
                                except InvalidSelectorException:
                                    print('没有折叠回答')

                                # 获取页面内容
                                ret = self.browser.page_source
                                soup = BeautifulSoup(ret, 'lxml')
                                id_tag = soup.find('div', class_='question-container')
                                # 获取最佳答案
                                div_tag = id_tag.find('div', class_='best-answer-container')
                                div_zuijia_daan = div_tag.find('div',class_='full-content').get_text()
                                print('最佳答案 -------- > ',div_zuijia_daan)
                                # 获取其他答案
                                div_wgts = id_tag.find_all('div', class_='w-reply-container w-reply-item-normal')
                                # 判断自己答案是否为最佳答案
                                if daan_str in div_zuijia_daan:
                                    print('自己答案 为 最佳答案')
                                    js = """$('.best-answer-container').css({"border":"3px solid red"})"""
                                    self.browser.execute_script(js)
                                    self.timesleep()
                                    self.browser.get_screenshot_as_file(
                                        './picture/' + keyword + '--3--' + '{guanjianci_num}.png'.format(
                                            guanjianci_num=guanjianci_num))

                                # 遍历 其他答案 判断是否为 其他答案
                                div_qita_daan = ''
                                for div_wgt in div_wgts:
                                    div_qita_daan = div_wgt.find('div',class_='full-content').get_text()
                                if daan_str in div_qita_daan:
                                    print('自己答案 为 其他答案- -------- > ',div_qita_daan)
                                    location_y = self.browser.find_element_by_class_name('fold-num-container')
                                    print('第三张截屏 y轴',location_y.location['y'])
                                    js = "window.scrollTo(0,{})".format(int(location_y.location['y']))
                                    self.browser.execute_script(js)
                                    self.timesleep()
                                    js = """$('.full-content').eq(1).css({"border":"3px solid red"})"""
                                    self.browser.execute_script(js)
                                    js = """$('.full-content').eq(2).css({"border":"3px solid red"})"""
                                    self.browser.execute_script(js)
                                    sleep(2)
                                    self.browser.get_screenshot_as_file(
                                        './picture/' + keyword + '--3--' + '{guanjianci_num}.png'.format(
                                            guanjianci_num=guanjianci_num))


                                jieping_1 = open('./picture/' + keyword + '--1--' + '{guanjianci_num}.png'.format(
                                    guanjianci_num=guanjianci_num), 'rb').read()

                                jieping_2 = open('./picture/' + keyword + '--2--' + '{guanjianci_num}.png'.format(
                                    guanjianci_num=guanjianci_num), 'rb').read()

                                jieping_3 = open('./picture/' + keyword + '--3--' + '{guanjianci_num}.png'.format(
                                    guanjianci_num=guanjianci_num), 'rb').read()
                                if jieping_1 and jieping_2 and jieping_3:
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
                                    requests.post(self.jieping_url, data=data_temp)
                                    print('存入数据库------>',keyword)
                                    sleep(2)
                                    self.browser.back()
                                    guanjianci_num += 2
                else:
                    continue
            except Exception as e:
                print('错误------》 ',e)
                # pass


    def __del__(self):
        sleep(5)
        self.browser.quit()

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
    # print('开始')
    # # url = "http://127.0.0.1:8006/api/fifty_guanjianci_fabu"
    # url = "http://wenda.zhugeyingxiao.com/api/fifty_guanjianci_fabu"
    # ret = requests.get(url)
    # if ret:
    #     json_ret = ret.content.decode()
    #     str_ret = json.loads(json_ret)
    #     print(str_ret)
    #     if str_ret['data']:
    #         ret_data = str_ret['data']
    #         GuanJianCi(ret_data).run()
    #         print(input('按任意键结束任务----->:'))

    while True:
        # url = 'http://wenda.zhugeyingxiao.com/test/api/fifty_guanjianci_fabu'
        url = 'http://wenda.zhugeyingxiao.com/api/fifty_guanjianci_fabu'
        # url = "http://127.0.0.1:8006/api/fifty_guanjianci_fabu"
        # canshu_url = 'http://wenda.zhugeyingxiao.com/test/api/fifty_guanjianci_fabu?canshu=2'
        canshu_url = 'http://wenda.zhugeyingxiao.com/api/fifty_guanjianci_fabu?canshu=2'
        # canshu_url = "http://127.0.0.1:8006/api/fifty_guanjianci_fabu?canshu=2"
        ret = requests.get(url)
        if ret:
            json_ret = ret.content.decode()
            str_ret = json.loads(json_ret)
            # print('str_ret ============ >',str_ret)
            if str_ret['data']:
                ret_data = str_ret['data']
                GuanJianCi(ret_data).run()

            else:
                # print('===== canshu=2 =====')
                ret = requests.get(canshu_url)
                if ret:
                    json_ret = ret.content.decode()
                    str_ret = json.loads(json_ret)
                    # print('str_ret  - ->', str_ret)
                    if str_ret['data']:
                        ret_data = str_ret['data']
                        GuanJianCi(ret_data).run()
                sleep_time = 60 * 5
                sleep(sleep_time)
                # print('===重新执行===')

        else:
            # print('===== canshu=2 =====')
            ret = requests.get(canshu_url)
            if ret:
                json_ret = ret.content.decode()
                str_ret = json.loads(json_ret)
                # print('str_ret  - ->', str_ret)
                if str_ret['data']:
                    ret_data = str_ret['data']
                    GuanJianCi(ret_data).run()
            sleep_time = 60 * 5
            sleep(sleep_time)
            print('===重新执行===')
huoqu_guanjianci()
