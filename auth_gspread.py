import gspread
from oauth2client.service_account import ServiceAccountCredentials

def get_sheet(sheet_name):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)
    return client.open(sheet_name).sheet1


# import gspread
# import json
# import os
# from google.oauth2.service_account import Credentials

# def get_sheet(sheet_name):
#     credentials_json_str = os.environ.get('GSHEET_CREDENTIALS')
#     if not credentials_json_str:
#         raise EnvironmentError("Environment variable GSHEET_CREDENTIALS not found.")

#     credentials_info = json.loads(credentials_json_str)
#     creds = Credentials.from_service_account_info(credentials_info)
#     gc = gspread.authorize(creds)
#     return gc.open(sheet_name).sheet1

# if __name__ == '__main__':
#     # Contoh penggunaan (pastikan GSHEET_CREDENTIALS sudah di-set)
#     sheet_name = "Nama Spreadsheet Anda"
#     try:
#         sheet = get_sheet(sheet_name)
#         print(f"Berhasil terhubung ke spreadsheet '{sheet_name}'.")
#         # Lakukan operasi lain dengan sheet di sini
#     except EnvironmentError as e:
#         print(f"Error: {e}")
#         print("Pastikan Anda telah mengatur environment variable GSHEET_CREDENTIALS.")
#     except Exception as e:
#         print(f"Terjadi kesalahan lain: {e}")