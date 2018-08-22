from datetime import timedelta

from flask import Flask
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from redis import StrictRedis


class Config(object):
    DEBUG = True  # 开启调试模式
    SQLALCHEMY_DATABASE_URI = "mysql://root:mysql@127.0.0.1:3306/flask01"  # mysql的连接地址
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # 决定是否追踪数据库变化
    REDIS_HOST = "127.0.0.1"  # redis的ip
    REDIS_PORT = 6379  # redis的端口
    SESSION_TYPE = "redis"  # session存储的数据库类型
    SESSION_REDIS = StrictRedis(host=REDIS_HOST, port=REDIS_PORT)  # 设置session存储使用的redis的连接对象
    SESSION_USE_SIGNER = True  # 对cookie中保存的session进行加密（需要使用app的密钥）
    SECRET_KEY = "32SwTkJya/j6RLvQyx++TrPXQqQU30tjMWzw4VpGQCdr5SVohLYBDZhjmHWgIxNV"
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)  # 设置session存储时间


app = Flask(__name__)
# 根据配置类来加载应用配置
app.config.from_object(Config)
#  创建数据库连接对象
db = SQLAlchemy(app)
# 创建redis连接对象，用于存储session
sr = StrictRedis(host=Config.REDIS_HOST, port=Config.REDIS_PORT)
# 初始化Session存储对象
Session(app)


@app.route('/')
def index():
    return 'hello world'


if __name__ == '__main__':
    app.run(debug=True)