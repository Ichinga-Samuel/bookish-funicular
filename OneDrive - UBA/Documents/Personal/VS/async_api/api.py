import http.client
import asyncio
import json




class API:
    URL = 'hacker-news.firebaseio.com/v0'

    def __init__(self):
        self.connections = []

    async def get(self, *, path: str, payload: dict = None):
        url = f'{self.URL}/{path}'
        conn = http.client.HTTPSConnection(url)
        self.connections.append(conn)
        payload = payload or self.payload
        await asyncio.to_thread(conn.request, 'GET', path, payload)
        res = await asyncio.to_thread(conn.getresponse)
        return json.loads(res.read().decode('utf-8'))
    
    async def close(self):
        [await asyncio.to_thread(conn.close) for conn in self.connections]
        
    async def get_item(self, *, item_id):
        path = f'item/{item_id}.json'
        res = await self.get(path=path)
        return res
    
    async def get_user(self, *, user_id):
        path = f'user/{user_id}.json'
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
    
