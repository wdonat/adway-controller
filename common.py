import uuid
import sysparam


class LoginSucess:
    def __init__(self):
        self.login_success = 1


class ServerError:
    def __init__(self, code, message):
        self.error_code = code
        self.error_message = message


class ConnectionError:
    def __init__(self, code, message):
        self.error_code = code
        self.error_message = message


class ReceiveLocation:
    def __init__(self, code):
        self.result_code = code


class ContentSuccess:
    def __init__(self, data):
        self.result_data = data


