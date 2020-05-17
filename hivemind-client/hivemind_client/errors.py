class HivemindClientError(Exception):
    name = 'Base Hivemind Client Error'
    def __init__(self, msg, data=None):
        super().__init__(msg)
        self.msg = msg
        self.data = data or {}

class FileNotFound(HivemindClientError): name = 'File Not Found'
class InvalidOptions(HivemindClientError): name = 'Invalid Options'
class OptionParseError(HivemindClientError): name = 'Option Parse Error'
class ServerError(HivemindClientError): name = 'Server Error'

class InvalidResponse(ServerError): name = 'Invalid Response'
class ConnectionRefused(ServerError): name = 'Connection Refused'
