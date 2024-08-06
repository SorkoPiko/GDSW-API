import asyncio
import schedule
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from os import environ

from models import SecretWayResponse, SecretWay, Route, getGJLevels21, GJQueryType, GJDifficulty

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi_cache import FastAPICache
from fastapi_cache.backends.dynamodb import DynamoBackend
from fastapi_cache.decorator import cache
from fastapi.responses import HTMLResponse
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from urllib.parse import urlencode

from scrape import scrape_google_sheet
from utils import data_to_robtop

allowed_types = [GJQueryType.MOST_LIKED, GJQueryType.MOST_DOWNLOADED, GJQueryType.SEARCH]

diffConverted = {
    GJDifficulty.AUTO: -10,
    GJDifficulty.EASY: 10,
    GJDifficulty.NORMAL: 20,
    GJDifficulty.HARD: 30,
    GJDifficulty.HARDER: 40,
    GJDifficulty.INSANE: 50
}

load_dotenv()
mongo = MongoClient(
    f"mongodb+srv://{environ.get('MONGO_USERNAME')}:{environ.get('MONGO_PASSWORD')}@{environ.get('MONGO_ENDPOINT')}",
    server_api=ServerApi('1')
)


async def scheduler():
    #await scrape_google_sheet(mongo)
    schedule.every().day.at("00:00").do(lambda: asyncio.create_task(scrape_google_sheet(mongo)))
    while True:
        schedule.run_pending()
        await asyncio.sleep(1)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    FastAPICache.init(DynamoBackend(table_name=environ.get('DYNAMODB_TABLE'), region=environ.get('DYNAMODB_REGION')),
                      prefix="fastapi-cache")
    task = asyncio.create_task(scheduler())
    try:
        yield
    finally:
        task.cancel()


app = FastAPI(
    lifespan=lifespan,
    title="Geometry Dash Secret Ways API",
    description="An API to find secret ways in Geometry Dash levels",
    version="1.1.2",
    docs_url="/"
)


@cache()
async def get_cache():
    return 1


@app.get("/secretway/{level_id}")
@cache(expire=3600)
async def get_secretway(level_id: int) -> SecretWayResponse:
    collection = mongo['secretways']['levels']
    data: dict = collection.find_one({'_id': level_id})
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


@app.post("/robtop", response_class=HTMLResponse)
async def robtop(request: Request):
    raw_form = await request.form()
    form_dict: dict = {key: value for key, value in raw_form.items()}
    print(form_dict)
    if "completedLevels" in form_dict:
        form_dict["completedLevels"] = form_dict["completedLevels"][1:-1].split(",")
    if "type" in form_dict:
        form_dict["type"] = int(form_dict["type"])
    if "diff" in form_dict:
        if form_dict["diff"] == "-":
            form_dict["diff"] = 0
        else:
            form_dict["diff"] = int(form_dict["diff"])
    if "demonFilter" in form_dict:
        form_dict["demonFilter"] = int(form_dict["demonFilter"])
    if "len" in form_dict:
        if form_dict["len"] == "-":
            form_dict["len"] = None
        else:
            form_dict["len"] = int(form_dict["len"])
    if "followed" in form_dict:
        if form_dict["followed"] == "":
            form_dict["followed"] = []
    form = getGJLevels21(**form_dict)
    if form.gdw or form.gauntlet:
        return RedirectResponse(
            url=f"https://www.boomlings.com/database/getGJLevels21.php?{urlencode(form_dict)}",
            status_code=303
        )

    if form.type not in allowed_types:
        return "-1"

    levelCollection = mongo['robtop']['levels']
    returnString = "-1"
    query = []

    if form.epic + form.legendary + form.mythic == 1:
        if form.epic:
            query.append({'42': 1})
        elif form.legendary:
            query.append({'42': 2})
        elif form.mythic:
            query.append({'42': 3})

    if form.type == GJQueryType.SEARCH:
        query += {'2': {'$text': {'$search': form.query}}}
        levels = list(levelCollection.find({
            '$and': [
                {'2': {'$text': {'$search': form.query}}}
            ]
        }))

        returnString = data_to_robtop(mongo, levels, form.page)

    return returnString


@app.get("/docs", include_in_schema=False)
async def docs_redirect():
    return RedirectResponse("/")
