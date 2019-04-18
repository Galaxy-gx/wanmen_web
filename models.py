#!/usr/bin/python
# -*- coding: UTF-8 -*-

from pymongo import MongoClient
from bson.son import SON
from flask_login import UserMixin
import time
import json
import config

client = MongoClient(config.app_config.get('MONGO_CONFIG'))
db = client['wanmen_ts_m3u8']


class all_courses_table:
    count = 0
    collection = db.all_courses

    def get_tag_list(self):
        pipeline = [
            {"$unwind": "$tag"},
            {"$project": {"tag": 1, "teacherName": 1, "difference": {"$eq": ["$tag", "$teacherName"]}}},
            {"$match": {"difference": False}},
            {"$group": {"_id": "$tag", "count": {"$sum": 1}}},
            {"$sort": SON([("count", -1), ("_id", -1)])}
        ]
        tags = list(self.collection.aggregate(pipeline))
        return tags

    def search(self, keywork):
        query = {}
        if keywork:
            query = {"$or": [{'name': {'$regex': str(keywork)}}, {'tag': {'$regex': str(keywork)}}]}

        self.count = self.collection.count_documents(query)
        return self.collection.find(query)


class m3u8_data_table:
    collection = db.m3u8_data

    def get_class_data(self, class_id):
        return self.collection.find({'class_id': class_id},
                                    {"_id": 1, "lectures_id": 1, "lectures_name": 1, "children_name": 1,
                                     "children_m3u8": 1}).sort(
            [["children_name", 1]]).collation({"locale": "en_US", "numericOrdering": True})


class User(UserMixin):
    user_table = db.user
    user_login_log = db.user_login_log

    def __init__(self, mobile):
        self.mobile = mobile

    def get_id(self):
        try:
            return self.mobile
        except AttributeError:
            raise NotImplementedError('No `id` attribute - override `get_id`')

    def check_user(self):
        flag = config.app_config.get('OPEN_REGISTER')
        if not flag:
            if self.find_user():
                flag = True

        return flag

    def find_user(self):
        return self.user_table.find_one({'mobile': self.mobile})

    def insert_user(self):
        course = {
            'mobile': self.mobile,
        }
        if not self.user_table.find_one({'mobile': self.mobile}):
            self.user_table.insert_one(course)

        return self.mobile

    def login_log(self, request):
        course = {
            'mobile': self.mobile,
            'ip': request.remote_addr,
            'header': json.dumps(dict(request.headers)),
            'datetime': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        }
        return self.user_login_log.insert_one(course)
