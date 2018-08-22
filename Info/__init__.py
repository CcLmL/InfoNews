from logging.handlers import RotatingFileHandler
import logging
from flask import Flask
from flask_migrate import Migrate
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from redis import StrictRedis

from Config import config_dict
# from Info.modules.home import home_blu  注意循环导入的问题！！！

db = None
sr = None


# 配置日志文件(将日志信息写入到文件中)
def setup_log():
    # 设置日志的记录等级
    logging.basicConfig(level=logging.DEBUG)  # 调试debug级
    # 创建日志记录器，指明日志保存的路径、每个日志文件的最大大小、保存的日志文件个数上限
    file_log_handler = RotatingFileHandler("logs/log", maxBytes=1024 * 1024 * 100, backupCount=10)
    # 创建日志记录的格式 日志等级 输入日志信息的文件名 行数 日志信息
    formatter = logging.Formatter('%(levelname)s %(pathname)s:%(lineno)d %(message)s')
    # 为刚创建的日志记录器设置日志记录格式
    file_log_handler.setFormatter(formatter)
    # 为全局的日志工具对象（flask app使用的）添加日志记录器
    logging.getLogger().addHandler(file_log_handler)


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
