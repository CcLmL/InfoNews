from flask_migrate import Migrate, MigrateCommand, Config
from flask_script import Manager
from flask import Flask
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from redis import StrictRedis


@app.route('/')
def index():
    return 'hello world'


if __name__ == '__main__':
    mgr.run()  # 在环境变量中添加runserver (-h -p等参数)
