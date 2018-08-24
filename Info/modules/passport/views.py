import random
import re

from flask import request, abort, current_app, make_response, jsonify

from Info import sr
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

    # 将短信验证码保存到redis
    try:
        sr.set("sms_code_id_" + mobile, sms_code, ex=60)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])
    # 将短信发送结果使用json返回
    return jsonify(errno=RET.OK, errmsg=error_map[RET.OK])