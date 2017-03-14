import pytest

import asyncio
from monitort import checker
from conftest import make_alive_item, make_unavail_item


@pytest.mark.asyncio
@asyncio.coroutine
def test_producer(db, q, event_loop):
    yield from db.items.remove()
    for i in range(10):
        yield from db.items.insert_one(make_alive_item())
    cnt = yield from db.items.count()
    assert cnt == 10
    yield from checker.produce_items(db, q)
    while not q.empty():
        item = yield from q.get()
        item.pop("_id")
        assert item == make_alive_item()
    assert q.empty() is True
    for task in asyncio.Task.all_tasks():
        task.cancel()
