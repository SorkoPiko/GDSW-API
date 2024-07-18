from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache
from dotenv import load_dotenv
from os import environ
from redis import asyncio as aioredis
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from scrape import scrape_google_sheet
import asyncio

load_dotenv()
mongo = MongoClient(
    f"mongodb+srv://{environ.get("MONGO_USERNAME")}:{environ.get("MONGO_PASSWORD")}@{environ.get("MONGO_ENDPOINT")}",
    server_api=ServerApi('1')
)


async def scrapeloop():
    while True:
        await scrape_google_sheet(mongo)
        await asyncio.sleep(86400)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    redis = aioredis.from_url(
        f"redis://{environ.get('REDIS_USERNAME')}:{environ.get('REDIS_PASSWORD')}@{environ.get('REDIS_ENDPOINT')}"
    )
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")
    task = asyncio.create_task(scrapeloop())
    try:
        yield
    finally:
        task.cancel()
        await redis.close()


app = FastAPI(lifespan=lifespan)


@cache()
async def get_cache():
    return 1


@app.get("/secretway/{level_id}")
@cache(expire=3600)
async def get_secretway(level_id: str):
    collection = mongo['secretways']['levels']
    data = collection.find_one({'_id': level_id})
    if data == None:
        return {"error": "No secret way found"}
    return data
