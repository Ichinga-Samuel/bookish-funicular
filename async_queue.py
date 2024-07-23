import asyncio

from dict_db import DictDB
from task_queue import TaskQueue, QueueItem
from api import API


class AsyncQueue:

    def __init__(self, db=None, timeout=60, size=0):
        self.connections = []
        self.visited = set()
        self.db = db or DictDB()
        self.task_queue = TaskQueue(size=size, timeout=timeout)
        self.api = API()

    async def get_user(self, *, user_id):
        res = await self.api.get_user(user_id=user_id)
        self.db.save(data=res)

    async def get_by_id(self, *, item_id):
        try:
            if item_id in self.visited:
                return
            res = await self.api.get_by_id(item_id=item_id)
            self.db.save(data=res)
            if 'kids' in res:
                [self.task_queue.add(QueueItem(self.get_by_id, item_id=item)) for item in res['kids']]

            if 'by' in res and res['by'] not in self.visited:
                self.task_queue.add(QueueItem(self.get_user, user_id=res['by']))
            return res
        except Exception as err:
            print(err)

    async def traverse_api(self):
        s, j, t, a = await asyncio.gather(self.api.show_stories(), self.api.job_stories(), self.api.top_stories(),
                                          self.api.ask_stories())
        stories = set(s) | set(j) | set(t) | set(a)
        [self.task_queue.add(QueueItem(self.get_by_id, item_id=itd)) for itd in stories]
        await self.task_queue.run()
