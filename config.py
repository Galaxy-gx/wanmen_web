from dotenv import find_dotenv, load_dotenv
import os

load_dotenv(find_dotenv())

app_config = {
    'SECRET_KEY': os.environ.get('SECRET_KEY'),
    'MONGO_CONFIG': os.environ.get('MONGO_CONFIG'),
}

app_msg = {
    '0': '操作成功',
    '101': '手机号或验证码有误',
    '102': '手机号没有权限操作',
    '103': '手机号验证失败',
    'default': '操作失败'
}
