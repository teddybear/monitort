import asyncio
import urllib.parse
import bson
from bson.objectid import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient


@asyncio.coroutine
def check_tcp_port(db, url, port):
        # TODO: ConnectionError handle and timeout
        # TODO: Forking
        cursor = db.items.find({})
        items = []
        while (yield from cursor.fetch_next):
            try:
                item = cursor.next_object()
                if item.get('address'):
                    url = urllib.parse.urlsplit(item['address'])
                    connect = asyncio.open_connection(
                        url.hostname, port=item['port'])
                    reader, writer = yield from connect
                    query = ('HEAD {path} HTTP/1.0\r\n'
                             'Host: {hostname}\r\n'
                             '\r\n').format(
                             path=url.path or '/', hostname=url.hostname)
                    writer.write(query.encode('latin-1'))
                    while True:
                        line = yield from reader.readline()
                        if not line:
                            break
                        line = line.decode('latin1').rstrip()
                        if line:
                            print('HTTP header> %s' % line)
                    writer.close()
                    print("Alive")
            except ConnectionRefusedError:
                print ("!")


def main(args=None):
    import sys
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

    args = parser.parse_args()
    db = AsyncIOMotorClient(args.db).items

    url = "http://127.0.0.1"
    port = "8080"
    loop = asyncio.get_event_loop()
    task = asyncio.ensure_future(check_tcp_port(db, url, port))
    loop.run_until_complete(task)
    loop.close()

if __name__ == "__main__":
    main()
