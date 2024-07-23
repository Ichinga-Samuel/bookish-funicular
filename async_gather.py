import asyncio
import signal 

from .api import API
from dict_db import DictDB

class AsyncGather():

    def __init__(self, db: None):
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
                tasks = [asyncio.create_task(self.traverse_item(item=item)) for item in res['kids']]
                self.tasks.extend(tasks)
                
            if 'by' in res:
                if item not in self.visited:
                    user = self.api.get_user(user_id=res['by'])
                    self.db.save(data=user)
                    self.visited.add(res['by'])

    async def traverse_api(self, timeout=60):
        signal.signal(signal.SIGINT, self.graceful_exit)
        signal.signal(signal.SIGTERM, self.graceful_exit)
        s, j, t, a = await asyncio.gather(self.api.show_stories(), self.api.job_stories(),
                                          self.api.top_stories(), self.api.ask_stories())
        stories = set(s) | set(j) | set(t) | set(a)
        tasks = [asyncio.create_task(self.traverse_item(item=story)) for story in stories]
        self.tasks.extend(tasks)
        try:
            async with asyncio.timeout(60):
                await asyncio.gather(*self.tasks)
        except (TimeoutError, KeyboardInterrupt) as exe:
            print('Timed out or Interrupted', exe)
        finally:
            print(f'{len(self.visited)} items visited')
            print(f'{len(self.connections)} opened')
        
    def graceful_exit(self, sig, frame):
        raise KeyboardInterrupt
