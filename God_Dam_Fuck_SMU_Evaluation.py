#!/usr/bin/env python3
# -*- coding:utf-8 -*-
###
# #    File: God Dam Fcuk SMU Evalation
# #    Project: God Dam Fuck SMU Evaluation
# #    Author: zzy
# #    mail: elliot.bia.8989@outlook.com
# #    github: https://github.com/elliot-bia
# #    Date: 2019-10-17 10:53:02
# #    Editors: zzy
# #    EditTime: 2019-10-23 15:31:10
# #    LastEditors: Jayce丶H
# #    github: https://github.com/Jayce-H
# #    LastEditTime: 2021-10-19 00:22:15
# #    Description: 用于SMU每日的课程评价
# #    ---------------------------------
# #    更新日志：
# #    2021-10-19:
# #    1、可自定义百度OCR相关设置APP_ID API_KEY SECRET_KEY
# #    默认识别模式为：高精度文字识别模式，不可更改！
# #    需手动在配置文件中添加[AipOcr]项，如下：
# #    [AipOcr]
# #    APP_ID=
# #    API_KEY=
# #    SECRET_KEY=
# #    ---------------------------------
# #    2021-10-18:
# #    1、适配Mac，修复无法读取location的bug
# #    已知问题：mac可能会出现无法crop图片的错误，待完善
# #    ---------------------------------
# #    2021-10-17：
# #    1、新增日志输出开关
# #    2、新增自定义评价分数
# #    可通过修改配置文件自定义想评价的分数
# #    3、基础代码变更
# #    Mac上无法使用以下命令
# #    driver.find_element_by_id(element)
# #    driver.find_element_by_class_name(element)
# #    全部替换为:
# #    driver.find_element(By.ID,element)
# #    driver.find_element(By.CLASS_NAME,element)
# #    4、由于win系统DPI缩放问题，导致截取验证码失败
# #    配置文件添加DPI项，保证验证码截图正确
# #    ---------------------------------
# #    2021-10-15：
# #    1、输出日志每行开头添加时间戳
# #    代码中所有 print(a,b)格式 调整为 print(str(a) + str(b))格式
# #    2、判断操作系统决定浏览器
# #    Windows为Edge，Mac为Safari，Linux为Chrome
# #    3、添加验证码OCR识别并填入，采用百度免费OCR
# #    识别错误会自动重新识别填入，直至正确为止
# #    ---------------------------------
# #    2021-10-06：
# #    1、读取本地配置，自动填入学号密码，缩短等待时间
# #    ---------------------------------
# #    2021-09-17：
# #    1.新增筛选当日未评价课程，避免重复post
# #    2.删除了问题类型3随机选取文本的功能，改为跳过不填
# #    3.更新了部分参数，原参数已不再适用
# #    4.随机评分从5星4星更改为4星3星，最高得分从100分更改为80分
# #    ---------------------------------
###


import sys
import aip
import requests
import json
import re
import datetime
# from datetime import date, timedelta, datetime
# from getch import pause


# get cookies
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time

# Download类
from urllib.parse import urlparse
# from datetime import datetime
from requests.exceptions import RequestException

# html解析
from bs4 import BeautifulSoup, element
import random

# 百度OCR识别 图片打开 文件删除
from aip import AipOcr, base
from os import path
from PIL import Image

import os
from selenium.webdriver.common.by import By

# 显性等待
from selenium.webdriver.support.wait import WebDriverWait

# 配置文件读取
import configparser

# 判断操作系统
import platform

account = ''                     # 初始化账号
pwd = ''                         # 初始化密码
ini=configparser.ConfigParser()  # 配置文件
layer = 2                        # 初始化验证码错误弹窗元素
dpi = 125                        # 默认dpi为125
syst = platform.system()         #获取当前操作系统
base_url = 'http://zhjw.smu.edu.cn'
path1 = '页面截图.png'
path2 = '验证码.png'
global driver   # 全局变量声明
driver = webdriver
# 定义自定义评价参数 getcustom(randnum,indexnum)
global randnum
randnum = 1
global indexnum
indexnum = -1
global values
values = []
bdocr = 0
if (os.path.exists('config.ini')):
    # 打开并读取配置文件
    ini.read("config.ini")
    account = ini.get('User' , 'Account')
    pwd = ini.get('User' , 'Password')
    logout = int(ini.get('Settings' , 'Log'))
    custom = int(ini.get('Settings','Custom'))
    dpi = int(ini.get('Settings','DPI'))
    customnum = ini.get("Custom",'Num')             # 获取自定义评价所有情况的数量
    # 检测是否自定义OCR
    try:
        APPID = ini.get('AipOcr','APP_ID')
        APPIKEY = ini.get('AipOcr','API_KEY')
        SECRETKEY = ini.get('AipOcr','SECRET_KEY')
        bdocr = 1
    except:
        bdocr = 0
    if account == '':
        auto = False
        waittime = 30
    else:
        auto = True
        waittime = 1
