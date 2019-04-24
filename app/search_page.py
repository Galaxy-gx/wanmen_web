# -*- coding:utf-8 -*-
# 一个月运行一次
# 获取所有万门课程包含ts视频url
# 更新，如果视频数量==已获取的ts数，则跳过，如果数量更新且比原来ts视频url数量 && 状态未完成，则覆盖。
# 异常，如果接口返回出错，通知。

from user_agent import generate_user_agent
import requests
import time
from dateutil.parser import parse
from pymongo import MongoClient
import re
from multiprocessing import Process, Queue, Pool, Manager
import config

pattern = '.+\.ts'

ua = generate_user_agent()
headers = {
    'User-Agent': ua
}

video_server = 'https://media.wanmen.org/'
lectures_url = "https://api.wanmen.org/4.0/content/lectures/"

client = MongoClient(config.app_config.get('MONGO_CONFIG'), connect=False)
db = client['wanmen_ts_m3u8']
collection = db.all_courses
collection_m3u8 = db.m3u8_data

manager = Manager()
queue = manager.Queue()


def update_data(data):
    del data['_id']
    del data['createdAt']
    del data['downloadCount']
    course = {"$set": data}
    return course


def process_get_item_ts(q, id, url):
    response = requests.get(url, timeout=30, headers=headers).json()
    ts_data = ''
    if response.get('video', '') == '' or response['video'].get('hls', '') == '':
        method = 0
        m3u8_url = ''
    else:
        method = 1
        m3u8_url = response['video']['hls']['pcMid']
        ts_data = requests.get(m3u8_url, timeout=30, headers=headers).content
    q.put([id, m3u8_url, method, ts_data])


def get_lectures_data(class_id, class_name, response):
    downloadAction = 1
    courses_url = "https://api.wanmen.org/4.0/content/courses/" + \
        response[i]['id']
    courses_data = get_courses_data(courses_url)

    for n in range(len(courses_data)):
        num = str(n + 1)
        print(
            "%s %s %s/%d count:%d" % (
                time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()
                              ), class_name, num, len(courses_data),
                len(courses_data[n]['children'])))
        lectures_id = courses_data[n]['id']
        lectures_name = num + '_' + \
            courses_data[n]['name'].replace('/', '').replace('_', '')

        downloadAction, children_data = get_children_data(num, courses_data[n]['children'], class_id, class_name,
                                                          lectures_id, lectures_name)

    return downloadAction


def get_children_data(num, data, class_id, class_name, lectures_id, lectures_name):
    process_count = 10
    children = {}
    flag = 1
    cut_data = [data[i:i + process_count]
                for i in range(0, len(data), process_count)]
    for i in range(len(cut_data)):
        p = Pool(process_count)
        for k in range(len(cut_data[i])):
            prefix = "%s.%d_" % (num, i * process_count + k + 1)
            children_id = cut_data[i][k]['id']
            children_name = prefix + \
                cut_data[i][k]['name'].replace('/', '').replace('_', '')
            children[children_id] = {}
            children[children_id]['name'] = children_name
            children[children_id]['hls_url'] = ''
            children[children_id]['method'] = 0
            children[children_id]['video_ts'] = ''
            p.apply_async(process_get_item_ts, args=(
                queue, children_id, lectures_url + children_id))

        p.close()
        p.join()

        while not queue.empty():
            item = queue.get()
            key = item[0]
            val = item[1]
            method = item[2]
            flag = method
            ts = item[3]
            children[key]['hls_url'] = val
            children[key]['method'] = method
            children[key]['video_ts'] = ts
            if not collection_m3u8.find_one({'_id': key}):
                collection_m3u8.insert_one(
                    m3u8_format_data(key, children, class_id, class_name, lectures_id, lectures_name))

    return flag, children


def format_data(data, downloadAction):
    course = {
        '_id': data.get('id'),
        'name': data.get('name').replace('/', '').replace('_', ''),
        'createdAt': parse(data.get('createdAt')),
        'updatedAt': parse(data.get('updatedAt')),
        'finishedAt': 0 if data.get('finishedAt', 0) == 0 else parse(data.get('finishedAt')),
        'price': data.get('price'),
        'likes': data.get('likes', 0),
        'tag': data.get('tag', '').split() if isinstance(data.get('tag'), str) else '',
        'status': data.get('status'),
        'bigImage': data.get('bigImage'),
        'videoCount': data.get('videoCount') if data.get('videoCount', '') else 0,
        'description': data.get('description'),
        'teacherName': data.get('teacherName'),
        'teacherAvatar': data.get('teacherAvatar'),
        'downloadAction': downloadAction,
        'downloadCount': 0
    }
    return course


def m3u8_format_data(id, data, class_id, class_name, lectures_id, lectures_name):
    course = {
        '_id': id,
        'class_id': class_id,
        'name': class_name,
        'lectures_id': lectures_id,
        'lectures_name': lectures_name,
        'children_name': data[id].get('name'),
        'children_m3u8': data[id].get('video_ts')
    }
    return course


def get_courses_data(url):
    response = requests.get(url, timeout=30, headers=headers).json()
    return response['lectures']


flag = True
page = 1
limit = 32
total, create_num, update_num, continue_num = 0, 0, 0, 0
while flag:
    item_num = 0
    if page >= 2:
        url = "https://api.wanmen.org/4.0/content/courses?limit=%d&page=%d" % (
            limit, page)
    else:
        url = "https://api.wanmen.org/4.0/content/courses?limit=%d" % limit
    page = page + 1
    response = requests.get(url, timeout=30, headers=headers).json()
    arr_len = len(response)
    for i in range(arr_len):
        _id = response[i]['_id']
        class_name = response[i]['name'].replace('/', '').replace('_', '')
        if arr_len < limit:
            flag = False

        tmp_str = 'create'
        db_item = collection.find_one(_id)
        if not db_item:
            downloadAction = get_lectures_data(_id, class_name, response)
            course = format_data(response[i], downloadAction)
            collection.insert_one(course)
            create_num = create_num + 1
        else:
            response_videoCount = 0
            db_item_videoCount = 0
            if response[i].get('videoCount') == 'None' or response[i].get('videoCount') == None:
                response_videoCount = 0
            else:
                response_videoCount = int(response[i].get('videoCount'))

            if db_item.get('videoCount') == 'None' or db_item.get('videoCount') == None:
                db_item_videoCount = 0
            else:
                db_item_videoCount = int(db_item.get('videoCount', 0))

            if response_videoCount == db_item_videoCount:
                tmp_str = 'continue'
                continue_num = continue_num + 1
            elif response_videoCount > db_item_videoCount:
                # 更新源ts视频url
                tmp_str = 'update'
                downloadAction = get_lectures_data(_id, class_name, response)
                course = format_data(response[i], downloadAction)
                collection.update_one({'_id': _id}, update_data(course))
                update_num = update_num + 1
            else:
                tmp_str = '%s error %s/%s' % (class_name,
                                              response_videoCount, db_item_videoCount)

        total = total + 1
        print('%s %s page:%d current:%d %s' % (
            time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), class_name, page - 1, i, tmp_str))

today = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
print("%s total:%d create_num:%d update_num:%d continue_num:%d" %
      (today, total, create_num, update_num, continue_num))
