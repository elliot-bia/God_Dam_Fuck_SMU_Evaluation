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
# #    LastEditTime: 2021-09-17 19:01:31
# #    ---------------------------------
# #    Description: 用于SMU每日的课程评价
# #    2021-09-17 更新内容：
# #    1.新增筛选当日未评价课程，避免重复post
# #    2.删除了问题类型3随机选取文本的功能，改为跳过不填
# #    3.更新了部分参数，原参数已不再适用
# #    4.随机评分从5星4星更改为4星3星，最高得分从100分更改为80分
###


import sys
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
from bs4 import BeautifulSoup
import random


accout = ""
pwd = ""


# JSESSIONID = '23678641EE74E228911E6F1000D741F4'

headers = {
    'Host': "zhjw.smu.edu.cn",
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:69.0) Gecko/20100101 Firefox/69.0',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'X-Requested-With': 'XMLHttpRequest'

}

# cookies = {'JSESSIONID': JSESSIONID}



class Logger(object):
    def __init__(self, filename='default.log', stream=sys.stdout):
        self.terminal = stream
        self.log = open(filename, 'w')
 
    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
 
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
        print("下载页面: ", url)
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
            print('error:', e.response)
            html = ''
            if hasattr(e.response, 'status_code'):
                code = e.response.status_code
                print('error code: ', code)
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
            print(data['jsrq'],f"课堂评价总共 {json_data['total']} 份")
            for i in json_data['rows']:
                temp = {}
                ###
                if i['pjdm'] == '' :   #筛选未评价的课程
                    temp['teadm'] = i['teadm']
                    temp['dgksdm'] = i['dgksdm']
                    question_list[i['rownum_']] = temp
                    print(f"第{i['rownum_']}份：",temp)
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
            #print(question_list)
            return question_list

        except Exception as e:
            print('出错: ', e)
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
            print(k, v)
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
        # 每份问卷3个类型5选择, 概率为1/9, 也就是每3份问卷会出现一个95分
        values = [20.0, 20.0, 20.0, 20.0, 20.0, 20.0, 20.0, 20.0, 40.0]
        probability_num = random.choice(values)
        return_dict = {}
        if probability_num == 20.0:
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

        if probability_num == 40.0:
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
            print("问题类型 txdm[0]=",txdm[0])
            #print(type(txdm[0]))
            #print("int(txdm[0])",int(txdm[0]))
            #print(type(int(txdm[0])))
            print("zbmc",zbmc)
            print("zbdm",zbdm)
            
            single_question_reply_info['txdm'] = int(txdm[0]) # 这里要数字
            single_question_reply_info['zbdm'] = zbdm[0]
            single_question_reply_info['zbmc'] = zbmc[0]



            # 进行分流, 如果匹配了, 说明是一种类型
            if txdm[0] == '5':
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
                print("正则匹配出错, 请检查以下内容: ", child)
            all_question_reply_info.append(single_question_reply_info)
        print("得分 score:",score)
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
    # 打开浏览器
    driver = webdriver.Chrome("chromedriver")
    # 打开网址
    driver.get("http://zhjw.smu.edu.cn/")
    # 找到账号登录
    elem_acc = driver.find_element_by_id("L_account")
    fill_keys(elem_acc, accout)

    # 找到密码登录
    elem_pwd = driver.find_element_by_id("L_pass")
    fill_keys(elem_pwd, pwd)

    # 找到验证码输入
    elem_vercode = driver.find_element_by_id("L_vercode")
    fill_keys(elem_vercode, "")  # 后续优化
    # # 找到验证码地址
    # elem_verpict = driver.find_element_by_id("captcha")
    # url = elem_verpict.get_attribute('src')
    # print(url)

    time.sleep(30)
    
    # 键入回车
    # elem_vercode.send_keys(Keys.RETURN)

    cookies = driver.get_cookies()
    # 关闭窗口
    driver.quit()

    # print(cookies)
    # 这里返回值为[{'domain': 'zhjw.smu.edu.cn', 'httpOnly': True, 'name': 'JSESSIONID', 'path': '/', 'secure': False, 'value': '2B583913425880224DD86D176C95D294'}]
    # 只取value 的值
    return cookies[0]['value']


def main():
    sys.stdout = Logger('a.log', sys.stdout)
    print('\n')
    print("请耐心等待30秒".center(30, '-'))
    print('\n')
    # 获得JSESSIONID
    JSESSIONID = login_get_cookies()
    print("成功获取jsessionid: ", JSESSIONID)
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
                temp_key = list(question_list.keys())[x]
                temp_value = question_list[temp_key]
                print(temp_key, temp_value)
                # 获取了内容
                print("-" * 50)
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
    print(" CopyRight: z ".center(50, '#'))
    print("            南医大计协本部程设组组长 z")
    print("              如需反馈bug请提交issue")
    print("All Rights Reserved".center(50))
    print(" CopyRight: z ".center(50, '#'))
    print('-'*50)
    print(" Update ".center(50,'#'))
    print("Jayce丶H".center(50))
    print("2021.09.17".center(50))
    print(" Update Done!".center(50,'#'))
    print('-'*50)
    print("30秒后会自动关闭此窗口")
    print('-'*50)
    time.sleep(30)

if __name__ == "__main__":
    main()