else :  # 首次运行输出配置文件
    auto = False
    waittime = 30
    logout = 1
    custom = 0
    with open('config.ini','w+') as f: 
        f.write('[User]\nAccount=\nPassword=\n\n[Settings]\nLog=1\nCustom=1\nDPI=125\
\n\n[Custom]\nNum=8\n1=4 4 4 3\n2=4 4 3 4\n3=4 3 4 4\n4=3 4 4 4\n5=4 4 4 4\n6=4 4 4 \
4\n7=4 4 4 4\n8=4 4 4 4\n\n[Info]\nUser说明=教务系统账号与密码\nSettings说明1=Log为日\
志输出开关，1为开，0为关\nSettings说明2=Custom为自定义评价开关，1为开，0为关\nSettings说\
明3=DPI为系统DPI缩放值，用于确保验证码截图位置准确\nCustom说明=自定义评价项，Num表示所有\
情况总数，每个序号表示一种情况，示例中给出8种情况，每种情况的值表示每道题的星数，如4443表\
示第一二三题4星，第四题3星，即得分为20+20+20+15=75分，第5 6 7 8情况相同，用来增加4444评\
价的概率，现配置得分概率：75分  二分之一，80分  二分之一，可自行添加修改')


headers = {
    'Host': "zhjw.smu.edu.cn",
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:69.0) Gecko/20100101 Firefox/69.0',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'X-Requested-With': 'XMLHttpRequest'

}

class Logger(object):
    def __init__(self, filename='default.log', stream=sys.stdout):
        self.terminal = stream
        self.log = open(filename, 'a')
    def write(self, message):
        self.terminal.write(message)
        if message == '\n':
            self.log.write(message)
        elif message == '':
            self.log.write(message)
        else:
            self.log.write("[%s]" %str(datetime.datetime.now()) + message)
    def flush(self):
        pass

