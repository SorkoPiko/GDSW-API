from os import environ
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from pymongo.mongo_client import MongoClient
import utils
from dotenv import load_dotenv

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
    for key, value in parsed_data.items():
        collection.update_one({'_id': key}, {'$set': value}, upsert=True)
