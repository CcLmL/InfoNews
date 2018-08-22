from flask import Flask
from flask_migrate import Migrate
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from redis import StrictRedis

from Config import config_dict
# from Info.modules.home import home_blu  注意循环导入的问题！！！

db = None
sr = None


# 定义函数来封装应用的创建   工厂函数
def create_app(config_type):
    # 根据配置类型取出配置类
    config_class = config_dict[config_type]

    app = Flask(__name__)
    # 根据配置类来加载应用配置
    app.config.from_object(config_class)

    # 声明全局变量
    global db, sr
    #  创建数据库连接对象
    db = SQLAlchemy(app)
    # 创建redis连接对象，用于存储session
    sr = StrictRedis(host=config_class.REDIS_HOST, port=config_class.REDIS_PORT)
    # 初始化Session存储对象
    Session(app)
    # 初始化迁移器(这里有点不熟悉，注意！！！)
    Migrate(app,db)

    # 3.注册蓝图
    from Info.modules.home import home_blu
    app.register_blueprint(home_blu)

    return app