class Downloader:
    """
    Description 描述:  因为下载用的多, 这里写成一个类, 顺便把访问过的域名延时加进来\n
    param 传参:  headers, cookies, num_retries, proxies, delay, timeout \n
    exception 异常处理:  None\n
    return 返回值: content内容或json
    """

    def __init__(self, headers=None, cookies=None, num_retries=3, proxies=None, delay=2, timeout=30):
        self.headers = headers
        self.cookies = cookies
        self.num_retries = num_retries
        self.proxies = proxies
        self.timeout = timeout

        # 延迟时间，避免访问过快
        self.delay = delay
        # 用字典保存访问某域名的时间
        self.domains = {}

    def wait(self, url):
        """
        Description 描述:  对访问过的域名添加延迟时间 \n
        param 传参:  url, delay \n
        exception 异常处理:  None \n
        return 返回值: None
        """
        # urlparse是对url进行操作的库, 这里获得域名
        domain = urlparse(url).netloc
        # 获取上次访问的时间
        last_accessed = self.domains.get(domain)
        if self.delay > 0 and last_accessed is not None:
            # 时间相减, 大于0就等待
            sleep_secs = self.delay - \
                (datetime.datetime.now() - last_accessed).seconds
            if sleep_secs > 0:
                time.sleep(sleep_secs)
        self.domains[domain] = datetime.datetime.now()

    def download(self, url, params=None, down_type=1, is_json=False, data=None):
        """
        Description 描述:  下载url内容 \n
        param 传参:   url, down_type: 1是get 2是post, is_json, data\n
        exception 异常处理:  非200进行异常处理 \n
        return 返回值: content或者json
        """
        print("下载页面: " + url)
        self.wait(url)
        try:
            # 如果是get类型
            if down_type == 1:
                response = requests.get(url, params=params, headers=self.headers,
                                        cookies=self.cookies, proxies=self.proxies, timeout=self.timeout)
            # 如果是post
            elif down_type == 2:
                response = requests.post(url, data=data, headers=self.headers,
                                         cookies=self.cookies, proxies=self.proxies, timeout=self.timeout)
            else:
                print("出错, 传参仅允许get(1), post(2)")
            if response.status_code == 200:
                print('状态码： 200')
                if is_json:
                    return response.json()
                else:
                    return response.content
            elif response.status_code == 401:
                print("出错!, 请检查登录是否正确!")
                print(response)
            return None
        except RequestException as e:
            print('error: ' + str(e.response))
            html = ''
            if hasattr(e.response, 'status_code'):
                code = e.response.status_code
                print('error code: ' + str(code))
                if self.num_retries > 0 and 500 <= code < 600:
                    # 遇到 5xx 错误就重试
                    html = self.download(url, down_type, is_json, data)
                    self.num_retries -= 10
            else:
                code = None
        return html

    def deal_num_evaluations(self):
        """
        Description 描述: 下载今日份的评价信息  \n
        param 传参:  None  \n
        exception 异常处理:  1, 若当天无课程返回None 2, 未登录成功退出 \n
        return 返回值: 带 数字, teadm, dgksdm的列表, 如{1: {'teadm': '201109006', 'dgksdm': '1498570'}, 2: {'teadm': '000002644', 'dgksdm': '1526196'}}
        """
        url = "http://zhjw.smu.edu.cn/new/student/ktpj/xsktpjData"
        today = datetime.date.today()
        yesterday = today - datetime.timedelta(days=1)
        data = {
            # 获取今日份日期
            "jsrq": yesterday,
            # "jsrq": "2019-10-16",
            # "jsrq": "2021-09-17",
            "page": "1",
            "rows": "20",
            "sort": "jcdm2",
            "order": "desc"
        }
        # 处理信息
        json_data = self.download(url, down_type=2, is_json=True, data=data)

        question_list = {}
        try:
            print(str(data['jsrq']) + f" 课堂评价总共 {json_data['total']} 份")
            for i in json_data['rows']:
                temp = {}
                ###
                if i['pjdm'] == '' :   #筛选未评价的课程
                    temp['teadm'] = i['teadm']
                    temp['dgksdm'] = i['dgksdm']
                    question_list[i['rownum_']] = temp
                    print(f"第{i['rownum_']}份： " + str(temp))
                else:
                    print(f"第{i['rownum_']}份已评价")
                ###
            ''' 原来的版本
                temp['teadm'] = i['teadm']
                temp['dgksdm'] = i['dgksdm']
                question_list[i['rownum_']] = temp
                print(temp)
                print('temp +1')
                print()
            '''
            print('')
            return question_list

        except Exception as e:
            print('出错: ' + str(e) )
            print(json_data)

    def get_html_question(self, info_list):
        """
        Description 描述:  下载html文档 \n
        param 传参:   \n
        exception 异常处理: None  \n
        return 返回值: 返回html文档
        """

        url = 'http://zhjw.smu.edu.cn/new/student/ktpj/showXsktpjwj.page?'
        
        question_params = {
            'pjlxdm': 6,
            'teadm': info_list['teadm'],
            'dgksdm': info_list['dgksdm'],
            'wjdm': 10003019,
            '_': 1631806763283
        }
        # print(info_list)
        # print(question_params)
        html_content = self.download(url, params=question_params, down_type=1, is_json=False)
        # html_content.decode()
        #print(html_content)
        return html_content.decode('utf-8')

    def post_question(self, post_content):
        """
        Description 描述:  发送问卷啊 \n
        param 传参:  url_params, post_content \n
        exception 异常处理:  None \n
        return 返回值: None
        """
        url = 'http://zhjw.smu.edu.cn/new/student/ktpj/savePj'
        
        self.download(url, down_type=2, data=post_content)
        print("post包发送成功, 请检查!")
        print('')
        



