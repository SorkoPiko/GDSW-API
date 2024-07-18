from fastapi import FastAPI
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from dotenv import load_dotenv
from os import environ

app = FastAPI()
load_dotenv()

SERVICE_ACCOUNT_FILE = 'path/to/your-service-account-file.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('sheets', 'v4', credentials=credentials)

SPREADSHEET_ID = environ.get('SPREADSHEET_ID')
RANGE_NAME = 'Easy!A1:D5'


@app.get("/scrape")
async def scrape_google_sheet():
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                range=RANGE_NAME).execute()
    values = result.get('values', [])

    if not values:
        return {"message": "No data found."}
    else:
        # Process and return the data as needed
        return {"data": values}