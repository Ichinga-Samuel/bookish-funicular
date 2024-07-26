import asyncio
from logging import getLogger

from typing import Coroutine, Callable
from signal import signal, SIGINT

logger = getLogger(__name__)


class QueueItem:
    def __init__(self, coroutine: Callable | Coroutine, *args, **kwargs):
        self.coroutine = coroutine
        self.args = args
        self.kwargs = kwargs
        self.time = asyncio.get_event_loop().time()

    def __lt__(self, other):
        return self.time < other.time

    async def run(self):
        try:
            await self.coroutine(*self.args, **self.kwargs)
        except Exception as err:
            logger.error(f"An error occurred while running coroutine: {err}")


class TaskQueue:
    def __init__(self, size=0, workers=10, timeout=60, queue=None):
        self.queue = queue or asyncio.PriorityQueue(maxsize=size)
        self.workers = workers
        self.tasks = []
        self.timeout = timeout
        self.stop = False

    def add(self, *, item: QueueItem, priority=2):
        try:
            if isinstance(self.queue, asyncio.PriorityQueue):
                item = (priority, item)
            self.queue.put_nowait(item) if not self.stop else ...
        except asyncio.QueueFull:
            return

    async def worker(self):
        while True:
            try:
                if isinstance(self.queue, asyncio.PriorityQueue):
                    _, item = await self.queue.get_nowait()
                else:
                    item = self.queue.get_nowait()
                await item.run()
                self.queue.task_done()
            except asyncio.QueueEmpty:
                logger.warning('Queue is empty. Exiting worker')
                break
    
    def sigint_handle(self, sig, frame):
        self.stop = True
        self.cancel()

    async def join(self):
        try:
            signal(SIGINT, self.sigint_handle)
            await asyncio.wait_for(self.queue.join(), timeout=self.timeout)
        except asyncio.CancelledError as _:
            logger.warning(f"Task was cancelled")
        except TimeoutError:
            self.stop = True

    async def run(self):
        workers = self.workers
        self.tasks.extend(asyncio.create_task(self.worker()) for _ in range(workers))
        await self.join()
        self.cancel()

    def cancel(self):
        for task in self.tasks:
            res = task.cancel()
            self.tasks.remove(task) if res else ...        
