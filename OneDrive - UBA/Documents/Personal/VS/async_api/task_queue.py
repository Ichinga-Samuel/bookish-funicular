import asyncio
from typing import Coroutine, Callable, Awaitable
from signal import signal, SIGINT, SIGTERM


class QueueItem:
    def __init__(self, coroutine: Callable | Awaitable | Coroutine, *args, **kwargs):
        self.coroutine = coroutine
        self.args = args
        self.kwargs = kwargs

    async def run(self):
        try:
            return await self.coroutine(*self.args, **self.kwargs)
        except Exception as err:
            print('err')


class TaskQueue:
    def __init__(self, size=0, workers=0, timeout=None):
        self.queue = asyncio.Queue(maxsize=size)
        self.workers = workers
        self.tasks = []
        self.timeout = timeout
        self.stop = False

    def add(self, item: QueueItem):
        try:
            self.queue.put_nowait(item) if not self.stop else ...
        except asyncio.QueueFull:
            return

    async def worker(self):
        while True:
            try:
                item: QueueItem = self.queue.get_nowait()
                await item.run()
                self.queue.task_done()
            except asyncio.QueueEmpty:
                break

    def sig_handle(self, sig, frame):
        self.stop = True

    async def join(self):
        try:
            signal(SIGINT, self.sig_handle)
            signal(SIGTERM, self.sig_handle)
            await asyncio.wait_for(self.queue.join(), timeout=self.timeout)
        except TimeoutError:
            self.stop = True

    async def run(self):
        workers = self.workers or self.queue.qsize()
        self.tasks.extend(asyncio.create_task(self.worker()) for _ in range(workers))
        await self.join()
        await self.cancel()

    async def cancel(self):
        for task in self.tasks:
            task.cancel()
        await asyncio.gather(*self.tasks, return_exceptions=True)