class Html_Parse:
    """
    Description 描述: 解析html内容, 返回post包的内容  \n
    param 传参:  html文档 \n
    exception 异常处理:  None \n
    return 返回值: url和dt列表, 还有一个分值
    """





    def get_url_params(self, soup):
        """
        Description 描述: 找到url的参数, 返回字典  \n
        param 传参:  soup \n
        exception 异常处理:  None \n
        return 返回值:  params的字典
        """
        #print("get url start!")
        # 找到tag的txt内容
        pattern = re.compile(r"/new/student/ktpj/savePj\'")
        target = soup.find("script", text=pattern).get_text()
        
        # 提取参数内容
        content_pattern = re.compile(r'/new/student/ktpj/savePj\',\s*{([\s\S]*?)wtpf')
        # 臭弟弟, match是从头开始匹配, 垃圾东西, 淦
        content = content_pattern.findall(target)

        # 提取参数内容后转换成字典
        params_single = re.compile(u'(\w*):\'(\d*|[\u4e00-\u9fa5]*)\'')  # 同时匹配中文
        # 转换成str
        str4 = "".join(content)
        # 找到参数, re分组
        params_all = params_single.findall(str4)
        # 弄成字典后返回
        dit = {}
        for k,v in params_all:
            print(str(k) + str(v))
            dit[k] = v
            #print(type(v))
            
        print("get_url_params done!")
        return dit


    def distinguish_question_type5(self, child):
        """
        Description 描述: 用来类型是5的选择问卷, 按照概率返回4星评价, 返回一个字典  \n
        param 传参:  html内容 \n
        exception 异常处理:  None \n
        return 返回值:  分数 和 字典包含txdm等
        """
        # 每份问卷3个类型5选择, 概率为1/10会出现一个75分
        # values = [20.0, 20.0, 20.0, 20.0, 20.0, 20.0, 20.0, 20.0, 20.0, 15.0]
        # probability_num = random.choice(values)

        # 如果配置文件存在，更改为读取配置文件进行评价，否则按系统默认执行
        global indexnum
        global values
        if auto:
            if custom == 1:   # 如果配置文件custom开关打开
                # 获取自定义评分 第randnum行的第child个评分 一份问卷多个问题randnum值不变
                probability_num = values[indexnum]
                print("自定义：pribability_num:" + str(probability_num))
            else:
                values = [4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 3]
                probability_num = random.choice(values)
        else:
            values = [4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 3]
            probability_num = random.choice(values)

        return_dict = {}
        if probability_num == 5:
            print("5星评价")
            zbxmdm_pattern = re.compile(r"\"fzbl\":40.0[\s\S]*zbxmdm\":\"(\d*)\"")
            zbxmdm = zbxmdm_pattern.findall(str(child))
            fz = 25
            dtjg = '★★★★★'
            # 写入字典
            return_dict['zbxmdm'] = zbxmdm[0]
            return_dict['fz'] = fz
            return_dict['dtjg'] = dtjg
            return return_dict, fz
        
        if probability_num == 4:
            print("4星评价")
            zbxmdm_pattern = re.compile(r"\"fzbl\":20.0[\s\S]*zbxmdm\":\"(\d*)\"")
            zbxmdm = zbxmdm_pattern.findall(str(child))
            fz = 20
            dtjg = '★★★★'
            # 写入字典
            return_dict['zbxmdm'] = zbxmdm[0]
            return_dict['fz'] = fz
            return_dict['dtjg'] = dtjg
            return return_dict, fz

        if probability_num == 3:
            print("3星评价")
            zbxmdm_pattern = re.compile(r"\"fzbl\":40.0[\s\S]*zbxmdm\":\"(\d*)\"")
            zbxmdm = zbxmdm_pattern.findall(str(child))
            fz = 15
            dtjg = '★★★'
            # 写入字典
            return_dict['zbxmdm'] = zbxmdm[0]
            return_dict['fz'] = fz
            return_dict['dtjg'] = dtjg
            return return_dict, fz
        
        if probability_num == 2:
            print("2星评价")
            zbxmdm_pattern = re.compile(r"\"fzbl\":40.0[\s\S]*zbxmdm\":\"(\d*)\"")
            zbxmdm = zbxmdm_pattern.findall(str(child))
            fz = 10
            dtjg = '★★'
            # 写入字典
            return_dict['zbxmdm'] = zbxmdm[0]
            return_dict['fz'] = fz
            return_dict['dtjg'] = dtjg
            return return_dict, fz        
  
        if probability_num == 1:
            print("1星评价")
            zbxmdm_pattern = re.compile(r"\"fzbl\":40.0[\s\S]*zbxmdm\":\"(\d*)\"")
            zbxmdm = zbxmdm_pattern.findall(str(child))
            fz = 5
            dtjg = '★'
            # 写入字典
            return_dict['zbxmdm'] = zbxmdm[0]
            return_dict['fz'] = fz
            return_dict['dtjg'] = dtjg
            return return_dict, fz
   
    def distinguish_question_type1(self, child):
        """
        Description 描述:  处理类型是1的问卷, 返回zbxmdm, fz 和 dtjg, 返回值写死  \n
        param 传参:  html内容 \n
        exception 异常处理: None  \n
        return 返回值: zbxmdm, fz 和 dtjg
        """
        return_dict = {}

        zbxmdm_pattern = re.compile(r"[\s\S]*是[\s\S]*value=\"(\d*)\"[\s\S]*否")
        zbxmdm = zbxmdm_pattern.findall(str(child))
        # print(zbxmdm)
        fz = 0
        dtjg = "否"
        # 写入字典
        return_dict['zbxmdm'] = zbxmdm[0]
        return_dict['fz'] = fz
        return_dict['dtjg'] = dtjg
        return return_dict

    '''
    def content_from_txt(self):
        """
        Description 描述:  随机读取txt文本的一行 \n
        param 传参:  None \n
        exception 异常处理: None  \n
        return 返回值: 评价字符串
        """
        # 文本list
        content_list = []
        with open('./content.txt', 'rt', encoding='utf-8') as f:
            for lines in f:
                content_list.append(lines.strip())
        # print(random.choice(content_list))
        return random.choice(content_list)

    def distinguish_question_type3(self, child):
        """
        Description 描述: 返回自定义评价 \n
        param 传参:  html内容 \n
        exception 异常处理:  None \n
        return 返回值:  fz和自定义评价
        """
        return_dict = {}
        fz = 0
        #dtjg = self.content_from_txt()
        dtjg = ""
        return_dict['fz'] = fz
        return_dict['dtjg'] = dtjg
        return return_dict
    '''

    def get_dt_content(self, soup):
        """
        Description 描述:  获取post包的dt内容 \n
        param 传参:  soup \n
        exception 异常处理:  None \n
        return 返回值: 分数 和 dt的txdm的等参数的字典
        """
        global randnum
        global indexnum
        global values
        #print("get dt start")
        # all_content = soup.find('input', id='thisSchoolIsSMU')
        all_content = soup.find_all('div', class_='question')
        
        # 定义所有的问题回答
        all_question_reply_info = []
        # 定义返回值的分数
        score = 0
        for child in all_content:
            # print(child)
            # print('-' * 30)

            # 定义单个问题的回答
            single_question_reply_info = {}


            # 还是正则, 烦死
            txdm_pattern = re.compile(r"data-txdm=\"(\d)\"")
            zbdm_pattern = re.compile(r"data-zbdm=\"(\d*|\w*)\">")
            zbmc_pattern = re.compile(r"<h3>([\s\S]*|[\u4e00-\u9fa5]*)</h3>")

            txdm = txdm_pattern.findall(str(child))
            zbdm = zbdm_pattern.findall(str(child))
            zbmc = zbmc_pattern.findall(str(child))
            print("问题类型 txdm[0]= " + txdm[0])
            #print(type(txdm[0]))
            #print("int(txdm[0])",int(txdm[0]))
            #print(type(int(txdm[0])))
            print("zbmc " + str(zbmc))
            print("zbdm " + str(zbdm))
            
            single_question_reply_info['txdm'] = int(txdm[0]) # 这里要数字
            single_question_reply_info['zbdm'] = zbdm[0]
            single_question_reply_info['zbmc'] = zbmc[0]



            # 进行分流, 如果匹配了, 说明是一种类型
            if txdm[0] == '5':
                if custom == 1:
                    indexnum += 1
                    print("自定义：选取randnum第 " + str(randnum) + " 项" + str(values) + "的第 "+str(indexnum + 1) + " 个indexnum评价分数")
                diff_content5, score_temp = self.distinguish_question_type5(child)
                #print("score_temp",score_temp)
                score = score_temp + score
                single_question_reply_info.update(diff_content5)
            elif txdm[0] == '1':
                diff_content1 = self.distinguish_question_type1(child)
                single_question_reply_info.update(diff_content1)
            elif txdm[0] == '3':  # skip
                print("不填跳过 skip")
                #diff_content3 = self.distinguish_question_type3(child)
                #single_question_reply_info.update(diff_content3)
            else:
                print("else")
                print("正则匹配出错, 请检查以下内容: " + str(child))
            all_question_reply_info.append(single_question_reply_info)
        print("得分 score: " + str(score))
        # print("")
        # print(all_question_reply_info)
        print("get_dt_content done!")
        return score, json.dumps(all_question_reply_info)
            

    def html_pares_index(self, html_content):
        """
        Description 描述:  这个类的执行顺序 \n
        param 传参:  html内容  \n
        exception 异常处理: None  \n
        return 返回值: url的params_data 和 dt的list
        """

        soup = BeautifulSoup(html_content, "lxml")
        # 这里全是post数据, 函数名字 搞错了
        post_data = self.get_url_params(soup)
        score, dt_list = self.get_dt_content(soup)
        post_data['wtpf'] = score
        post_data['dt'] = dt_list
        # print("解析结果".center(30, '-'))
        # print(post_data)
        # print(post_data)
        return post_data

