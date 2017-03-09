import sys
import logging
import urllib.parse
import asyncio
import bson
from bson.objectid import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient
import time

log = logging.getLogger(__name__)

q = asyncio.Queue()


@asyncio.coroutine
def produce_items(db):
    cursor = db.items.find({})
    while (yield from cursor.fetch_next):
        item = cursor.next_object()
        if item:
            yield from q.put(item)
    yield from q.join()
    for task in asyncio.Task.all_tasks():
        task.cancel()
    loop = asyncio.get_event_loop()
    loop.stop()
    log.info("Exit")


@asyncio.coroutine
def check_tcp_port(db):
    while True:
        item = yield from q.get()
        host, port = item['address'], item['port']
        try:
            # Wait for 3 seconds, then raise TimeoutError
            conn = asyncio.open_connection(host, port)
            reader, writer = yield from asyncio.wait_for(
                conn, timeout=3)
            log.info(
                "Connection is alive {} {}".format(host, port))
            writer.close()
            if not item.get("alive", False):
                db.items.update_one(
                    {"_id": item["_id"]},
                    {
                        "$set": {
                            "alive": True,
                            "since": int(time.time())
                        }
                    }
                )
            elif not item.get("since", None):
                db.items.update_one(
                    {"_id": item["_id"]},
                    {
                        "$set": {
                            "since": int(time.time())
                        }
                    }
                )

        except asyncio.TimeoutError:
            log.info("Timeout, skipping {} {}".format(host, port))
            db.items.update_one(
                {"_id": item["_id"]},
                {
                    "$set": {
                        "alive": False,
                        "since": int(time.time())
                    }
                }
            )
        except ConnectionRefusedError:
            log.info(
                "Connection refused, skipping {} {}"
                .format(host, port)
            )
            db.items.update_one(
                {"_id": item["_id"]},
                {
                    "$set": {
                        "alive": False,
                        "since": int(time.time())
                    }
                }
            )
        finally:
            q.task_done()


def main():
    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--db",
        help="Default: mongodb://127.0.0.1/monitort",
        type=str,
        default="mongodb://127.0.0.1/monitort"
    )
    parser.add_argument(
        "--forks",
        help="Default: 4",
        type=int,
        default=4
    )

    args = parser.parse_args()

    db = AsyncIOMotorClient(args.db).items

    loop = asyncio.get_event_loop()
    for frk in range(args.forks):
        asyncio.ensure_future(check_tcp_port(db))
    loop.run_until_complete(produce_items(db))


if __name__ == "__main__":
    log = logging.getLogger("")
    ch = logging.StreamHandler(sys.stdout)
    log.addHandler(ch)
    log.setLevel(logging.DEBUG)
    log.info("Start")
    main()
