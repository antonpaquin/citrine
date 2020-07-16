class CitrineClientError(Exception):
    name = 'Base Citrine Client Error'
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


class NoBranch(CitrineClientError): name = 'Code branch should not be possible'

class FileNotFound(CitrineClientError): name = 'File Not Found'
class InvalidOptions(CitrineClientError): name = 'Invalid Options'
class OptionParseError(CitrineClientError): name = 'Option Parse Error'
class ServerError(CitrineClientError): name = 'Server Error'

class InvalidResponse(ServerError): name = 'Invalid Response'
class ConnectionError(ServerError): name = 'Connection Error'
class ConnectionRefused(ConnectionError): name = 'Connection Refused'
