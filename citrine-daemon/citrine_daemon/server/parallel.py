import asyncio
import logging
from queue import Queue
import threading
import time
from typing import *
from uuid import uuid4

import stopit

from citrine_daemon import errors, package
from citrine_daemon.server.json import CitrineEncoder


logger = logging.getLogger(__name__)

primary_job_queue = Queue(maxsize=1000)
job_cache_hold_time = 60
job_cache: Dict[str, 'AsyncFuture'] = {}

thread_local = threading.local()
thread_local.active_job = None

uuid = lambda: str(uuid4()).replace('-', '')
# TODO janitor
# Old results (in fs / db), old futures, old packages should be cleaned up at a configurable interval


class FutureState:
    INITIALIZED = 0
    RUNNING = 1
    DONE = 2
    ERROR = -1
    INTERRUPTED = -2

    @staticmethod
    def get_msg(state):
        return {
            FutureState.INITIALIZED: 'Initializing',
            FutureState.RUNNING: 'In Progress',
            FutureState.DONE: 'Done',
            FutureState.ERROR: 'Error',
            FutureState.INTERRUPTED: 'Interrupted',
        }.get(state)


class AsyncFuture(object):
    """
    Utility for crossing thread boundaries from within an asyncio event loop
    """
    
    def __init__(self, fn, args=None, kwargs=None, request_info=None):
        self.fn = fn
        self.args = args or ()
        self.kwargs = kwargs or {}
        self.request_info = request_info
        self.cache_expire = None
        
        self.result_val = None
        self.result_exc = None
        self.extra_data = {}

        self.uid = uuid()  # type: str
        self.thread = None
        # initialized -> running, interrupted
        # running -> done, error, interrupted
        self.state = FutureState.INITIALIZED
        self._state_lock = threading.Lock()

        self._done = asyncio.Event()
        _event_set = self._done.set
        _threadsafe_call = asyncio.get_running_loop().call_soon_threadsafe
        self.set_done = lambda: _threadsafe_call(_event_set)
        job_cache[self.uid] = self
        
    def run(self, thread):
        logger.debug('Executing async job')
        if self.state != FutureState.INITIALIZED:
            return
        try:
            self.thread = thread  # Once this is set, thread can be interrupted
            self.transition(FutureState.RUNNING)
            self.result_val = self.fn(*self.args, **self.kwargs)
            self.transition(FutureState.DONE)
            logger.debug('Async job complete')
        except errors.JobInterrupted as e:
            self.result_exc = e
            logger.info('Async job interrupted')
        except Exception as e:
            self.transition(FutureState.ERROR)
            self.result_exc = e
            logger.warning('Async job failed')

        self.set_done()
        
    def transition(self, to_state: int):
        with self._state_lock:
            self.state = to_state
        
    def interrupt(self):
        with self._state_lock:
            if self.state == FutureState.RUNNING:
                stopit.async_raise(self.thread.ident, errors.JobInterrupted('Interrupted by user'))
            if self.state in {FutureState.RUNNING, FutureState.INITIALIZED}:
                self.state = FutureState.INTERRUPTED

    async def result(self):
        await self._done.wait()
        if self.result_exc:
            raise self.result_exc
        else:
            return self.result_val
        
    def to_dict(self):
        res = {
            'uid': self.uid,
            'status': FutureState.get_msg(self.state),
            'data': self.extra_data,
        }
        if self.result_exc:
            res['error'] = self.result_exc
        if self.result_val:
            res['result'] = self.result_val
        return res
    

CitrineEncoder.register_encoder(AsyncFuture, lambda fut: fut.to_dict())


async def run_in_worker(fn, args=None, kwargs=None, request_info=None):
    fut = AsyncFuture(fn, args, kwargs, request_info)
    primary_job_queue.put(fut)
    return await fut.result()


def run_async(fn, args=None, kwargs=None, request_info=None):
    fut = AsyncFuture(fn, args, kwargs, request_info)
    logger.debug(f'Queueing async job {fut.uid}', {'async_job_id': fut.uid})
    primary_job_queue.put(fut)
    return fut


def get_future(uid: str) -> AsyncFuture:
    if uid in job_cache:
        return job_cache[uid]
    raise errors.NoSuchJob(f'No such job {uid}', data={'uid': uid})


def get_active_job() -> Optional[AsyncFuture]:
    return getattr(thread_local, 'active_job', None)


def worker_thread(worker_id: int):
    logger.info(f'Worker {worker_id} initialized')
    self = threading.current_thread()
    while True:
        job: AsyncFuture = primary_job_queue.get()
        thread_local.active_job = job
        logger.debug('Worker starting async job')
        package.db.start_connection()
        try:
            job.run(self)
        except errors.JobInterrupted:
            pass
        package.db.end_connection(commit=(job.state == FutureState.DONE))
        job.cache_expire = time.time() + job_cache_hold_time
        logger.debug('Worker finished async job')
        thread_local.active_job = None
        
        
def janitor_thread():
    logger.info('Janitor initialized')
    while True:
        time.sleep(job_cache_hold_time)
        t = time.time()
        purge_jobs = []
        for job_id, cached_job in job_cache.items():
            if cached_job.cache_expire is None:
                continue
            if cached_job.cache_expire < t:
                purge_jobs.append(job_id)
        for job_id in purge_jobs:
            job_cache.pop(job_id)


def job_put_extra(key: str, value: any):
    fut: AsyncFuture = thread_local.active_job
    fut.extra_data[key] = value


def init_workers(n_workers: int):
    logger.info('Booting threadpool')
    threadpool = []
    for idx in range(n_workers):
        threadpool.append(threading.Thread(
            name=f'worker-{idx}',
            target=worker_thread,
            args=(idx,),
            daemon=True,
        ))
    [t.start() for t in threadpool]
    threading.Thread(
        name='janitor',
        target=janitor_thread,
        daemon=True,
    ).start()
