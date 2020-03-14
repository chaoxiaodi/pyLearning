#!/usr/bin/python
# -*- coding: utf-8 -*-
import requests
import datetime
import logging
import os
import sys
import re
import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

# 定义日志格式和输出
log_file = '/tmp/zbxalert.log'
log_level = logging.INFO
log_format = '%(asctime)s[%(levelname)s]: %(message)s'
logging.basicConfig(filename=log_file, level=log_level, format=log_format)
logger = logging.getLogger()

# zabbix消息处理
class ZbxHanding:
    '''
    zabbix 消息接收处理
    zabbix 图片处理
    zabbix 消息格式化
    '''

    def __init__(self):
        # zabbix 服务器url
        self.zserver_url = 'http://zabbix.abc.com'
        # zabbix 图形页面url
        self.zchart_url = "http://zabbix.abc.com/chart.php"
        # 全局变量host
        self.host = 'zabbix.abc.com'
        # zabbix获取图片保存的名称
        self.pic_name = 'zbxalert.png'
        # zabbix itemid 用来获取图片
        self.zitemid = ''

    # 根据接收的zabbix 返回item id
    def get_zitemid(self):
        self.zitemid = re.search(r'ITEM ID:(\d+)', sys.argv[3]).group(1)

    # 根据获取到的item id获取zabbix对应图形
    def get_pic_from_zbx(self):
        # 构建session，或者可以一次构建之后使用cookie登录
        myRequests = requests.Session()
        try:
            heads = {
                "Host": self.host,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8"
            }
            # 构建登录所需的信息
            playLoad = {
                "name": "Admin",
                "password": 'zabbix',
                "autologin": "1",
                "enter": "Sign in",
            }
            myRequests.post(url=self.zserver_url, headers=heads, data=playLoad)
            url_playload = {
                "from": "now-1h",
                "to": "now",
                "itemids": self.zitemid,
                "width": "800",
            }
            getGraph = myRequests.get(url=self.zchart_url, params=url_playload)
            IMAGEPATH = os.path.join('/tmp/', self.pic_name)
            #print(IMAGEPATH)
            # 将获取到的图片数据写入到文件中去
            with open(IMAGEPATH, 'wb') as f:
                f.write(getGraph.content)
            pic_url = IMAGEPATH
            return pic_url
        except Exception as e:
            logger.error(e)
            return False

    # 对报警信息进行格式化
    def format_text(self):
        format_info = "## " + str(sys.argv[2]) + "\n"
        x = str(sys.argv[3]).split('\n')
        for i in x:
            if re.search('ITEM ID', str(i)):
                pass
            else:
                format_info += "- " + str(i)
        return format_info

# 发送钉钉消息
class DingDing:
    '''
    钉钉发送消息处理
    获取token
    上传图片
    发送消息
    '''

    def __init__(self):
        self.dappkey = '你的钉钉appkey'
        self.dappsecret = '你的钉钉app密钥'
        # 钉钉获取token url
        self.dgturls = 'https://oapi.dingtalk.com/gettoken'
        # 钉钉上传图片url
        self.dupurls = 'https://oapi.dingtalk.com/media/upload'
        # 钉钉群机器人webhook url
        self.dwebhook_url = 'https://oapi.dingtalk.com/robot/send?access_token=' \
                            '你的webhook'
        # 钉钉获取的token
        self.dtoken = ''
        self.mediaid = ''

    # 获取钉钉token
    def get_dingtoken(self):
        heads = {
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0'
        }
        data = {
            'appkey': self.dappkey,
            'appsecret': self.dappsecret
        }
        res = requests.get(self.dgturls, params=data, headers=heads)
        self.dtoken = json.loads(res.text)['access_token']

    # 上传图片到钉钉，并返回media id
    def upload_pic_dingding(self, file_name):
        heads = {
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0'
        }
        files = {'media': open(file_name, 'rb')}
        data = {
            'access_token': self.dtoken,
            'type': "image"
        }
        res = requests.post(self.dupurls, data=data, files=files)
        self.mediaid = json.loads(res.text)['media_id']

    # 构造发送消息的请求
    def msg_to_dingding(self, zhuti, info):
        headers = {'Content-Type': 'application/json;charset=utf-8'}
        data = {
            "msgtype": "actionCard",
            "actionCard": {
                "title": zhuti,
                "text": "![screenshot](" + self.mediaid + ")\n" + info
            },
        }
        r = requests.post(url=self.dwebhook_url, json=data, headers=headers)

