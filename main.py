from flask_migrate import Migrate, MigrateCommand, Config
from flask_script import Manager
from flask import Flask
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from redis import StrictRedis

from Info import create_app

# 创建应用
app = create_app("dev")
# 创建管理器
mgr = Manager(app)
# 添加迁移命令
mgr.add_command("mc",MigrateCommand)

if __name__ == '__main__':
    mgr.run()  # 在环境变量中添加runserver (-h -p等参数)
