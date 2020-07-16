import os
from uuid import uuid4

import numpy as np
from PIL import Image

from citrine_daemon.storage import storage
from citrine_daemon.server.json import CitrineEncoder


# TODO result database
# consider moving this to the sqlite

class FileHandle(object):
    def __init__(self):
        self.fname = str(uuid4()).replace('-', '')
        self.fpath = os.path.join(storage.results_path(), self.fname)

    @staticmethod
    def from_pil_image(img: Image):
        handle = FileHandle()
        img.save(handle.fpath, format='png')
        return handle
    
    @staticmethod
    def from_numpy(array: np.ndarray):
        handle = FileHandle()
        np.savez_compressed(handle.fpath, array=array)
        return handle

    def open(self, *args, **kwargs):
        return open(self.fpath, *args, **kwargs)

    def to_dict(self):
        return {
            'file_ref': self.fname
        }


CitrineEncoder.register_encoder(FileHandle, lambda fh: fh.to_dict())
