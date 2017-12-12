import asyncio
import threading


class Tasks:
    loop = asyncio.new_event_loop()

    @classmethod
    def _run(cls):
        try:
            cls.loop.run_forever()
        finally:
            cls.loop.close()

    @classmethod
    def do(cls, func, *args, **kwargs):
        cls.loop.call_soon(lambda: func(*args, **kwargs))
        cls.loop._write_to_self()

    @classmethod
    def later(cls, func, *args, after=None, **kwargs):
        cls.loop.call_later(after, lambda: func(*args, **kwargs))
        cls.loop._write_to_self()

    @classmethod
    def periodic(cls, func, *args, interval=None, **kwargs):
        @asyncio.coroutine
        def f():
            while True:
                yield from asyncio.sleep(interval)
                func(*args, **kwargs)

        cls.loop.create_task(f())
        cls.loop._write_to_self()


threading.Thread(name="tasks", target=Tasks._run, daemon=True).start()
