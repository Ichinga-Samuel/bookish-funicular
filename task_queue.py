import asyncio
from typing import Coroutine, Callable
from signal import signal, SIGINT, SIGTERM


class QueueItem:
    def __init__(self, coroutine: Callable | Coroutine, *args, **kwargs):
        self.coroutine = coroutine
        self.args = args
        self.kwargs = kwargs

    async def run(self):
        try:
            return await self.coroutine(*self.args, **self.kwargs)
        except Exception as err:
            print('err')


class TaskQueue:
    def __init__(self, size=0, workers=0, timeout=60):
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

    def sigterm_handle(self, sig, frame):
        raise KeyboardInterrupt
    
    def sigint_handle(self, sig, frame):
        self.stop = True

    async def join(self):
        try:
            signal(SIGINT, self.sigint_handle)
            signal(SIGTERM, self.sigterm_handle)
            await asyncio.wait_for(self.queue.join(), timeout=self.timeout)
        except (TimeoutError, KeyboardInterrupt) as exe:
            print('Timed out or Interrupted', exe)

    async def run(self):
        workers = self.workers or self.queue.qsize()
        self.tasks.extend(asyncio.create_task(self.worker()) for _ in range(workers))
        await self.join()
        await self.cancel()

    async def cancel(self):
        self.tasks = [task.cancel() for task in self.tasks]
        await asyncio.gather(*self.tasks, return_exceptions=True)
