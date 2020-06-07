import traceback
from typing import Dict

from hivemind_daemon.server.json import HivemindEncoder


class HivemindException(Exception):
    name = 'Root Error'
    
    def __init__(self, msg, status_code=500, data=None):
        super(HivemindException, self).__init__(msg)
        self.msg = msg
        self.status_code = status_code
        self.data = data
        
    def to_dict(self) -> Dict:
        res = {
            'error': self.name,
            'msg': self.msg,
            'status_code': self.status_code,
        }
        if self.data is not None:
            res['data'] = self.data
        return res


class JobInterrupted(HivemindException): name = 'Job Interrupted'

class InternalError(HivemindException): name = 'Internal Error'
class ModelRunError(InternalError): name = 'Model Run Error'

class PackageError(HivemindException): name = 'Package Error'
class PackageInstallError(PackageError): name = 'Package Install Error'
class PackageStorageError(PackageError): name = 'Package Storage Error'
class RepositoryError(PackageError): name = 'Repository Error'

class DownloadException(HivemindException): name = 'Download Exception'
class DownloadCollision(DownloadException): name = 'Download Collision'
class HashMismatch(DownloadException): name = 'Hash Mismatch'
class RemoteFailedError(DownloadException): name = 'Remote Server Error'

class DatabaseError(HivemindException): name = 'Database Error'
class DatabaseMissingEntry(DatabaseError): name = 'Missing Entry'
class DatabaseCollision(DatabaseError): name = 'Database Collision'

class InvalidInput(HivemindException):
    name = 'Invalid Input'
    def __init__(self, msg, status_code=400, data=None):
        super(InvalidInput, self).__init__(msg, status_code=status_code, data=data)

class MissingEndpoint(InvalidInput): name = 'Missing Endpoint'
class InvalidTensor(InvalidInput): name = 'Invalid Tensor'
class NoSuchJob(InvalidInput): name = 'No such job'
class ValidationError(InvalidInput): name = 'Validation Error'


def serialize_unknown_exception(exc: Exception):
    # Debug tool to show unknown exceptions in request response.
    # Probably a good idea to disable by default
    return {
        'name': exc.__class__.__name__,
        'msg': exc.args,
        'traceback': traceback.format_list(traceback.extract_tb(exc.__traceback__)),
    }


HivemindEncoder.register_encoder(HivemindException, lambda x: x.to_dict())
HivemindEncoder.register_encoder(Exception, serialize_unknown_exception)

