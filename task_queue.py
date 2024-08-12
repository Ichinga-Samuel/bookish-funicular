import asyncio

from typing import Coroutine, Callable, Literal
from signal import signal, SIGINT


class QueueItem:
    def __init__(self, coroutine: Callable | Coroutine, _must_finish=False, *args, **kwargs):
        self.coroutine = coroutine
        self.args = args
        self.kwargs = kwargs
        self.must_finish = _must_finish
        self.time = asyncio.get_event_loop().time()

    def __hash__(self):
        return id(self)

    def __lt__(self, other):
        return self.time < other.time

    async def run(self):
        try:
            await self.coroutine(*self.args, **self.kwargs)
        except Exception as err:
            print(f"An error occurred while running coroutine: {err}")


class TaskQueue:
    def __init__(self, size: int = 0, workers: int = 20, timeout: float = None,
                 queue: asyncio.Queue = None, on_timeout: Literal['cancel', 'finish', 'must_finish'] = 'cancel'):
        self.queue = queue or asyncio.PriorityQueue(maxsize=size)
        self.workers = workers
        self.tasks = []
        self.must_finish = set()
        self.timeout = timeout
        self.stop = False
        self.on_timeout = on_timeout

    def add(self, *, item: QueueItem, priority=1):
        try:
            if self.stop:
                return
            self.must_finish.add(item) if item.must_finish else ...
            if isinstance(self.queue, asyncio.PriorityQueue):
                item = (priority, item)
            self.queue.put_nowait(item)
        except asyncio.QueueFull:
            ...

    async def worker(self):
        while True:
            try:
                if isinstance(self.queue, asyncio.PriorityQueue):
                    _, item = self.queue.get_nowait()
                else:
                    item = self.queue.get_nowait()
                await item.run()
                self.queue.task_done()
                self.must_finish.discard(item)
            except asyncio.QueueEmpty:
                print('Queue is empty. Exiting worker')
                break
            except Exception as err:
                print(f"An error occurred while running worker: {err}")
                break

    def sigint_handle(self, sig, frame):
        self.stop = True
        self.cancel()

    async def join(self, timeout=None):
        start = asyncio.get_event_loop().time()
        
        try:
            signal(SIGINT, self.sigint_handle)
            await asyncio.wait_for(self.queue.join(), timeout=timeout)
        
        except asyncio.CancelledError as _:
            print(f"Task was cancelled")
            
        except TimeoutError:
            print(f"Tasks timed out after {(asyncio.get_event_loop().time() - start)} seconds."
                  f"{self.queue.qsize()} tasks remaining in queue")
            self.stop = True
            if self.queue.qsize() == 0:
                return
            match self.on_timeout:
                case 'cancel':
                    self.cancel()
                case 'finish':
                    await self.queue.join()
                case 'must_finish':
                    await asyncio.gather(*[item.run() for item in self.must_finish])
                case _:
                    ...
        finally:
            print(f'Exiting queue after {(asyncio.get_event_loop().time() - start)} seconds.'
                  f' {self.queue.qsize()} tasks remaining')

    async def run(self):
        workers = self.workers
        self.tasks.extend(asyncio.create_task(self.worker()) for _ in range(workers))
        await self.join(timeout=self.timeout)
        self.cancel()

    def cancel(self):
        for task in self.tasks:
            res = task.cancel()
            self.tasks.remove(task) if res else ...
