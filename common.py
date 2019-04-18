#!/usr/bin/python
# -*- coding: UTF-8 -*-

import re
import config
from flask import jsonify


def format_tags(arr):
    filter_arr = ['了解', '万门', '入门', '通识', '注册', '一级', '学习', '精讲', '如何', '一月', '介绍', '课程', '联考', '知识', '计划', '规划', '职业',
                  '老师', '轻松', '课堂', '简单', '素质', '时间', '教师', '小时', '分享', '体验', '九年', '预测', '超轻', '走进', '相关', '未知', '什么']
    new_arr = []

    for item in arr:
        if item.get('_id') not in filter_arr and len(item.get('_id')) > 1 and len(item.get('_id')) < 6 and not any(
                char.isdigit() for char in item.get('_id')):
            new_arr.append(item.get('_id'))
    return new_arr


def format_m3u8(data):
    new_data = str(data, encoding='utf-8')
    video_server = 'https://media.wanmen.org/'
    it = re.finditer(".+\.ts", new_data)
    for match in it:
        new_data = new_data.replace(match.group(), video_server + match.group())
    return new_data


def get_page_data(data_count, page_limit, page, search):
    html = '<ul class="pagination pagination-lg">'
    page_count = int(data_count / page_limit) + 1

    page_next = 1 if (page - 1) <= 1 else page - 1
    page_last = page_count if (page + 1) >= page_count else page + 1

    page_next_html = '' if page_next <= 1 else '<li><a href="/list/page/%d?search=%s">&laquo;</a></li>' % (
        page_next, search)
    page_last_html = '' if page_last >= page_count else '<li><a href="/list/page/%d?search=%s">&raquo;</a></li>' % (
        page_last, search)
    li = '<li %s><a href="/list/page/%d?search=%s">%d</a></li>'
    lis_num = 3
    lis = ''
    for i in range(1, page_count + 1):
        next_num = 0 if page - lis_num > 0 else (lis_num - page) + 1
        last_num = 0 if page + lis_num <= page_count else page + lis_num - page_count
        if (page - lis_num - last_num) <= i and (page + lis_num + next_num) >= i:
            status = ''
            if page == i:
                status = 'class="active"'

            lis = lis + li % (status, i, search, i)

    html = html + page_next_html + lis + page_last_html
    html = html + "</ul>"
    return html


def info_msg(code, msg=''):
    if msg == '':
        if str(code) in config.app_msg.keys():
            msg = config.app_msg[str(code)]
        else:
            msg = config.app_msg['default']
    return jsonify({'code': code, 'msg': msg})
