import pytest

import asyncio
import checker
from motor.motor_asyncio import AsyncIOMotorClient


@pytest.fixture
def db():
    return AsyncIOMotorClient().items


@pytest.mark.asyncio
def test_producer(db):
    """ TODO: Write working test... T_T"""
    q = checker.q
    asyncio.ensure_future(checker.produce_items(db))
    item = yield from q.get()
    print(type(item))
    assert type(item) is None
    q.task_done()
