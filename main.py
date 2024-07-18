from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from dotenv import load_dotenv
from os import environ
from redis import asyncio as aioredis
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

app = FastAPI()
load_dotenv()
mongo = MongoClient(
    f"mongodb+srv://{environ.get("MONGO_USERNAME")}:{environ.get("MONGO_PASSWORD")}@{environ.get("MONGO_ENDPOINT")}",
    server_api=ServerApi('1')
)

SERVICE_ACCOUNT_FILE = 'credentials.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('sheets', 'v4', credentials=credentials)

SPREADSHEET_ID = environ.get('SPREADSHEET_ID')
SHEET_NAMES = {
    'easy': 'Easy',
    'normal': 'Normal',
    'hard': 'Hard',
    'harder': 'Harder',
    'insane': 'Insane',
    'easydemon': 'Easy Demon',
    'mediumdemon': 'Medium Demon',
    'harddemon': 'Hard Demon',
    'insanedemon': 'Insane Demon',
    'extremededemon': 'Extreme Demon'
}


async def calculate_range(sheet_name, column):
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=f'{sheet_name}!{column}2:{column}').execute()
    values = result.get('values', [])
    return len(values) + 1


@cache()
async def get_cache():
    return 1


@app.get("/scrape")
async def scrape_google_sheet():
    values = []
    for name in SHEET_NAMES.values():
        last_row = await calculate_range(name, 'A')
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                    range=f'{name}!A2:F{last_row}').execute()
        values += result.get('values', [])

    if not values:
        return {"message": "No data found."}
    else:
        return {"data": values}


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    redis = aioredis.from_url(
        f"redis://{environ.get('REDIS_USERNAME')}:{environ.get('REDIS_PASSWORD')}@{environ.get('REDIS_ENDPOINT')}"
    )
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")
    yield
