import asyncio

from typing import Coroutine, Callable
from signal import signal, SIGINT


class QueueItem:
    def __init__(self, coroutine: Callable | Coroutine, *args, **kwargs):
        self.coroutine = coroutine
        self.args = args
        self.kwargs = kwargs

    def __lt__(self, other):
        return True

    async def run(self):
        try:
            await self.coroutine(*self.args, **self.kwargs)
        except Exception as err:
            print(err)


class TaskQueue:
    def __init__(self, size=0, workers=10, timeout=60):
        self.queue = asyncio.PriorityQueue(maxsize=size)
        self.workers = workers
        self.tasks = []
        self.timeout = timeout
        self.stop = False

    def add(self, item: QueueItem, priority=2):
        try:
            self.queue.put_nowait((priority, item)) if not self.stop else ...
        except asyncio.QueueFull:
            return

    async def worker(self):
        while True:
            try:
                _, item = self.queue.get_nowait()
                await item.run()
                self.queue.task_done()
            except asyncio.QueueEmpty:
                print('Queue is empty')
                break
    
    def sigint_handle(self, sig, frame):
        self.stop = True
        self.cancel()

    async def join(self):
        try:
            signal(SIGINT, self.sigint_handle)
            await asyncio.wait_for(self.queue.join(), timeout=self.timeout)
        except asyncio.CancelledError as exe:
            print('Interrupted', exe)
        except TimeoutError:
            self.stop = True

    async def run(self):
        workers = self.workers
        self.tasks.extend(asyncio.create_task(self.worker()) for _ in range(workers))
        await self.join()
        self.cancel()

    def cancel(self):
        [task.cancel() for task in self.tasks]
