import logging
from datetime import timedelta

from redis import StrictRedis


class Config(object):
    DEBUG = True  # 开启调试模式
    SQLALCHEMY_DATABASE_URI = "mysql://root:mysql@127.0.0.1:3306/info16"  # mysql的连接地址
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # 决定是否追踪数据库变化
    REDIS_HOST = "127.0.0.1"  # redis的ip
    REDIS_PORT = 6379  # redis的端口
    SESSION_TYPE = "redis"  # session存储的数据库类型
    SESSION_REDIS = StrictRedis(host=REDIS_HOST, port=REDIS_PORT)  # 设置session存储使用的redis的连接对象
    SESSION_USE_SIGNER = True  # 对cookie中保存的session进行加密（需要使用app的密钥）
    SECRET_KEY = "32SwTkJya/j6RLvQyx++TrPXQqQU30tjMWzw4VpGQCdr5SVohLYBDZhjmHWgIxNV"
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)  # 设置session存储时间
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True  # 每次在请求结束后,都会自动提交

class DevelopConfig(Config):  # 定义开发环境的配置
    DEBUG = True
    LOGLEVEL = logging.DEBUG


class ProductConfig(Config):  # 定义生产环境的配置
    DEBUG = False
    LOGLEVEL = logging.ERROR


# 设置配置字典
config_dict = {
    "dev": DevelopConfig,
    "pro": ProductConfig
}