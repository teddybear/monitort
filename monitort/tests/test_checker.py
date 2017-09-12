import pytest

import asyncio
from monitort import checker
from conftest import make_alive_item, make_unavail_item


@pytest.mark.asyncio
@asyncio.coroutine
def test_producer(db, q):
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


@pytest.mark.asyncio
@asyncio.coroutine
def test_check_tcp_port(db, q, event_loop):
    yield from db.items.remove()
    for i in range(10):
        yield from db.items.insert_one(make_alive_item())
    cnt = yield from db.items.count()
    assert cnt == 10


@pytest.mark.asyncio
@asyncio.coroutine
def test_update_item(db):
    yield from db.items.remove()
    yield from db.items.insert_one(make_alive_item())
    yield from db.items.insert_one(make_unavail_item())
    cnt = yield from db.items.count()
    assert cnt == 2
    alive_item = yield from db.items.find_one(
        {"name": make_alive_item()["name"]})

    yield from checker.update_item(db, alive_item, alive=True)

    alive_item = yield from db.items.find_one(
        {"name": make_alive_item()["name"]})

    assert alive_item['since'] == make_alive_item()['since']
    assert alive_item['alive'] is True

    unav_item = yield from db.items.find_one(
        {"name": make_unavail_item()["name"]})

    yield from checker.update_item(db, unav_item, alive=True)

    unav_item = yield from db.items.find_one(
        {"name": make_unavail_item()["name"]})

    assert unav_item['since'] != make_unavail_item()['since']
    assert unav_item['alive'] is True
