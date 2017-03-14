import sys
import logging
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import time

log = logging.getLogger(__name__)


@asyncio.coroutine
def produce_items(db, q):
    cursor = db.items.find({})
    while (yield from cursor.fetch_next):
        item = cursor.next_object()
        if item:
            yield from q.put(item)


def update_item(db, item, alive=True):
    if alive:
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
    else:
        db.items.update_one(
            {"_id": item["_id"]},
            {
                "$set": {
                    "alive": False,
                    "since": int(time.time())
                }
            }
        )


@asyncio.coroutine
def check_tcp_port(db, q):
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
            update_item(db, item, True)
        except asyncio.TimeoutError:
            log.info("Timeout, skipping {} {}".format(host, port))
            update_item(db, item, False)
        except ConnectionRefusedError:
            log.info(
                "Connection refused, skipping {} {}"
                .format(host, port)
            )
            update_item(db, item, False)
        finally:
            q.task_done()


@asyncio.coroutine
def runner(db, forks):
    q = asyncio.Queue()
    tasks = []
    for frk in range(forks):
        tasks.append(asyncio.ensure_future(check_tcp_port(db, q)))
    yield from produce_items(db, q)
    yield from q.join()
    # for task in asyncio.Task.all_tasks():
    for task in tasks:
        task.cancel()
    log.debug("Exit")


def main(args=None):
    import argparse
    if args is None:
        args = sys.argv[1:]
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

    log = logging.getLogger("")
    ch = logging.StreamHandler(sys.stdout)
    log.addHandler(ch)
    log.setLevel(logging.DEBUG)
    log.debug("Start")

    args = parser.parse_args(args)

    loop = asyncio.get_event_loop()

    db = AsyncIOMotorClient(args.db).items

    q = asyncio.Queue()
    tasks = []

    # loop.run_until_complete(produce_items(db, q))
    loop.run_until_complete(runner(db, args.forks))


if __name__ == "__main__":
    main()
