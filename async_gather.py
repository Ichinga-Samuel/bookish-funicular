import asyncio
import signal

from api import API
from dict_db import DictDB


class AsyncGather:
    def __init__(self, db=None):
        self.api = API()
        self.db = db or DictDB() 
        self.visited = set()  # keep track of visited items or users
        self.tasks: list[asyncio.Task] = []
        signal.signal(signal.SIGINT, self.sigint_handler)

    async def traverse_item(self, *, item):
        if item in self.visited:
            return

        print(f"Getting item {item}")
        res = await self.api.get_item(item_id=item)
        await self.db.save(data=res)
        self.visited.add(item)

        tasks = []
        user_stories = []

        # saving user data
        if (by := res.get('by')) and by not in self.visited:
            res = await self.api.get_user(user_id=by)
            self.visited.add(res['id'])
            await self.db.save_user(data=res)
            if submissions := res.get('submitted'):
                user_stories.extend(asyncio.create_task(self.traverse_item(item=item)) for item in submissions)

        # saving kids data
        if kids := res.get('kids'):
            tasks.extend(asyncio.create_task(self.traverse_item(item=item)) for item in kids)

        # saving parent data
        if (parent := res.get('parent')) and parent not in self.visited:
            tasks.append(asyncio.create_task(self.traverse_item(item=parent)))

        # include user stories in the tasks
        tasks.extend(user_stories)

        await asyncio.gather(*tasks)

    async def walk_back(self, *, amount: int = 1000, timeout: int = 60):
        largest = await self.api.max_item()
        print(f"Walking back from item {largest} to {largest - amount}")
        loop = asyncio.get_running_loop()
        start = loop.time()
        try:
            self.tasks = [asyncio.create_task(self.traverse_item(item=item)) for item in
                          range(largest, largest - amount, -1)]
            for task in asyncio.as_completed(self.tasks, timeout=timeout):
                try:
                    await task
                except asyncio.CancelledError as _:
                    ...
            else:
                print('Timed out or completed')

        except Exception as exe:
            print(f"Error: {exe}")

        finally:
            print(f"Made {len(self.visited)} API calls in"
                  f" {loop.time() - start:.2f} seconds")
            print(self.db)

    async def traverse_api(self, timeout=60):
        s, j, n, t, a, b = await asyncio.gather(self.api.show_stories(), self.api.job_stories(), self.api.new_stories(),
                                                self.api.top_stories(), self.api.ask_stories(), self.api.best_stories())
        stories = set(s) | set(j) | set(t) | set(a) | set(b) | set(n)
        print(f"Total stories: {len(stories)}")
        loop = asyncio.get_running_loop()
        start = loop.time()
        try:
            self.tasks = [asyncio.create_task(self.traverse_item(item=story)) for story in stories]
            await asyncio.wait_for(asyncio.gather(*self.tasks), timeout)

        except TimeoutError as _:
            print('Timed out')

        except asyncio.CancelledError as exe:
            print('Tasks Cancelled', exe)

        finally:
            print(f"Made {len(self.visited)} API calls and "
                  f"saved {len(self.db)} items in {loop.time() - start:.2f} seconds.")
            print(self.db)

    def sigint_handler(self, sig, frame):
        for task in self.tasks:
            task.cancel() if not task.done() else ...
