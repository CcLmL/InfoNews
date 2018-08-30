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


if __name__ == '__main__':
    mgr.run()  # 在环境变量中添加runserver (-u -p等参数)
