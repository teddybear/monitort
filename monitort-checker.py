import sys
import logging
import urllib.parse
import asyncio
import bson
from bson.objectid import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient


log = logging.getLogger(__name__)


@asyncio.coroutine
def make_connection(db, forks=4):
    clients = {}
    loop = asyncio.get_event_loop()
    cursor = db.items.find({})
    for frk in range(forks):
        task = asyncio.ensure_future(check_tcp_port(cursor))

        clients[task] = frk

        def client_done(task):
            del clients[task]
            log.info("Client Task Finished")
            if len(clients) == 0:
                log.info("clients is empty, stopping loop.")
                loop = asyncio.get_event_loop()
                loop.stop()

        log.info("New Client Task")
        task.add_done_callback(client_done)


@asyncio.coroutine
def check_tcp_port(cursor):
    while (yield from cursor.fetch_next):
        item = cursor.next_object()
        host, port = item['address'], item['port']
        try:
            # Wait for 3 seconds, then raise TimeoutError
            conn = asyncio.open_connection(host, port)
            reader, writer = yield from asyncio.wait_for(
                conn, timeout=3)
            log.info(
                "Connection is alive {} {}".format(host, port))
            writer.close()
        except asyncio.TimeoutError:
            log.info("Timeout, skipping {} {}".format(host, port))
            continue
        except ConnectionRefusedError:
            log.info(
                "Connection refused, skipping {} {}"
                .format(host, port)
            )
            continue


def run():
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
    main = asyncio.ensure_future(make_connection(db, args.forks))
    loop.run_forever()


if __name__ == "__main__":
    log = logging.getLogger("")
    ch = logging.StreamHandler(sys.stdout)
    log.addHandler(ch)
    log.setLevel(logging.DEBUG)
    log.info("Ololo?..")
    run()
