class HivemindClientError(Exception):
    name = 'Base Hivemind Client Error'
    def __init__(self, msg, data=None):
        super().__init__(msg)
        self.msg = msg
        self.data = data or {}

    def to_dict(self):
        return {
            'name': self.name,
            'msg': self.msg,
            'data': self.data,
        }


class NoBranch(HivemindClientError): name = 'Code branch should not be possible'

class FileNotFound(HivemindClientError): name = 'File Not Found'
class InvalidOptions(HivemindClientError): name = 'Invalid Options'
class OptionParseError(HivemindClientError): name = 'Option Parse Error'
class ServerError(HivemindClientError): name = 'Server Error'

class InvalidResponse(ServerError): name = 'Invalid Response'
class ConnectionError(ServerError): name = 'Connection Error'
class ConnectionRefused(ConnectionError): name = 'Connection Refused'
