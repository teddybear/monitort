import json
import asyncio
from aiohttp import web
import bson
from bson.objectid import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient


# def get_db():
#     db = AsyncIOMotorClient().items
#     return db


def validate_item_create(doc):
    return (
        "name" in doc and
        "address" in doc and
        "port" in doc
    )


def validate_item_update(doc):
    return (
        "name" in doc or
        "address" in doc or
        "port" in doc
    )


def validate_id(request):
    try:
        return ObjectId(request.match_info.get('id', None))
    except bson.errors.InvalidId:
        return None


@asyncio.coroutine
def endpoints(request):
    try:
        db = request.app['db']
        if request.method == "POST":
            doc = yield from request.json()
            if validate_item_create(doc):
                items = yield from db.items.insert_one(doc)
                print(items, dir(items))
                doc.update({"id": str(doc.pop("_id"))})
                return web.Response(text=json.dumps(doc))
            return web.Response(
                text=json.dumps({"error": "validation error"}),
                status=404
            )
        cursor = db.items.find({})
        items = []
        while (yield from cursor.fetch_next):
            item = cursor.next_object()
            item.update(
                {"id": str(item.pop("_id"))}
            )
            items.append(item)
        return web.Response(text=json.dumps({'items': items}))
    except Exception as e:
        return web.Response(
            text=json.dumps(
                {"error": "Internal Server Error: {}".format(e.message)}
            ),
            status=500
        )


@asyncio.coroutine
def get_item(request):
    try:
        item_id = validate_id(request)
        if not item_id:
            return web.Response(text='{"error": "invalid id"}', status=404)
        db = request.app['db']

        item = yield from db.items.find_one({"_id": item_id})
        if item:
            item.update(
                {"id": str(item.pop("_id"))}
            )
            return web.Response(text=json.dumps(item))
        else:
            return web.Response(
                text=json.dumps({
                    "error": "item with id={} is not found"
                    .format(str(item_id))
                }),
                status=404
            )
    except Exception as e:
        return web.Response(
            text=json.dumps(
                {"error": "Internal Server Error: {}".format(e.message)}
            ),
            status=500
        )


@asyncio.coroutine
def update_item(request):
    try:
        item_id = validate_id(request)
        if not item_id:
            return web.Response(text='{"error": "invalid id"}', status=404)
        db = request.app['db']
        item = yield from db.items.find_one({"_id": item_id})
        if item:
            doc = yield from request.json()
            if validate_item_update(doc):
                upd = yield from db.items.update_one(
                    {"_id": item_id}, {'$set': doc}
                )
                item = yield from db.items.find_one({"_id": item_id})
                item.update(
                    {"id": str(item.pop("_id"))}
                )
                return web.Response(text=json.dumps(item))
        else:
            return web.Response(
                text=json.dumps({
                    "error": "item with id={} is not found"
                    .format(str(item_id))
                }),
                status=404
            )
    except Exception as e:
        return web.Response(
            text=json.dumps(
                {"error": "Internal Server Error: {}".format(e.message)}
            ),
            status=500
        )


@asyncio.coroutine
def del_item(request):
    try:
        item_id = validate_id(request)
        if not item_id:
            return web.Response(text='{"error": "invalid id"}', status=404)
        db = request.app['db']
        item = yield from db.items.find_one({"_id": item_id})
        if item:
            upd = yield from db.items.delete_one({"_id": item_id})
            item.update(
                {"id": str(item.pop("_id"))}
            )
            return web.Response(text=json.dumps(item))
        else:
            return web.Response(
                text=json.dumps({
                    "error": "item with id={} is not found"
                    .format(str(item_id))
                }),
                status=404
            )
    except Exception as e:
        return web.Response(
            text=json.dumps(
                {"error": "Internal Server Error: {}".format(e.message)}
            ),
            status=500
        )

app = web.Application()

app.router.add_get('/endpoints', endpoints)
app.router.add_post('/endpoints/', endpoints)
app.router.add_get('/endpoints/{id}', get_item)
app.router.add_put('/endpoints/{id}', update_item)
app.router.add_delete('/endpoints/{id}', del_item)


def main(args=None):
    import sys
    import argparse
    if args is None:
        args = sys.argv[1:]
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--address",
        help="Default: 127.0.0.1",
        type=str,
        default="127.0.0.1"
    )
    parser.add_argument(
        "--port",
        help="Default: 8080",
        type=int,
        default=8080
    )
    parser.add_argument(
        "--db",
        help="Default: mongodb://127.0.0.1/monitort",
        type=str,
        default="mongodb://127.0.0.1/monitort"
    )

    args = parser.parse_args()
    db = AsyncIOMotorClient(args.db).items
    app['db'] = db
    web.run_app(app, host=args.address, port=args.port)


if __name__ == "__main__":
    main()
