#!/usr/bin/python
# -*- coding: utf-8 -*-
import requests, time
import json, sys, re, os
# from poster3.encode import multipart_encode
# from poster3.streaminghttp import register_openers

# 钉钉token
dtoken = ''
# 钉钉上传文件返回的id
dmedia_id = ''
# 获取zabbix item id用于获取图片
zitem_id = ''
# zabbix 服务器url
zserver_url = 'http://zabbix.abc.com'
# zabbix 图形页面url
zchart_url = "http://zabbix.abc.com/chart.php"
# 钉钉群机器人webhook --运维小菜鸟
webhook_url = 'https://oapi.dingtalk.com/robot/send?access_token='
# 全局变量host
host = 'zabbix.abc.com'

# 根据接收的zabbix 返回item id
def get_zitemid():
    zitemid=re.search(r'ITEM ID:(\d+)',sys.argv[3]).group(1)
    return zitemid

# 根据获取到的item id获取zabbix对应图形
def get_pic_from_zbx():
    # 构建session，或者可以一次构建之后使用cookie登录
    myRequests = requests.Session()
    try:
        heads = {
            "Host": host,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8"
        }
        # 构建登录所需的信息
        playLoad = {
            "name": "Admin",
            "password": '12345678',
            "autologin": "1",
            "enter": "Sign in",
        }
        myRequests.post(url=zserver_url, headers=heads, data=playLoad)
        testUrlplayLoad = {
            "from": "now-1h",
            "to": "now",
            "itemids": zitem_id,
            "width": "800",
        }
        getGraph = myRequests.get(url=zchart_url, params=testUrlplayLoad)
        IMAGEPATH = os.path.join('/tmp/', pic_name)
        print(IMAGEPATH)
        # 将获取到的图片数据写入到文件中去
        with open(IMAGEPATH, 'wb') as f:
            f.write(getGraph.content)
        pic_url = IMAGEPATH
        return pic_url
    except Exception as e:
        print(e)
        return False

# 获取钉钉token
def get_dingtoken():
    heads = {
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.96 Safari/537.36'
    }
    data = {
        'appkey': 'dingappkey',
        'appsecret': 'dingappsecret'
    }
    durls = 'https://oapi.dingtalk.com/gettoken'
    res = requests.get(durls, params=data, headers=heads)
    dtoken = json.loads(res.text)['access_token']
    return dtoken
# 上传图片到钉钉，并返回media id
def upload_pic_dingding(dtoken, file_name):
    heads = {
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.96 Safari/537.36'
    }
    durls = 'https://oapi.dingtalk.com/media/upload'
    files = {'media': open(file_name, 'rb')}
    data ={
        'access_token': dtoken,
        'type': "image"
    }
    res = requests.post(durls, data=data, files=files)
    mdeia_id = json.loads(res.text)['media_id']
    return mdeia_id

# 对报警信息进行格式化
def format_text():
    format_info = "## "+zhuti+"\n"
    x = oldinfo.split('\n')
    for i in x:
        if re.search('ITEM ID',str(i)):
            pass
        else:
            format_info+="- "+str(i)
    return format_info

# 构造发送消息的请求
def send_msg(dmedia_id,zinfo):
    headers = {'Content-Type': 'application/json;charset=utf-8'}
    data = {
        "msgtype": "actionCard",
        "actionCard": {
            "title": zhuti,
            "text": "![screenshot]("+dmedia_id+")\n"+zinfo
        },
    }
    r = requests.post(url=webhook_url, json=data, headers=headers)

if __name__ == '__main__':
    if sys.getdefaultencoding() != 'utf-8':
        reload(sys)
        sys.setdefaultencoding('utf-8')
    zitem_id = get_zitemid()
    pic_name = 'zbxalert.png'
    touser = str(sys.argv[1])
    zhuti = str(sys.argv[2])
    oldinfo = str(sys.argv[3])
    zinfo = format_text()
    pic_path = get_pic_from_zbx()
    dtoken = get_dingtoken()
    dmedia_id = upload_pic_dingding(dtoken, pic_path)
    send_msg(dmedia_id, zinfo)