from logging.handlers import RotatingFileHandler
import logging
from flask import Flask, g, render_template
from flask_migrate import Migrate
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from redis import StrictRedis

from Config import config_dict
# from Info.modules.home import home_blu  注意循环导入的问题！！！

db = None
sr = None


# 配置日志文件(将日志信息写入到文件中)
def setup_log(level):
    # 设置日志的记录等级
    logging.basicConfig(level=level)  # 调试debug级
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
    sr = StrictRedis(host=config_class.REDIS_HOST, port=config_class.REDIS_PORT, decode_responses=True)  # 这里要进行解码配置，因为从redis库里取出的数据是bytes类型的
    # 初始化Session存储对象
    Session(app)
    # 初始化迁移器(这里有点不熟悉，注意！！！)
    Migrate(app,db)

    # 3.注册蓝图
    from Info.modules.home import home_blu
    app.register_blueprint(home_blu)

    from Info.modules.passport import passport_blu
    app.register_blueprint(passport_blu)

    from Info.modules.news import news_blu
    app.register_blueprint(news_blu)

    from Info.modules.user import user_blu
    app.register_blueprint(user_blu)

    from Info.modules.admin import admin_blu
    app.register_blueprint(admin_blu)

    # 配置日志文件
    setup_log(config_class.LOGLEVEL)

    # 让模型文件和主程序建立关系
    # from info.models import *  # import * 语法不能在局部作用域中使用
    # 可以使用 import Info.models
    from Info import models  # 因为这里之前我没有建立关系所以导致我数据迁移生成版本的时候出现了错误

    # 添加自定义的过滤器
    from Info.common import index_convert  # 哪用放哪
    app.add_template_filter(index_convert, "index_convert")

    from Info.common import user_login_data  # 还是上面的问题

    # 监听404错误
    @app.errorhandler(404)
    @user_login_data
    def page_not_found(e):  # 这个参数是发生错误的信息,必须要的参数
        user = g.user
        user = user.to_dict() if user else None
        # 渲染404页面
        return render_template("news/404.html", user=user)

    return app

