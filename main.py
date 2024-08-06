import asyncio
import schedule
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from os import environ

from models import SecretWayResponse, SecretWay, Route, getGJLevels21, GJQueryType, GJDifficulty, GJDemonFilter

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
    GJDifficulty.EASY: 10,
    GJDifficulty.NORMAL: 20,
    GJDifficulty.HARD: 30,
    GJDifficulty.HARDER: 40,
    GJDifficulty.INSANE: 50
}

demonDiffConverted = {
    GJDemonFilter.EASY: 3,
    GJDemonFilter.MEDIUM: 4,
    GJDemonFilter.HARD: 0,
    GJDemonFilter.INSANE: 5,
    GJDemonFilter.EXTREME: 6
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
    version="2.0.1",
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
    if "completedLevels" in form_dict:
        try:
            form_dict["completedLevels"] = [int(x) for x in form_dict["completedLevels"][1:-1].split(",")]
        except:
            form_dict["completedLevels"] = []
    if "type" in form_dict:
        form_dict["type"] = int(form_dict["type"])
    if "diff" in form_dict:
        if form_dict["diff"] == "-":
            form_dict["diff"] = None
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

    if form.type == GJQueryType.SEARCH and form.query is None:
        form.type = GJQueryType.MOST_LIKED

    if form.type == GJQueryType.SEARCH:
        try:
            lvlId = int(form.str)
        except:
            lvlId = None
        if lvlId is not None:
            levels = list(levelCollection.find({'_id': lvlId}))

            return data_to_robtop(mongo, levels, form.page)

    if form.diff:
        if form.diff == GJDifficulty.DEMON:
            query.append({'17': '1'})
            if form.demonFilter:
                query.append({'43': str(demonDiffConverted[form.demonFilter])})
        elif form.diff == GJDifficulty.AUTO:
            query.append({'25': '1'})
        elif form.diff == GJDifficulty.NA:
            query.append({'8': '0'})
        else:
            query.append({'9': str(diffConverted[form.diff])})

    if sum([form.epic, form.legendary, form.mythic]) <= 1:
        if form.epic:
            query.append({'42': '1'})
        elif form.legendary:
            query.append({'42': '2'})
        elif form.mythic:
            query.append({'42': '3'})
        if form.featured:
            query.append({'19': {'$ne': '0'}})

    if form.original:
        query.append({'30': 0})

    if form.completedLevels:
        if form.uncompleted:
            query.append({'_id': {'$nin': form.completedLevels}})
        if form.onlyCompleted:
            query.append({'_id': {'$in': form.completedLevels}})

    if form.coins:
        query.append({'38': '1'})

    if form.twoPlayer:
        query.append({'31': '1'})

    if form.noStar:
        query.append({'18': '0'})

    if form.star:
        query.append({'18': {'$ne': '0'}})

    if form.song:
        if form.customSong:
            query.append({'35': str(form.song)})
        else:
            query.append({'12': str(form.song)})

    if form.length:
        query.append({'15': str(form.length.value)})

    if form.type == GJQueryType.SEARCH:
        query.append({'$text': {'$search': form.query}})
        try:
            levels = list(levelCollection.find({
                '$and': query
            }))
        except:
            print(query)
            return "-1"

        returnString = data_to_robtop(mongo, levels, form.page)

    elif form.type == GJQueryType.MOST_DOWNLOADED:
        try:
            if not query:
                levels = list(levelCollection.find())
            else:
                levels = list(levelCollection.find({
                    '$and': query
                }))
        except:
            print(query)
            return "-1"

        levels = sorted(levels, key=lambda x: int(x['10']), reverse=True)

        returnString = data_to_robtop(mongo, levels, form.page)

    elif form.type == GJQueryType.MOST_LIKED:
        try:
            if not query:
                levels = list(levelCollection.find())
            else:
                levels = list(levelCollection.find({
                    '$and': query
                }))
        except:
            print(query)
            return "-1"

        levels = sorted(levels, key=lambda x: int(x['14']), reverse=True)

        returnString = data_to_robtop(mongo, levels, form.page)

    return returnString


@app.get("/docs", include_in_schema=False)
async def docs_redirect():
    return RedirectResponse("/")
