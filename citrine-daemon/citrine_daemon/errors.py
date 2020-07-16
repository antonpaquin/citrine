import traceback
from typing import Dict

from citrine_daemon.server.json import CitrineEncoder


class CitrineException(Exception):
    name = 'Root Error'
    default_code = 500

    def __init__(self, msg, status_code=None, data=None):
        super(CitrineException, self).__init__(msg)
        self.msg = msg
        if status_code is None:
            status_code = self.default_code
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


class JobInterrupted(CitrineException): name = 'Job Interrupted'

class InternalError(CitrineException): name = 'Internal Error'
class ModelRunError(InternalError): name = 'Model Run Error'

class PackageError(CitrineException): name = 'Package Error'
class PackageInstallError(PackageError): name = 'Package Install Error'
class PackageAlreadyExists(PackageInstallError): name = 'Package Already Exists'
class PackageStorageError(PackageError): name = 'Package Storage Error'
class RepositoryError(PackageError): name = 'Repository Error'

class DownloadException(CitrineException): name = 'Download Exception'
class DownloadCollision(DownloadException): name = 'Download Collision'
class HashMismatch(DownloadException): name = 'Hash Mismatch'
class RemoteFailedError(DownloadException): name = 'Remote Server Error'

class DatabaseError(CitrineException): name = 'Database Error'
class DatabaseMissingEntry(DatabaseError): name = 'Missing Entry'
class DatabaseCollision(DatabaseError): name = 'Database Collision'

class InvalidInput(CitrineException):
    name = 'Invalid Input'
    default_code = 400
class MissingFunction(InvalidInput): name = 'Missing Function'
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


CitrineEncoder.register_encoder(CitrineException, lambda x: x.to_dict())
CitrineEncoder.register_encoder(Exception, serialize_unknown_exception)

