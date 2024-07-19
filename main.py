import asyncio
import schedule
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from os import environ

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache
from mangum import Mangum
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from redis import asyncio as aioredis

from scrape import scrape_google_sheet

load_dotenv()
mongo = MongoClient(
    f"mongodb+srv://{environ.get('MONGO_USERNAME')}:{environ.get('MONGO_PASSWORD')}@{environ.get('MONGO_ENDPOINT')}",
    server_api=ServerApi('1')
)

async def scheduler():
    schedule.every().day.at("00:00").do(lambda: asyncio.create_task(scrape_google_sheet(mongo)))
    while True:
        schedule.run_pending()
        await asyncio.sleep(1)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    redis = aioredis.from_url(
        f"redis://{environ.get('REDIS_USERNAME')}:{environ.get('REDIS_PASSWORD')}@{environ.get('REDIS_ENDPOINT')}"
    )
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")
    task = asyncio.create_task(scheduler())
    try:
        yield
    finally:
        task.cancel()
        await redis.close()


app = FastAPI(lifespan=lifespan)
handler = Mangum(app)

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
