import asyncio
import schedule
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from os import environ

from models import SecretWayResponse, SecretWay, Route

from dotenv import load_dotenv
from fastapi import FastAPI, Form, Request
from fastapi.responses import RedirectResponse
from fastapi_cache import FastAPICache
from fastapi_cache.backends.dynamodb import DynamoBackend
from fastapi_cache.decorator import cache
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

from scrape import scrape_google_sheet

load_dotenv()
mongo = MongoClient(
    f"mongodb+srv://{environ.get('MONGO_USERNAME')}:{environ.get('MONGO_PASSWORD')}@{environ.get('MONGO_ENDPOINT')}",
    server_api=ServerApi('1')
)


async def scheduler():
    await scrape_google_sheet(mongo)
    schedule.every().day.at("00:00").do(lambda: asyncio.create_task(scrape_google_sheet(mongo)))
    while True:
        schedule.run_pending()
        await asyncio.sleep(1)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    FastAPICache.init(DynamoBackend(table_name=environ.get('DYNAMODB_TABLE'), region=environ.get('DYNAMODB_REGION')), prefix="fastapi-cache")
    task = asyncio.create_task(scheduler())
    try:
        yield
    finally:
        task.cancel()


app = FastAPI(
    lifespan=lifespan,
    title="Geometry Dash Secret Ways API",
    description="An API to find secret ways in Geometry Dash levels",
    version="1.1.0",
    docs_url="/"
)


@cache()
async def get_cache():
    return 1


@app.get("/secretway/{level_id}")
@cache(expire=3600)
async def get_secretway(level_id: int) -> SecretWayResponse:
    collection = mongo['secretways']['levels']
    data = collection.find_one({'_id': level_id})
    if data is None:
        return SecretWayResponse()
    data.pop("_id")
    routes = data.pop("routes")
    new_routes = []
    for route in routes:
        new_routes.append(Route(**route))
    data["routes"] = new_routes
    if data["yt"] is None:
        data.pop("yt")
    return SecretWayResponse(found=True, data=SecretWay(**data))


@app.get("/docs", include_in_schema=False)
async def docs_redirect():
    return RedirectResponse("/")


@app.post("/robtop")
async def robtop(request: Request):
    pass