def fill_keys(elem, keys):
    "用来填充字节"
    # 清空内容
    elem.click()
    elem.clear()
    # 发送key
    elem.send_keys(keys)

def login_get_cookies():
    """
    Description 描述: 手动登录, 然后获取cookie后关闭窗口\n
    param 传参: None \n
    return 返回值: cookies
    """
    global driver
    # 最大化窗口
    driver.maximize_window()
    driver.implicitly_wait(10)
    # 打开网址
    driver.get("http://zhjw.smu.edu.cn/")
    time.sleep(1)

    # 找到验证码 输入空 用于获取验证码图片
    # elem_vercode = driver.find_element(By.ID,"L_vercode")
    elem_vercode = driver.find_element(By.ID,"L_vercode")
    fill_keys(elem_vercode, "")
    
    # 找到密码登录
    # elem_pwd = driver.find_element(By.ID,"L_pass")
    elem_pwd = driver.find_element(By.ID,"L_pass")
    fill_keys(elem_pwd, pwd)
    
    # 找到账号登录
    # elem_acc = driver.find_element(By.ID,"L_account")
    elem_acc = driver.find_element(By.ID,"L_account")
    fill_keys(elem_acc, account)

    # OCR识别验证码 并且登录 判断验证码是否正确 错误则递归循环OCR识别
    # layui-layer2 4 6为验证码错误时的弹窗id
    checkocr('layui-layer',2)

    # 显性等待 等待登陆成功
    try:
        # 等待登录页面特定元件消失，判断是否登录成功
        WebDriverWait(driver,waittime).until_not(lambda x: isEleExist.idn("L_vercode"))
        print("登录成功！")
    except  Exception as e:
        print('登录超时！未在指定时间内完成登录！')
        print(e)
        sys.exit()      
    else:
        cookies = driver.get_cookies()
        # print(cookies)
        # 关闭窗口
        driver.quit()
        # 这里返回值为[{'domain': 'zhjw.smu.edu.cn', 'httpOnly': True, 'name': 'JSESSIONID', 'path': '/', 'secure': False, 'value': '2B583913425880224DD86D176C95D294'}]
        # 只取value 的值
        return cookies[0]['value']

