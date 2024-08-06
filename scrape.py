from os import environ
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from pymongo.mongo_client import MongoClient
import utils
from datetime import datetime
from dotenv import load_dotenv
import requests

load_dotenv()

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


async def get_sheet_id(sheet_name):
    sheet_metadata = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
    sheets = sheet_metadata.get('sheets', [])
    for sheet in sheets:
        if sheet.get('properties', {}).get('title') == sheet_name:
            return sheet.get('properties', {}).get('sheetId')
    return None


async def scrape_google_sheet(client: MongoClient):
    values = []
    for name in SHEET_NAMES.values():
        sheet_id = await get_sheet_id(name)
        last_row = await calculate_range(name, 'A')
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                    range=f'{name}!C2:F{last_row}').execute()
        data = list(result.get('values', []))
        if data:
            for i in range(len(data)):
                data[i].insert(3, utils.generate_cell_link(SPREADSHEET_ID, sheet_id, i + 2))
            values += data

    parsed_data = utils.parse_data(values)
    collection = client['secretways']['levels']
    updated_ids = set()

    for key, value in parsed_data.items():
        existing_record = collection.find_one({'_id': int(key)})
        if not existing_record:
            value['timestamp'] = datetime.now()
        collection.update_one({'_id': int(key)}, {'$set': value}, upsert=True)
        updated_ids.add(int(key))

    collection.delete_many({'_id': {'$nin': list(updated_ids)}})

    await scrape_robtop_api(client)


def get_all_ids(client: MongoClient) -> list[str]:
    collection = client['secretways']['levels']

    return [str(doc['_id']) for doc in collection.find({}, {'_id': 1})]


async def scrape_robtop_api(client: MongoClient):
    allIds = get_all_ids(client)
    url = "https://www.boomlings.com/database/getGJLevels21.php"
    headers = {
        "User-Agent": ""
    }
    data = {
        "onlyCompleted": 1,
        "secret": "Wmfd2893gb7",
    }
    levels, creators, songs = [], set(), set()
    while True:
        data["completedLevels"] = f"({','.join(allIds[:10])})",
        del allIds[:10]
        req = requests.post(url=url, data=data, headers=headers)
        reqParsed = utils.robtop_to_level_info(req.text)

        if len(reqParsed[0]) == 0: #shouldn't be necessary but just in case
            break

        levels += reqParsed[0]

        for creator in reqParsed[1]:
            creators.add(tuple(creator.items()))

        for song in reqParsed[2]:
            songs.add(tuple(song.items()))

        if len(allIds) == 0:
            break

    creators = [dict(creator) for creator in creators]
    songs = [dict(song) for song in songs]

    levelCollection = client['robtop']['levels']
    creatorCollection = client['robtop']['creators']
    songCollection = client['robtop']['songs']

    updated_ids = set()
    for level in levels:
        id = level.pop('1')
        levelCollection.update_one({'_id': int(id)}, {'$set': level}, upsert=True)
        updated_ids.add(int(id))

    levelCollection.delete_many({'_id': {'$nin': list(updated_ids)}})

    updated_ids.clear()
    for creator in creators:
        id = creator.pop('userID')
        creatorCollection.update_one({'_id': int(id)}, {'$set': creator}, upsert=True)
        updated_ids.add(int(id))

    creatorCollection.delete_many({'_id': {'$nin': list(updated_ids)}})

    updated_ids.clear()
    for song in songs:
        id = song.pop('1')
        songCollection.update_one({'_id': int(id)}, {'$set': song}, upsert=True)
        updated_ids.add(int(id))

    songCollection.delete_many({'_id': {'$nin': list(updated_ids)}})
