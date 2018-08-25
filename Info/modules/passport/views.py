import random
import re
from datetime import datetime

from flask import request, abort, current_app, make_response, jsonify, session

from Info import sr, db
from Info.lib.yuntongxun.sms import CCP
from Info.models import User
from Info.modules.passport import passport_blu

from Info.utils.captcha.pic_captcha import captcha


# 2.使用蓝图来装饰路由
from Info.utils.response_code import RET, error_map


@passport_blu.route('/get_img_code')
def get_img_code():
    # 获取参数
    img_code_id = request.args.get("img_code_id")
    # 校验参数
    if not img_code_id:
        return abort(403)
    # 生成图片验证码
    img_name, img_code_text, img_code_bytes = captcha.generate_captcha()  # 使用的是第三方工具（utils里面）
    # 将图片key和验证码文字保存到redis数据库中
    # 一旦是关于数据库的操作都应当进行异常捕获,提高程序稳定性
    try:
        sr.set("img_code_id_" + img_code_id, img_code_text, ex=180)
    except Exception as e:
        current_app.logger.error(e)
        return abort(500)
    # 返回验证码图片
    # 创建响应头
    response = make_response(img_code_bytes)
    # 设置响应头
    response.content_type="image/jpeg"
    return response


# 获取短信验证码
@passport_blu.route('/get_sms_code', methods=["POST"])
def get_sms_code():
    # 获取参数   request.json可以获取到application/json格式传过来的json数据
    img_code_id = request.json.get("img_code_id")
    img_code = request.json.get("img_code")
    mobile = request.json.get("mobile")
    # 校验参数
    if not all([img_code_id,img_code,mobile]):
        return jsonify(errno=RET.PARAMERR,errmsg=error_map[RET.PARAMERR])  # 这里使用的是response_code文件里自定义的状态码

    # 校验手机号格式
    if not re.match(r"1[135678]\d{9}$",mobile):
        return jsonify(errno=RET.PARAMERR, errmsg="手机格式不正确")

    # 根据图片key取出验证码文字
    try:
        real_img_code = sr.get("img_code_id_" + img_code_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])
    # 校验图片验证码
    if not real_img_code:  # 校验是否过期
        return jsonify(errno=RET.PARAMERR, errmsg="验证码以过期")

    if img_code.upper() != real_img_code:  # 校验验证码是否正确
        return jsonify(errno=RET.PARAMERR, errmsg="验证码不正确")

    # 校验手机号码的正确性
    # 根据手机号从数据库中取出对应的记录
    try:
        user = User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])

    # 判断该用户是否存在
    if user:  # 提示用户已存在
        return jsonify(errno=RET.DATAEXIST, errmsg=error_map[RET.DATAEXIST])

    # 如果校验成功，发送短信
    # 生成4位随机数字
    sms_code = "%04d" % random.randint(0,9999)
    current_app.logger.info("短信验证码为：%s" % sms_code)
    # res_code = CCP().send_template_sms(mobile, [sms_code, 5], 1)
    # if res_code == -1:  # 短信发送失败
    #     return jsonify(errno=RET.THIRDERR, errmsg=error_map[RET.THIRDERR])

    # 将短信验证码保存到redis
    try:
        sr.set("sms_code_id_" + mobile, sms_code, ex=60)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])
    # 将短信发送结果使用json返回
    return jsonify(errno=RET.OK, errmsg=error_map[RET.OK])


@passport_blu.route('/register', methods=["POST"])
def register():
    # 获取参数  request.json可以获取到application/json格式传过来的json数据
    mobile = request.json.get("mobile")
    password = request.json.get("password")
    sms_code = request.json.get("sms_code")
    # 校验参数
    if not all([mobile, password, sms_code]):
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    # 校验手机格式
    if not re.match(r'1[35678]\d{9}', mobile):
        return jsonify(errno=RET.PARAMERR,errmsg=error_map[RET.PARAMERR])

    # 根据手机号取出短信验证码文字
    try:
        real_sms_code = sr.get("sms_code_id_" + mobile)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg=error_map[RET.DATAERR])
    # 校验短信验证码
    if not real_sms_code:  # 校验是否过期
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    if sms_code != real_sms_code:  # 校验输入短信验证码是否正确
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    # 将用户数据保存到数据库
    user = User()
    user.mobile = mobile
    # 使用计算性属性password对密码加密过程进行封装
    user.password = password
    # print(user.password)  # 在property装饰器中封装了，只要获取这个值时就会抛出一个错误
    user.nick_name = mobile
    # 记录用户最后登陆的时间
    user.last_login = datetime.now()

    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])

    # 状态保持  免密码登陆
    session["user_id"] = user.id

    return jsonify(errno=RET.OK, errmsg=error_map[RET.OK])


# 用户登陆
@passport_blu.route('/login', methods=["POST"])
def login():
    # 获取参数
    mobile = request.json.get("mobile")
    password = request.json.get("password")
    # 校验参数
    if not all([mobile, password]):
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    # 校验手机格式
    if not re.match(r"1[35678]\d{9}", mobile):
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    # 根据手机号从数据库中取出用户模型
    try:
        user = User().query.filter_by(mobile=mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])

    if not user:
        return jsonify(errno=RET.USERERR, errmsg=error_map[RET.USERERR])

    # 校验密码
    if not user.check_password(password):
        return jsonify(errno=RET.PWDERR, errmsg=error_map[RET.PWDERR])

    # 注册用户最后的登陆时间
    user.last_login = datetime.now()
    # 这里本身需要对数据进行提交，但是设置了SQLALCHEMY_COMMIT_ON_TEARDOWN后，就会自动提交了
    # 状态保持
    session["user_id"] = user.id

    # 将校验结果以json返回
    return jsonify(errno=RET.OK, errmsg=error_map[RET.OK])


# 退出登陆
@passport_blu.route('/logout')
def logout():
    # 将用户信息从session中删除  pop可以设置默认值，当减值对不存在时，不会报错并返回默认值
    session.pop("user_id", None)
    # 将结果返回
    return jsonify(errno=RET.OK, errmsg=error_map[RET.OK])
