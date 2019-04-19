import requests
import re
from user_agent import generate_user_agent
from uwsgi_cache.cache import CacheManager

cache = CacheManager("media_user_cache", 120)


class passport:
    ua = generate_user_agent()

    def seccode(self, mobile, rand_num):
        headers = {
            'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Host': 'passport.9you.com',
            'Pragma': 'no-cache',
            'Referer': 'https://passport.9you.com/mobile_regist.php',
            'User-Agent': self.ua,
            'Origin': 'https://passport.9you.com',
        }
        suffix = '?' + str(rand_num) if rand_num else ''
        content = requests.post('https://passport.9you.com/seccode.php' + suffix, headers=headers)

        arr = re.findall('PHPSESSID\=([^\;].*)\;.*', content.headers['Set-Cookie'])
        PHPSESSID = str(arr[0]).encode('utf-8')
        print(type(PHPSESSID))
        print(type(mobile))
        print(type({'id': PHPSESSID}))
        cache.set(mobile, {'id': PHPSESSID})
        print(mobile + arr[0])
        return content.content

    def send_sms(self, mobile, code):
        PHPSESSID = cache.get(mobile)
        print(PHPSESSID)
        headers = {
            'Host': 'passport.9you.com',
            'Origin': 'https://passport.9you.com',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'User-Agent': self.ua,
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Cache-Control': 'no-cache',
            'X-Requested-With': 'XMLHttpRequest',
            'Cookie': 'PHPSESSID=' + PHPSESSID,
            'Connection': 'keep-alive',
            'Referer': 'https://passport.9you.com/mobile_regist.php',
        }
        d = {"mobile": mobile, "dataType": "json", "type": "regist", "checkcode": code}
        # content = requests.post('https://passport.9you.com/sendmobilecode.php', data=d, headers=headers).json()
        return int(4), ''
        # return int(content.get('ret')), content.get('msg')

    def verfiy_sms(self, mobile, sms):
        PHPSESSID = cache.get(mobile)
        headers = {
            'Host': 'passport.9you.com',
            'Connection': 'keep-alive',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache',
            'Origin': 'https://passport.9you.com',
            'Upgrade-Insecure-Requests': '1',
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': self.ua,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
            'Referer': 'https://passport.9you.com/mobile_regist.php',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Cookie': 'PHPSESSID=' + PHPSESSID,
        }

        d = {"username": mobile, "password": "fKWKWd2m2nrMXQf", "code": sms, "realname": '%E7%A8%8B%E5%85%86%E7%A5%A5',
             'idcard': '34082419901212323x', 'nickname': '123123', 'protocal': 1, 'x': 46, 'y': 17}
        content = requests.post('https://passport.9you.com/mobile_regist_do.php', data=d, headers=headers)
        content.encoding = 'utf-8'
        login_flag = 0
        search_obj = re.search('昵称中含有禁用字符', content.text)
        msg = ''
        if search_obj:
            login_flag = 1
        else:
            arr = re.findall('<br />([^<.]*)<br />', content.text)
            if len(arr) >= 1:
                msg = arr[0]
        return login_flag, msg
