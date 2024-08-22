import asyncio

from api import API
from dict_db import DictDB


class AsyncGather:
    def __init__(self, db=None):
        self.api = API()
        self.db = db or DictDB()
        self.visited = set()

    async def traverse_item(self, *, item):
        if item in self.visited:
            return

        res = await self.api.get_item(item_id=item)
        await self.db.save(data=res)
        self.visited.add(item)
        print(f"{res.get('title', res.get('id'))}")

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

    async def traverse_api(self):
        s, j, n, t, a, b = await asyncio.gather(self.api.show_stories(), self.api.job_stories(), self.api.new_stories(),
                                                self.api.top_stories(), self.api.ask_stories(), self.api.best_stories())
        stories = set(s) | set(j) | set(t) | set(a) | set(b) | set(n)
        print(f"Total stories: {len(stories)}")
        start = asyncio.get_running_loop().time()

        try:
            tasks = [asyncio.create_task(self.traverse_item(item=story)) for story in stories]
            await asyncio.gather(*tasks)

        except Exception as _:
            print('Cancelled')

        finally:
            print(f"Made {len(self.visited)} API calls. Saved {len(self.db)} items"
                  f" in {asyncio.get_running_loop().time() - start} seconds")
            print(self.db)


async def main():
    await AsyncGather().traverse_api()

asyncio.run(main())
