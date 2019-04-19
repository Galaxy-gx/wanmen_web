#!/usr/bin/python
# -*- coding: UTF-8 -*-

from flask import Flask, Response, request, render_template, redirect, url_for
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
from flask_bootstrap import Bootstrap
from models import *
import config
import common
import sms
import datetime
from urllib.parse import urlsplit, parse_qs
from collections import OrderedDict

app = Flask(__name__)
app.secret_key = config.app_config.get('SECRET_KEY')
Bootstrap(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
sms = sms.passport()


@app.route('/')
@app.route('/list/', defaults={'page': 1})
@app.route('/list/page/<int:page>', methods=['GET'])
@login_required
def get_list(page=1):
    model = all_courses_table()
    search = request.args.get('search', '')
    page_limit = 32
    tags = common.format_tags(model.get_tag_list())
    skip_num = 0
    if page > 1:
        skip_num = page_limit * (page - 1)

    courses_data = model.search(search).skip(skip_num).limit(page_limit)
    data_count = model.count
    pagination = common.get_page_data(data_count, page_limit, page, search)
    courses = []
    for i in courses_data:
        i['bigImage'] = str(i.get('bigImage')).replace('https://imgs.wanmen.org/',
                                                       'https://media.scooky.com/proxy/img/')
        courses.append(i)

    return render_template('list.html', courses=courses, tags=tags[:105], pagination=pagination, search=search)


@app.route('/detail/<path:url_info>', methods=['GET'])
@login_required
def get_detail(url_info):
    children_id = ''
    path_info = url_info.split('/', 2)
    id = path_info[0]
    if len(path_info) > 1 and path_info[1] == 'children_id' and len(path_info[2]) == 24:
        children_id = path_info[2]

    course = all_courses_table().collection.find_one({'_id': id})
    class_data = m3u8_data_table().get_class_data(id)
    detail_data = OrderedDict()
    for item in class_data:
        is_download = 0
        if not children_id:
            children_id = item.get("_id")

        if item.get("lectures_id") not in detail_data.keys():
            detail_data[item.get("lectures_id")] = OrderedDict()

        detail_data[item.get("lectures_id")]['lectures_name'] = item.get("lectures_name")
        if 'children_data' not in detail_data[item.get("lectures_id")]:
            detail_data[item.get("lectures_id")]['children_data'] = OrderedDict()

        if item.get("children_m3u8"):
            is_download = 1

        if item.get("_id") not in detail_data[item.get("lectures_id")]['children_data'].keys():
            detail_data[item.get("lectures_id")]['children_data'][item.get("_id")] = OrderedDict()

        detail_data[item.get("lectures_id")]['children_data'][item.get("_id")]['name'] = item.get("children_name")
        detail_data[item.get("lectures_id")]['children_data'][item.get("_id")]['is_download'] = is_download

    return render_template('detail.html', id=id, course=course, detail_data=detail_data, play_id=children_id)


@app.route('/media/<children_id>', methods=['GET'])
@login_required
def get_media(children_id):
    m3u8_data = m3u8_data_table().collection.find_one({'_id': children_id}, {"children_m3u8": 1})
    if not m3u8_data.get("children_m3u8"):
        return "media is not found"
    m3u8_list = common.format_m3u8(m3u8_data.get("children_m3u8"))
    return Response(m3u8_list, content_type='application/vnd.apple.mpegurl')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('get_list'))

    if request.method == 'POST':
        mobile = request.form.get('mobile', '')
        remeber = request.form.get('remeber', '')
        sms_code = request.form.get('sms', '')

        if not mobile or not sms_code:
            return common.info_msg(101)
        elif not User(mobile).check_user():
            return common.info_msg(102)
        else:
            login_flag, msg = sms.verfiy_sms(mobile, sms_code)

        if login_flag:
            model = User(mobile)
            if config.app_config.get('OPEN_REGISTER'):
                model.insert_user()
            model.login_log(request)
            user_json = model.find_user()
            if remeber == 'true':
                login_user(User(user_json.get('mobile')), True, datetime.timedelta(weeks=1))
            else:
                login_user(User(user_json.get('mobile')))
            arr = parse_qs(urlsplit(request.form.get("url")).query)
            next_url = ''
            if 'next' in arr.keys():
                next_url = arr.get('next')[0]

            return common.info_msg(0, next_url)
        else:
            return common.info_msg(103, msg)
    return render_template('login.html')


@app.route('/send_sms', methods=['POST'])
def send_sms():
    mobile = request.form.get('mobile', '')
    code = request.form.get('code', '')
    if mobile and code:
        if User(mobile).check_user():
            ret, msg = sms.send_sms(mobile, code)
            return common.info_msg(ret, msg)
        else:
            return common.info_msg(102)
    else:
        return common.info_msg(101)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/seccode', methods=['GET', 'POST'])
def seccode():
    rand_num = request.args.get('rand_num', '')
    mobile = request.args.get('mobile', '')
    return Response(sms.seccode(mobile,rand_num), content_type='image/png')


@login_manager.user_loader
def load_user(user_id):
    user_json = User(user_id).find_user()
    return User(user_json.get('mobile'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
