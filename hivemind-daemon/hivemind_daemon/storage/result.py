import os
from uuid import uuid4

import numpy as np
from PIL import Image

from hivemind_daemon.storage import storage
from hivemind_daemon.server.json import HivemindEncoder


class FileHandle(object):
    def __init__(self):
        self.fname = str(uuid4()).replace('-', '')
        self.fpath = os.path.join(storage.results_path, self.fname)

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
            'fileresult': self.fname
        }


HivemindEncoder.register_encoder(FileHandle, lambda fh: fh.to_dict())
