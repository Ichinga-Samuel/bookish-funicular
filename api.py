import http.client
import asyncio
import json
import signal

from base import User, Story, Comment, Poll, PollOption, BaseClass


class API:
    api = 'hacker-news.firebaseio.com'
    version = 'v0'
    url = f'{api}/{version}'
    payload = {}
    connections = []
    result = {
        'ids': set(),
        'data': {}
    }
    models: dict[str: BaseClass | User] = {'story': Story, 'comment': Comment, 'poll': Poll, 'pollopt': PollOption,
                                           'job': Story, 'user': User}
    
    async def get(self, *, path: str, payload: dict = None):
        conn = http.client.HTTPSConnection('hacker-news.firebaseio.com')
        self.connections.append(conn)
        payload = payload or self.payload
        path = f'/{self.version}/{path}'
        await asyncio.to_thread(conn.request, 'GET', path, payload)
        res = await asyncio.to_thread(conn.getresponse)
        return json.loads(res.read().decode('utf-8'))
    
    async def close(self):
        [await asyncio.to_thread(conn.close) for conn in self.connections]
        
    async def save(self, *, data: dict, key: str = ''):
        key = data.get('type', key)
        model = self.models[key]
        data = model(**data)
        await data.save(self.result['data'])
        self.result['ids'].add(data.id)
        
    async def get_by_id(self, *, item_id):
        if item_id in self.result['ids']:
            return
        path = f'item/{item_id}.json'
        res = await self.get(path=path)
        await self.save(data=res)
        tasks = []
        if 'kids' in res:
            tasks = [asyncio.create_task(self.get_by_id(item_id=item)) for item in res['kids']]
            
        if 'by' in res:
            task = asyncio.create_task(self.get_user(user_id=res['by']))
            tasks.append(task)
            
        await asyncio.gather(*tasks, return_exceptions=True) if tasks else ...
        return res
    
    async def get_user(self, *, user_id):
        if user_id in self.result['ids']:
            return
        
        path = f'user/{user_id}.json'
        res = await self.get(path=path)
        await self.save(data=res, key='user')
    
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
    
    async def stories(self):
        signal.signal(signal.SIGINT, self.graceful_exit)
        signal.signal(signal.SIGTERM, self.graceful_exit)
        s, j, t, a = await asyncio.gather(self.show_stories(), self.job_stories(), self.top_stories(), self.ask_stories())
        stories = set(s) | set(j) | set(t) | set(a)
        aws = [asyncio.create_task(self.get_by_id(item_id=itd)) for itd in stories]
        try:
            async with asyncio.timeout(60):
                await asyncio.gather(*aws)
        except TimeoutError:
            print('Timed Out')
        finally:
            print(len(self.result['data']))
            print(len(self.connections))
    
    def graceful_exit(self, sig, frame):
        print(len(self.result['data']))
        print(len(self.connections))
        exit()


asyncio.run(API().stories())