# 判断元素是否存在
class isEleExist():
    def idn(element):
        try:
            # driver.find_element_by_id(element)
            driver.find_element(By.ID,element)
            print("id元素： " + str(element) + " 存在")
            return True
        except:
            print("未检测到id元素： " + str(element))
            return False
    def classname(element):
        try:
            # driver.find_element_by_class_name(element)
            driver.find_element(By.CLASS_NAME,element)
            print("class_name元素： " + str(element) + " 存在")
            return True
        except:
            print("未检测到class_name元素： " + str(element))
            return False

# OCR识别验证码 并且登录 判断验证码是否正确 错误则递归循环OCR识别
def checkocr(ele,layer):
    global driver
    ocr()
    time.sleep(1)
    if auto:
        if isEleExist.idn(ele + str(layer)):
            print("验证码错误，正在重试...")
            layer += 2
            # 点击确定
            # elem_err = driver.find_element_by_class_name("layui-layer-btn0")
            elem_err = driver.find_element(By.CLASS_NAME,"layui-layer-btn0")
            elem_err.click()
            checkocr(ele,layer)
        else:
            print("验证码正确")
    else:
        print("无法读取配置信息，自动填入登录停止")
        print("请在 " + str(waittime) + " 秒内完成手动登录")

# 验证码识别
def ocr():
    global driver
    # 页面截图保存至本地
    driver.save_screenshot(path1)
    print('页面截图保存')
    image = Image.open(path1)

    # 获取验证码位置 裁切页面截图
    # 元素提取受电脑缩放比例影响 缩放比例100%可以使用以下代码
    # 更新为适配DPI，坐标乘DPI即可
    # '''
    code_element = driver.find_element(By.ID,'captcha')
    print('验证码x坐标：' + str(code_element.get_attribute("x")))
    print('验证码y坐标：' + str(code_element.get_attribute("y")))
    print('验证码大小：' + str(code_element.size))
    left = code_element.get_attribute("x")
    top = code_element.get_attribute("y")
    width = code_element.size['width']
    height = code_element.size['height']
    print(left + ' '+ top + ' ' + str(width + int(left)) + ' ' + str(height + int(top)))
    right = width * dpi / 100 + int(left)
    down = height * dpi / 100 + int(top)
    print("DPI为" + str(dpi) +"% 适配DPI后坐标为：")
    print(left + ' ' + top + ' ' + str(right) + ' ' + str(down))
    code_image = image.crop((int(left), int(top), right, down))
    # 保存验证码截图
    code_image.save(path2)
    print('验证码图片保存')
    # '''
    # 改为绝对位置裁切 当前使用 分辨率1920*1080 缩放比例125%
    # code_image = image.crop((1502,451,1633,496))  # window
    # code_image = image.crop((620,353,725,389))    # mac_vmware
    '''
    # mac_vmware无法使用crop裁切图片，原因不明......
    # 换OpenCV2进行裁切，需在文件头添加 import cv2
    image = cv2.imread(path1)
    code_image = image[int(top) : down, int(left) : right]
    cv2.imwrite(path2, code_image)
    '''

    ##################################################
    # 验证码识别：
    # 以下内容由百度OCR文档提供
    # 文档地址：https://cloud.baidu.com/doc/OCR/s/7kibizyfm
    # ！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！
    # 此共享账号每日调用量有上限，若调用数已满，则请自主申请账号修改参数信息
    # ！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！
    """ 你的 APPID AK SK """
    APP_ID = '25006301'
    API_KEY = 'dW4FImxGiaVAnDaFaOpavKFk'
    SECRET_KEY = 'bgw0vp2xePn5IrWEG9Zs5yCG53OwFFdm'
    if bdocr == 1:
        client = AipOcr(APPID, APPIKEY, SECRETKEY)
        print("更改AipOcr APP_ID:" + str(APPID) + "，程序默认APP_ID为:" + str(APP_ID))
    else:
        client = AipOcr(APP_ID, API_KEY, SECRET_KEY)
    # url = 'http://zhjw.smu.edu.cn/yzm'
    i = open(path2,'rb')
    img = i.read()
    print('验证码自动识别中')

    '''
    # 带参数调用通用文字识别, 远程url图片可选参数
    options = {}
    options["language_type"] = "ENG"
    options["detect_direction"] = "true"
    options["detect_language"] = "true"
    options["probability"] = "false"   
    # 带参数调用通用文字识别, 图片参数为远程url图片
    mesage = client.basicGeneralUrl(url, options)
    '''
    # 带参数调用高精度文字识别
    mesage = client.basicAccurate(img)
    print('返回结果：\n' + str(mesage))
    i.close()

    # 读取识别结果
    if mesage.get('words_result'):
        for text in mesage.get('words_result'):
            yzm = text.get('words')
            print('OCR识别成功！')
            print('初始结果：' + str(yzm))
            print('纠正识别结果')
            newStr = ''.join(list(filter(str.isalnum,yzm))) # 去除特殊字符和空格，只保留数字和英文字符
            yzm = newStr.lower() # 大写变小写
            print('最终结果：' + str(yzm))
            # 找到验证码输入
            fill_keys(driver.find_element(By.ID,"L_vercode"),yzm)
            # 键入回车
            # elem_vercode.send_keys(Keys.RETURN)
            # 点击登录 读取配置文件失败则不点击登录
            if auto:
                # elem_button = driver.find_element_by_class_name("layui-btn")
                elem_button = driver.find_element(By.CLASS_NAME,"layui-btn")
                elem_button.click()
    else:
        if auto:
            print('识别失败！正在重试...')
            time.sleep(1)
            ocr()
        else:
            print('识别失败！')

    # 最后删除保存的图片
    if os.path.exists(path1):  # 如果文件存在
        os.remove(path1)  
        print("删除文件 “%s”" %path1)
    else:
        print('文件  “%s”  不存在' %path1) # 否则返回文件不存在
    if os.path.exists(path2):  # 如果文件存在
        os.remove(path2)
        print("删除文件 “%s”" %path2)
    else:
        print('文件  “%s”  不存在' %path2) # 否则返回文件不存在
    # 验证码识别结束
    ##################################################

