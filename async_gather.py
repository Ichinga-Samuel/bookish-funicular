import asyncio
import signal

from api import API
from dict_db import DictDB


class AsyncGather:
    main_task: asyncio.Task

    def __init__(self, db=None):
        self.api = API()
        self.db = db or DictDB() 
        self.visited = set() # keep track of visited items or users

    async def traverse_item(self, *, item):
        if item in self.visited:
            return

        res = await self.api.get_item(item_id=item)
        await self.db.save(data=res)
        self.visited.add(item)

        tasks = []
        if kids := res.get('kids'):
            tasks.extend(asyncio.create_task(self.traverse_item(item=item)) for item in kids)

        if (by := res.get('by')) and by not in self.visited:
            res = await self.api.get_user(user_id=by)
            self.visited.add(res['id'])
            await self.db.save_user(data=res)
            if submissions := res.get('submitted'):
                tasks.extend(asyncio.create_task(self.traverse_item(item=item)) for item in submissions)
        await asyncio.gather(*tasks)

    async def walk_back(self, amount: int = 500):
        first = await self.api.max_item()
        # for i in aiter(first, amount + first):


    async def traverse_api(self, timeout=60):
        s, j, n, t, a, b = await asyncio.gather(self.api.show_stories(), self.api.job_stories(), self.api.new_stories(),
                                                self.api.top_stories(), self.api.ask_stories(), self.api.best_stories())
        stories = set(s) | set(j) | set(t) | set(a) | set(b) | set(n)
        print(f"Total stories: {len(stories)}")
        start = asyncio.get_running_loop().time()
        try:
            signal.signal(signal.SIGINT, self.sigint_handler)
            tasks = [asyncio.create_task(self.traverse_item(item=story)) for story in stories]
            self.main_task = asyncio.gather(*tasks)
            await asyncio.wait_for(self.main_task, timeout)

        except TimeoutError as _:
            print('Timed out')

        except asyncio.CancelledError as _:
            print('Cancelled')

        finally:
            print(f"Made {len(self.visited)} API calls.\n"
                  f"Saved {len(self.db)} items in {asyncio.get_running_loop().time() - start:.2f} seconds.")
            print(self.db)

    def cancel_tasks(self):
        self.main_task.cancel() if not self.main_task.done() else None
        raise asyncio.CancelledError

    def sigint_handler(self, sig, frame):
        self.cancel_tasks()
