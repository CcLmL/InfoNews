import datetime
import random

from flask import current_app
from flask_migrate import MigrateCommand
from flask_script import Manager
from Info import create_app

# 创建应用
app = create_app("dev")
# 创建管理器
mgr = Manager(app)
# 添加迁移命令
mgr.add_command("mc",MigrateCommand)


# 生成超级管理员
@mgr.option("-u", dest="username")
@mgr.option("-p", dest="password")
def create_superuser(username, password):
    if not all([username, password]):
        print("账号/密码不正确")
        return

    from Info.models import User
    from Info import db
    # 创建用户模型
    user = User()
    user.mobile = username
    user.password = password
    user.nick_name = username
    user.is_admin = True

    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        print("生成失败")
        return

    print("生成管理员成功")


# 添加测试用户
def add_test_users():
    from Info import db
    from Info.models import User
    users = []
    now = datetime.datetime.now()
    for num in range(10000):
        try:
            user = User()
            user.nick_name = "%011d" % num
            user.mobile = "%011d" % num
            user.password_hash = "pbkdf2:sha256:50000$SgZPAbEj$a253b9220b7a916e03bf27119d401c48ff4a1c81d7e00644e0aaf6f3a8c55829"
            user.last_login = now - datetime.timedelta(seconds=random.randint(0,2678400))
            user.create_time = now - datetime.timedelta(seconds=random.randint(0,2678400))
            users.append(user)
            print(user.mobile)
        except Exception as e:
            print(e)

    db.session.add_all(users)
    db.session.commit()
    print("OK again")


if __name__ == '__main__':
    mgr.run()  # 在环境变量中添加runserver (-u -p等参数)
    # add_test_users()
