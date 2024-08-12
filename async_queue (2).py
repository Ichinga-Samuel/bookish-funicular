import asyncio
from logging import getLogger

from .task_queue import TaskQueue, QueueItem
from .api import API
from .save_to_db import save_item, save_user

logger = getLogger(__name__)


class AsyncQueue:

    def __init__(self, **task_queue_kwargs):
        self.connections = []
        self.visited = set()
        self.task_queue = TaskQueue(**task_queue_kwargs)
        self.api = API()

    async def get_user(self, *, user_id):
        try:
            res = await self.api.get_user(user_id=user_id)
            self.task_queue.add(item=QueueItem(save_user, _must_finish=True, user=res), priority=0)

            if submitted := res.get('submitted', []):
                [self.task_queue.add(item=QueueItem(self.get_by_id, item_id=item), priority=4) for item in submitted]
        except Exception as err:
            logger.error(f"{err} in getting user")

    async def get_by_id(self, *, item_id):
        try:
            if item_id in self.visited:
                return
            res = await self.api.get_by_id(item_id=item_id)
            self.visited.add(res['id'])

            if (by := res.get('by')) and by not in self.visited:
                self.task_queue.add(item=QueueItem(self.get_user, user_id=by), priority=1)

            if (parent := res.get('parent')) and parent not in self.visited:
                self.task_queue.add(item=QueueItem(self.get_by_id, item_id=parent), priority=2)

            self.task_queue.add(item=QueueItem(save_item, _must_finish=True, item=res), priority=0)

            if kids := res.get('kids', []):
                [self.task_queue.add(item=QueueItem(self.get_by_id, item_id=item), priority=4) for item in kids]

            return res
        except Exception as err:
            logger.error(f"{err} in getting item")

    async def traverse_api(self):
        s, j, t, a = await asyncio.gather(self.api.show_stories(), self.api.job_stories(), self.api.top_stories(),
                                          self.api.ask_stories())
        stories = set(s) | set(j) | set(t) | set(a)
        [self.task_queue.add(item=QueueItem(self.get_by_id, item_id=itd), priority=3) for itd in stories]
        await self.task_queue.run()

    async def update(self):
        res = await self.api.updates()
        items = res['items']
        profiles = res['profiles']
        [self.task_queue.add(item=QueueItem(self.get_user, user_id=profile), priority=3) for profile in profiles]
        [self.task_queue.add(item=QueueItem(self.get_by_id, item_id=item), priority=3) for item in items]
        await self.task_queue.run()