# 发送微信消息
class Wechat:
    '''
    钉钉发送消息处理
    获取token
    上传图片
    发送消息
    '''
    def __init__(self):
        self.wcorpid = '你的企业微信id'
        self.wcorpsecret = '你的企业安全字段'
        # 钉钉获取token url
        self.wgturls = 'https://qyapi.weixin.qq.com/cgi-bin/gettoken'
        # 钉钉上传图片url
        self.wupurls = ' https://qyapi.weixin.qq.com/cgi-bin/media/upload'
        # 钉钉群机器人webhook url
        self.wmsg_url = 'https://qyapi.weixin.qq.com/cgi-bin/message/send'
        # 钉钉获取的token
        self.wtoken = ''
        self.mediaid = ''

    def get_wechattoken(self):
        heads = {
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0'
        }
        data = {
            'corpid': self.wcorpid,
            'corpsecret': self.wcorpsecret
        }
        res = requests.get(self.wgturls, params=data, headers=heads)
        self.wtoken = json.loads(res.text)['access_token']

    def upload_pic_wechat(self, file_name):
        heads = {
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0'
        }
        self.wupurls += "?access_token=%s&type=image" % self.wtoken
        files = {'media': open(file_name, 'rb')}
        data = {
            'access_token': self.wtoken,
            'type': "image"
        }
        res = requests.post(self.wupurls, files=files)
        self.mediaid = json.loads(res.text)['media_id']

    def msg_to_wechat(self, info):
        headers = {'Content-Type': 'application/json;charset=utf-8'}
        self.wmsg_url += "?access_token=%s" % self.wtoken

        text = {
            "toparty": "3",
            "msgtype": "text",
            "agentid": 1000002,
            "text": {
                "content": info
            },
        }
        img = {
            "toparty": "3",
            "msgtype": "image",
            "agentid": 1000002,
            "image": {
                "media_id": self.mediaid
            },
        }
        send_text = requests.post(url=self.wmsg_url, json=text, headers=headers)
        send_img = requests.post(url=self.wmsg_url, json=img, headers=headers)

# 发送邮件
class Email:
    '''
    钉钉发送消息处理
    获取token
    上传图片
    发送消息
    '''
    def __init__(self):
        self.user = '你的邮箱账号'
        self.passwd = '你的邮箱密码'
        self.serverurl = 'smtp.qiye.163.com'
        self.serverport = 465
        self.to_list = ["接收邮件的地址1", "接收邮件的地址2"]

    def msg_to_email(self, zhuti, info):
        # 构建html消息体，把接收的消息转换为html格式
        send_str = '<html><body>'
        send_str += '<center>' + info.replace('\n', '</br>') + '</center>'
        # html中以<img>标签添加图片，align和width可以调整对齐方式及图片的宽度
        send_str += '<img src="cid:zbxalert" alt="zbxalert" align="center" width=100% >'
        send_str += '<center>60分钟内的数据状态图</center>'
        send_str += '</body></html>'
        # 构建message
        msg = MIMEMultipart()
        # 添加邮件内容
        content = MIMEText(send_str, _subtype='html', _charset='utf8')
        msg.attach(content)
        # 邮件正文添加图片
        img1 = MIMEImage(open('/tmp/zbxalert.png', 'rb').read(), _subtype='octet-stream')
        img1.add_header('Content-ID', 'zbxalert')
        msg.attach(img1)
        # 附件形式添加图片
        #img = MIMEImage(open('./zbxalert.png', 'rb').read(), _subtype='octet-stream')
        #img.add_header('Content-Disposition', 'attachment', filename='./zbxalert.png')
        #msg.attach(img)
        # 登录邮箱
        mail_server = smtplib.SMTP_SSL(self.serverurl, self.serverport)
        mail_server.login(self.user, self.passwd)
        #发送邮件
        msg['To'] = ';'.join(self.to_list)
        msg['From'] = self.user
        msg['Subject'] = zhuti
        mail_server.sendmail(self.user, self.to_list, msg.as_string())
        print("send email success!")

