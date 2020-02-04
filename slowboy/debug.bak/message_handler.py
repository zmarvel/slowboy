import abc
import asyncio
from typing import Callable

from slowboy.debug.messages import *

class MessageHandler(metaclass=abc.ABCMeta):
    def __init__(self, loop: asyncio.BaseEventLoop, queue: asyncio.Queue):
        self.loop = loop
        self.queue = queue
        self._task = None
        self._shutdown_cbs = []

    def register_shutdown_callback(self, cb: Callable[[], None]):
        """Register callback to be called when the task is cancelled.
        """
        self._shutdown_cbs.append(cb)

    @abc.abstractmethod
    def handle_message(self, message: Message):
        """Abstract method called by handle_messages task when a new message
        arrives in the queue.
        """
        raise NotImplementedError()

    @property
    def task(self):
        return self._task

    def start(self):
        """Returns `handle_messages` wrapped in a task.
        """
        task = self.loop.create_task(self.handle_messages())
        self._task = task
        return task

    def stop(self):
        """Cancel the message-handling task; when the task is cancelled, any
        shutdown callbacks will be called.
        """
        self._task.cancel()
        for cb in self._shutdown_cbs:
            cb()

    async def handle_messages(self):
        """Coroutine that waits on messages in the queue and calls
        handle_message.
        """
        try:
            print('Started {}'.format(self))
            while True:
                msg = await self.queue.get()
                print('handle_messages: dequeued {}'.format(msg))
                self.handle_message(msg)
        except asyncio.CancelledError:
            print('Shutting down {}'.format(self))
