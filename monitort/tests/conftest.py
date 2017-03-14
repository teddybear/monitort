import pytest
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient


@pytest.fixture
def db(event_loop):
    return AsyncIOMotorClient(io_loop=event_loop).test_items


@pytest.fixture
def q(event_loop):
    return asyncio.Queue(loop=event_loop)


@pytest.fixture
def make_alive_item():
    return {
        'address': '127.0.0.1',
        'port': '8080',
        'name': 'Alive Item',
        'alive': True,
        'since': 12343567
    }


@pytest.fixture
def make_unavail_item():
    return {
        'address': '127.0.0.1',
        'port': '21',
        'name': 'Unavail Item',
        'alive': False,
        'since': 12343567
    }
