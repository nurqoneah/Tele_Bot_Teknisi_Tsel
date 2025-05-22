# import gspread
# from oauth2client.service_account import ServiceAccountCredentials

# def get_sheet(sheet_name):
#     scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
#     creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
#     client = gspread.authorize(creds)
#     return client.open(sheet_name).sheet1


import gspread
import json
import os
from dotenv import load_dotenv
load_dotenv()
from google.oauth2.service_account import Credentials

def get_sheet(sheet_name):
    scopes = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds_json = os.environ.get('GOOGLE_SHEETS_CREDENTIALS')
    creds_dict = json.loads(creds_json)

    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)

    client = gspread.authorize(creds)
    sheet = client.open(sheet_name).sheet1
    return sheet
