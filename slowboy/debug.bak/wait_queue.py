import asyncio
from functools import partial
import threading
from time import sleep

async def wait(t):
    try:
        await asyncio.sleep(t)
        print('wait({}) finished'.format(t))
    except asyncio.CancelledError:
        print('wait({}) cancelled'.format(t))


class MyThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self._tasks = []

    def stop(self):
        #while self.loop.is_running():
        #    for task in asyncio.Task.all_tasks(loop=self.loop):
        #        task.cancel()
        #    sleep(1)
        #    print(asyncio.Task.all_tasks(loop=self.loop))
        #    self.loop.stop()
        #    print(self.loop)

        #self.loop.close()
        self.loop.call_soon_threadsafe(self.loop.stop)
        for task in asyncio.Task.all_tasks(loop=self.loop):
            task.cancel()

    def run(self):
        self.loop = asyncio.new_event_loop()
        long_task = self.loop.create_task(wait(3600))
        short_task = self.loop.create_task(wait(4))

        self.loop.run_forever()
        #self.loop.run_until_complete(short_task)
        #long_task.cancel()
        #self.loop.run_until_complete(long_task)


thd = MyThread()
thd.start()

sleep(1)
thd.stop()

thd.join()
