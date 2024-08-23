import asyncio

from typing import Coroutine, Callable, Literal
from signal import signal, SIGINT


class QueueItem:
    def __init__(self, coroutine: Callable | Coroutine, must_complete=False, *args, **kwargs):
        self.coroutine = coroutine
        self.args = args
        self.kwargs = kwargs
        self.must_complete = must_complete
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
    def __init__(self, size: int = 0, workers: int = 1000, timeout: int = 60,
                 queue: asyncio.Queue = None, on_exit: Literal['cancel', 'complete_priority'] = 'cancel'):
        self.queue = queue or asyncio.PriorityQueue(maxsize=size)
        self.workers = workers
        self.tasks = []
        self.priority_tasks = set()  # tasks that must complete
        self.timeout = timeout
        self.stop = False
        self.on_exit = on_exit
        self.cancelled = False
        self.main_task = None
        signal(SIGINT, self.sigint_handle)

    def add(self, *, item: QueueItem, priority=3):
        try:
            if not self.stop:
                if isinstance(self.queue, asyncio.PriorityQueue):
                    self.priority_tasks.add(item) if item.must_complete else ...
                    item = (priority, item)
                self.queue.put_nowait(item)
        except asyncio.QueueFull:
            ...

    async def worker(self):
        while True:
            try:
                print('this should not be running') if self.cancelled else ...
                if isinstance(self.queue, asyncio.PriorityQueue):
                    _, item = self.queue.get_nowait()
                else:
                    item = self.queue.get_nowait()
                if not self.stop or item.must_complete:
                    await item.run()
                self.queue.task_done()
                self.priority_tasks.discard(item)

            except asyncio.QueueEmpty:
                return

            except Exception as err:
                print(f"An error occurred while running worker: {err}")
                # break

    def sigint_handle(self, sig, frame):
        print('SIGINT received, cancelling tasks...')
        self.stop = True
        self.cancel()

    async def cleanup(self):
        match self.on_exit:
            case 'complete_priority':
                print('Completing priority tasks...')
                self.stop = True
                self.timeout = None
                await self.run()
                # await asyncio.gather(*[item.run() for item in self.priority_tasks])
            case _:
                ...

    async def run(self, timeout: int = 0):
        loop = asyncio.get_running_loop()
        start = loop.time()

        try:
            self.tasks.extend(asyncio.create_task(self.worker()) for _ in range(self.workers))
            self.tasks.append(task := asyncio.create_task(self.queue.join(), name='queue join'))
            self.main_task = task
            await asyncio.wait_for(self.main_task, timeout=timeout or self.timeout)

        except asyncio.CancelledError as _:
            print(f'Tasks cancelled after {(loop.time() - start)} seconds.')
            print(self.main_task, self.main_task.done(), self.main_task.cancelled(), self.main_task.get_name())
            await self.cleanup()

        except TimeoutError:
            print(f"Tasks timed out after {(loop.time() - start)} seconds."
                  f"{self.queue.qsize()} tasks remaining in queue, {len(self.priority_tasks)} are priority tasks")
            await self.cleanup()

        finally:
            print(f'Exiting queue after {(loop.time() - start)} seconds.'
                  f'{self.queue.qsize()} tasks remaining, {len(self.priority_tasks)} are priority tasks')
            self.cancel()

    async def ran(self, timeout: int = None):
        self.tasks.extend(asyncio.create_task(self.worker()) for _ in range(self.workers))
        await self.join(timeout=timeout)
        self.cancel()

    def cancel(self):
        print(f"Cancelling {len(self.tasks)} worker tasks")
        cancelled = [task.cancel() for task in self.tasks if not task.done()]
        print(f'Cancelled {len(cancelled)} worker tasks')
        self.tasks.clear()
        self.cancelled = True
