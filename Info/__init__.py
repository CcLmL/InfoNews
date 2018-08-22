from flask import Flask
from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from redis import StrictRedis

from Config import config_dict

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
    # 创建管理器
    mgr = Manager(app)
    # 初始化迁移命令
    Migrate(app, db)
    # 添加迁移命令
    mgr.add_command("mc", MigrateCommand)

    return app

