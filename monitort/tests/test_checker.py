import pytest

import asyncio
from monitort import checker


@pytest.mark.asyncio
@asyncio.coroutine
def test_producer(db, q, event_loop):
    """ TODO: Fill data before consume"""
    yield from checker.produce_items(db, q)

    while not q.empty():
        item = yield from q.get()
        assert item is not None
    assert q.empty() is True
    for task in asyncio.Task.all_tasks():
        task.cancel()
