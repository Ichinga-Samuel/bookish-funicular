import http.client
import asyncio
import json


class API:
    URL = 'hacker-news.firebaseio.com'

    async def get(self, *, path: str):
        url = f'{self.URL}'
        path = f'/v0/{path}'
        conn = http.client.HTTPSConnection(url)
        await asyncio.to_thread(conn.request, 'GET', path)
        res = await asyncio.to_thread(conn.getresponse)
        res = json.loads(res.read().decode('utf-8'))
        conn.close()
        return res

    async def get_item(self, *, item_id):
        path = f'item/{item_id}.json'
        res = await self.get(path=path)
        return res

    async def get_user(self, *, user_id):
        path = f'user/{user_id}.json'
        res = await self.get(path=path)
        return res

    async def get_by_id(self, *, item_id):
        path = f'item/{item_id}.json'
        res = await self.get(path=path)
        return res

    async def max_item(self):
        path = 'maxitem.json'
        res = await self.get(path=path)
        return res

    async def top_stories(self):
        path = 'topstories.json'
        res = await self.get(path=path)
        return res

    async def ask_stories(self):
        path = 'askstories.json'
        res = await self.get(path=path)
        return res

    async def job_stories(self):
        path = 'jobstories.json'
        res = await self.get(path=path)
        return res

    async def show_stories(self):
        path = 'showstories.json'
        res = await self.get(path=path)
        return res

    async def updates(self):
        path = 'updates.json'
        res = await self.get(path=path)
        return res
