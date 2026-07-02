"""统一错误码定义"""

ERROR_CODES = {
    200: 'ok',
    201: 'created',
    400: 'bad_request',
    401: 'unauthorized',
    403: 'forbidden',
    404: 'not_found',
    409: 'conflict',
    422: 'unprocessable_entity',
    500: 'internal_server_error',
}


def success(data=None, message='ok', code=200):
    return {'code': code, 'data': data, 'message': message}, code


def error(code=400, message=None):
    messages = {
        400: '请求参数有误',
        401: '请先登录',
        403: '无权限访问',
        404: '资源不存在',
        409: '数据冲突',
        422: '业务校验失败',
        500: '服务器内部错误',
    }
    return {'code': code, 'data': None, 'message': message or messages.get(code, '未知错误')}, code