def main():
    global driver
    global randnum
    global indexnum
    global values
    if logout == 0:
        print('日志输出已关闭')
    else:
        sys.stdout = Logger('a.log', sys.stdout)
        print('')
        open('a.log','a').write(str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')).center(100,"-") + '\n')

    # 根据操作系统打开对应浏览器
    # 此操作会直接打开浏览器，故在读取完配置文件后再执行
    print("当前操作系统为： " + str(syst))
    if syst == 'Windows':
        try:
           driver = driver.Edge()
        except Exception as e:
           print("未正确安装Edge Driver")
           print(e)
           sys.exit()
    elif syst == 'Darwin' or syst == 'Mac':
        driver = driver.Safari()
    else:
        try:
            driver = driver.Chrome()
        except Exception as e:
            print("未正确安装Chrome Driver")
            print(e)
            sys.exit()
    if bdocr == 1:
        print("已启用自定义AipOcr参数...")
    # 获得JSESSIONID
    JSESSIONID = login_get_cookies()
    if JSESSIONID == '':
        print('获取jsessionid失败')
    else:
        print("成功获取jsessionid: " + JSESSIONID)
        cookies = {'JSESSIONID': JSESSIONID}
        proxies = {"http":"127.0.0.1:8080"}
        Download_Class = Downloader(headers=headers, cookies=cookies)
        # 查看今日份的评价
        question_list = Download_Class.deal_num_evaluations()
    
        # 定义好解析html文档的类
        html_parse_class = Html_Parse()


        # 下载今日份的问卷
        if isinstance(question_list, dict):  # 使用isinstance检测数据类型
            # 遍历字典
            if len(question_list)==0:
                print("当日剩余 0 份未评价")
            else:
                for x in range(len(question_list)): 
                    print("-" * 50)
                    if custom == 1:
                        randnum = random.randrange(1,int(customnum) + 1)     # 随机从1-num里面选一种情况
                        print("自定义：选取第 " + str(randnum) + " 项 randnum")
                        indexnum = -1    # 初始化评价选取序号 
                        print("自定义：初始化评价选取 值values:[ ] 和 序号indexnum:-1")
                        values = []
                        valuenum = ini.get("Custom",str(randnum)) # 获取该情况的value值
                        for i in range(0,4):
                            values.append(int(valuenum.split(" ")[i].strip("\n")))
                        print("自定义：获取第 " + str(randnum) +" 项的值values:" + str(values))
                    temp_key = list(question_list.keys())[x]
                    temp_value = question_list[temp_key]
                    print(str(temp_key) + '： ' + str(temp_value))
                    # 获取了内容
                    html_content = Download_Class.get_html_question(temp_value)
                    # print(html_content)
                    print("现在获取html内容")
            
                    post_data = html_parse_class.html_pares_index(html_content)
                    print("post包解析完成")
                    response = Download_Class.post_question(post_data)
                    # print(response.request.body)
                print('-'*50)
                print("程序执行完成, 请检查结果!")
    print('-'*50)
    print(" CopyRight: z ".center(30, '#'))
    print("            南医大计协本部程设组组长 z")
    print("              如需反馈bug请提交issue")
    print("github: https://github.com/elliot-bia")
    print("All Rights Reserved".center(50))
    print(" CopyRight: z ".center(30, '#'))
    print('-'*50)
    print("Author: zzy".center(50))
    print("github: https://github.com/elliot-bia")
    print("Editors: Jayce丶H".center(50))
    print("github: https://github.com/Jayce-H")
    print("Version3.5.2 2021.10.19".center(50))
    print('-'*50)
    if logout == 1:
        print("日志已写入文件a.log中")
        print("3秒后会自动关闭此窗口")
        print('-'*50)
    print('\n')
    time.sleep(3)

if __name__ == "__main__":
    main()
