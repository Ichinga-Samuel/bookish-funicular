import asyncio

from async_gather import AsyncGather
from async_queue import AsyncQueue


async def main(mode='queue'):
    if mode == 'gather':
        # async gather
        ag = AsyncGather()
        await ag.traverse_api()
    elif mode == 'queue':
        # async queue
        aq = AsyncQueue()
        await aq.traverse_api()
    else:
        print('Invalid mode')


if __name__ == '__main__':
    asyncio.run(main())
