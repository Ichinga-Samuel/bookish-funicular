import asyncio
import signal 

from api import API
from dict_db import DictDB


class AsyncGather:
    def __init__(self, db=None):
        self.api = API()
        self.db = db or DictDB()
        self.visited = set()
        self.tasks = []

    async def traverse_item(self, *, item):
        # get item by id and follow up on kids and user
        if item in self.visited:
            return
        res = await self.api.get_item(item_id=item)
        self.db.save(data=res)
        self.visited.add(item)

        if 'kids' in res:
            async with asyncio.TaskGroup() as tg:
                [tg.create_task(self.traverse_item(item=item)) for item in res['kids']]

        if 'by' in res:
            if item not in self.visited:
                user = self.api.get_user(user_id=res['by'])
                self.db.save(data=user)
                self.visited.add(res['by'])

    async def traverse_api(self, timeout=60):
        s, j, t, a = await asyncio.gather(self.api.show_stories(), self.api.job_stories(),
                                          self.api.top_stories(), self.api.ask_stories())
        stories = set(s) | set(j) | set(t) | set(a)
        tasks = [asyncio.create_task(self.traverse_item(item=story)) for story in stories]
        self.tasks.extend(tasks)
        try:
            signal.signal(signal.SIGINT, self.sigterm_handler)
            await asyncio.wait_for(asyncio.gather(*self.tasks), timeout=timeout)
        except (TimeoutError, asyncio.CancelledError) as exe:
            print('Timed out or Interrupted', exe)
        finally:
            print(f'{len(self.db)} items visited')
        
    def sigterm_handler(self, sig, frame):
        tasks = asyncio.all_tasks()
        [task.cancel() for task in self.tasks]