# 发送飞书群消息
class FeiShu:
    '''
    钉钉发送消息处理
    获取token
    上传图片
    发送消息
    '''
    def __init__(self):
        self.fsappid = '你的飞书appid'
        self.fsappsecret = '你的飞书app安全字段'
        # 飞书获取token url
        self.fsgturls = 'https://open.feishu.cn/open-apis/auth/v3/app_access_token/internal/'
        # 飞书上传图片urlf
        self.fsupurls = 'https://open.feishu.cn/open-apis/image/v4/put/'
        # 飞书发送消息需要获取群组列表
        self.fsgtgurls = 'https://open.feishu.cn/open-apis/chat/v4/list?'
        # 飞书发送消息url
        self.fsmsg_url = 'https://open.feishu.cn/open-apis/message/v4/send/'
        # 飞书获取的token
        self.fstoken = ''
        # 飞书上传图片返回的mediaid
        self.image_key = ''

    def get_feishutoken(self):
        heads = {
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0'
        }
        data = {
            'app_id': self.fsappid,
            'app_secret': self.fsappsecret
        }
        res = requests.post(self.fsgturls, json=data, headers=heads)
        self.fstoken = json.loads(res.text)['app_access_token']

    def upload_pic_feishu(self, file_name):
        heads = {
            # 飞书这个部分不能使用json，特意注释
            # 'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0',
            'Authorization': "Bearer %s" % self.fstoken
        }
        files = {'media': open(file_name, 'rb')}
        data = {"image_type": "message"}
        res = requests.post(url=self.fsupurls,
                            headers=heads,
                            files=files,
                            data=data)
        self.image_key = json.loads(res.text)['data']['image_key']


    def get_group_list(self):
        heads = {
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0',
            'Authorization': "Bearer %s" % self.fstoken
        }
        res = requests.get(self.fsgtgurls, headers=heads)
        glist = json.loads(res.text)
        # 飞书的给群组发送消息需要提前获取添加了应用机器人的群组列表中的chat_id的信息
        # 这一点还比较奇葩

    def msg_to_feishu(self, zhuti, info):
        heads = {
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0',
            'Authorization': "Bearer %s" % self.fstoken
        }
        data = {
            "chat_id": "oc_4676f9709c0bd8c9177acc2cbb923adb",
            "msg_type": "post",
            "content": {
                "post": {
                    "zh_cn": {
                        "title": zhuti,
                        "content": [
                            [
                                {
                                    "tag": "text",
                                    "un_escape": True,
                                    "text": info
                                }
                            ],
                            [
                                {
                                    "tag": "img",
                                    "image_key": self.image_key,
                                    "width": 800,
                                    "height": 400
                                }
                            ]
                        ]
                    }
                }
            }
        }
        send_text = requests.post(url=self.fsmsg_url, json=data, headers=heads)

# 根据参数发送到不同的应用接收方
def chiose_app(zhuti, info, appname):
    '''
    :param zhuti: 消息主题
    :param info: 消息内容
    :param appname: 消息接收应用
    :return:
    '''
    if appname == 'wechat':
        # 发送到企业微信20200314测试成功
        # 企业微信与钉钉发送方式不太一样，企业微信不支持卡片消息，发送文本后再发送一个图片
        wechat = Wechat()
        wechat.get_wechattoken()
        wechat.upload_pic_wechat('/tmp/zbxalert.png')
        wechat.msg_to_wechat(info)
    elif appname == 'dingding':
        # 发送消息到钉钉20200314测试成功
        ding = DingDing()
        ding.get_dingtoken()
        ding.upload_pic_dingding('/tmp/zbxalert.png')
        ding.msg_to_dingding(zhuti, info)
    elif appname == 'email':
        # 发送消息到邮件20200314测试成功；
        email = Email()
        email.msg_to_email(zhuti, info)
    elif appname == 'feishu':
        # 发送消息到飞书20200314测试成功
        fs = FeiShu()
        fs.get_feishutoken()
        fs.upload_pic_feishu('/tmp/zbxalert.png')
        fs.get_group_list()
        fs.msg_to_feishu(zhuti, info)
    else:
        print("传入的接收方名称不正确！请传入一下几种：\n"
              "wechat dingding email feishu")

def main():
    if len(sys.argv) == 5:
        touser = str(sys.argv[1])
        zhuti = str(sys.argv[2])
        oldinfo = str(sys.argv[3])
        toapp = str(sys.argv[4])
        zbx = ZbxHanding()
        info = zbx.format_text()
        zbx.get_zitemid()
        zbx.get_pic_from_zbx()
        chiose_app(zhuti, info, toapp)
    else:
        print("必须传入4个参数！{"
              "touser：消息接收人,"
              "zhuti: 消息主题",
              "info: 消息内容,"
              "toapp： 接收app名称[wechat dingding email feishu]}")
        return 0

if __name__ == '__main__':
    if sys.getdefaultencoding() != 'utf-8':
        reload(sys)
        sys.setdefaultencoding('utf-8')
    main()
