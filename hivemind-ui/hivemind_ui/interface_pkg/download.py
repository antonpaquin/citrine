import hashlib
import os
import requests
import threading
from typing import *


import hivemind_ui.config as config


# TODO fix ui download
# This file lazily copy-pasted from the daemon version
# Consider rewriting with the needs of UI in mind
# I just replaced all the errors with RuntimeError...


bytes_64k = 2**16
download_lock = {}  # type: Dict[str, threading.Lock]


def job_put_extra(*args):
    # Placeholder / stub
    pass


def get_file(link: str, hash_expected: str) -> str:
    download_path = os.path.join(config.get_config('storage.rootpath'), 'download')
    fpath = os.path.join(download_path, hash_expected)
    if os.path.isfile(fpath):
        return fpath

    part_fpath = fpath + '.part'
    if part_fpath in download_lock and download_lock[part_fpath].locked():
        raise RuntimeError(f'Could not acquire lock for file {part_fpath}')
    if part_fpath not in download_lock:
        download_lock[part_fpath] = threading.Lock()

    with download_lock[part_fpath]:
        req_headers = {}
        if os.path.isfile(part_fpath):
            accept_ranges, content_length = test_range(link)
            if accept_ranges:
                start_offset = os.path.getsize(part_fpath)
                req_headers['Range'] = f'bytes={start_offset}-{content_length}'
            else:
                os.remove(part_fpath)

        with requests.get(link, headers=req_headers, stream=True) as r:
            try:
                r.raise_for_status()
            except requests.exceptions.HTTPError as e:
                raise RuntimeError(f'Failed to download file: {str(e)}')
            if 'Content-Length' in r.headers:
                job_put_extra('download-size', int(r.headers['Content-Length']))

            with open(part_fpath, 'ab') as out_f:
                fsize = os.path.getsize(part_fpath)
                job_put_extra('download-progress', fsize)
                for chunk in r.iter_content(chunk_size=bytes_64k):
                    fsize += out_f.write(chunk)
                    job_put_extra('download-progress', fsize)

        shasum = hashlib.sha256()
        with open(part_fpath, 'rb') as in_f:
            while True:
                data = in_f.read(bytes_64k)
                if not data:
                    break
                shasum.update(data)

        hash_actual = shasum.hexdigest()
        if hash_actual != hash_expected:
            os.remove(part_fpath)
            raise RuntimeError(f'File hash {hash_actual} did not match expected value {hash_expected}')

        os.rename(part_fpath, fpath)
        return fpath


def test_range(link):
    r = requests.head(link)
    if r.status_code != 200:
        raise RuntimeError(f'Request for URL {link} failed with error code {r.status_code}')
    if not 'Accept-Ranges' in r.headers and 'Content-Length' in r.headers:
        return False, 0
    if r.headers['Accept-Ranges'] == 'none':
        return False, 0
    return True, r.headers['Content-Length']
