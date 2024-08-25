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
    def __init__(self, size: int = 0, workers: int = 50, timeout: int = 60,
                 queue: asyncio.Queue = None, on_exit: Literal['cancel', 'complete_priority'] = 'complete_priority'):
        self.queue = queue or asyncio.PriorityQueue(maxsize=size)
        self.workers = workers
        self.tasks = []
        self.priority_tasks = set()  # tasks that must complete
        self.timeout = timeout
        self.stop = False
        self.on_exit = on_exit
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
        counter = 5
        while True:
            try:
                if isinstance(self.queue, asyncio.PriorityQueue):
                    _, item = self.queue.get_nowait()
                else:
                    item = self.queue.get_nowait()
                if not self.stop or item.must_complete:
                    await item.run()
                self.queue.task_done()
                self.priority_tasks.discard(item)

            except asyncio.QueueEmpty:
                if counter:
                    await asyncio.sleep(counter)
                    counter -= 1
                else:
                    break

    def sigint_handle(self, sig, frame):
        print('SIGINT received, cleaning up...')

        if self.on_exit == 'complete_priority':
            print(f'Completing {len(self.priority_tasks)} priority tasks...')
            self.stop = True

        else:
            self.cancel()

        self.on_exit = 'cancel'  # force cancel on exit if SIGINT is received again
                
    async def run(self, timeout: int = 0):
        loop = asyncio.get_running_loop()
        start = loop.time()

        try:
            self.tasks.extend(asyncio.create_task(self.worker()) for _ in range(self.workers))
            task = asyncio.create_task(self.queue.join())
            self.tasks.append(task)
            await asyncio.wait_for(task, timeout = timeout or self.timeout)

        except TimeoutError:
            print(f"Timed out after {loop.time() - start} seconds. {self.queue.qsize()} tasks remaining")

            if self.on_exit == 'complete_priority' and self.priority_tasks:
                print(f'Completing {len(self.priority_tasks)} priority tasks...')
                self.stop = True
                await self.queue.join()

            else:
                self.cancel()

        except asyncio.CancelledError:
            print('Tasks cancelled')

        finally:
            print(f'Exiting queue after {(loop.time() - start)} seconds.'
                  f'{self.queue.qsize()} tasks remaining, {len(self.priority_tasks)} are priority tasks')

        self.cancel()

    def cancel(self):
        cancelled = [task.cancel() for task in self.tasks if not task.done()]
        print(f'Cancelled {len(cancelled)} worker tasks') if cancelled else ...
        self.tasks.clear()
