import sys
import os
OWD = os.getcwd()
# print(OWD)
sys.path.append(OWD)
os.chdir(OWD)

from docs.conf import *

import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from time import sleep
from pandas import DataFrame

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

creds = None
data_frame = None

def login():
    global creds

    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "client_secrets.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

def get_values(s="Sheet1"):
    global creds, data_frame

    try:
        service = build("sheets", "v4", credentials=creds)

        # Call the Sheets API
        sheet = service.spreadsheets()
        result = (
            sheet.values()
            .get(spreadsheetId=SAMPLE_SPREADSHEET_ID, range=SAMPLE_RANGE_NAME)
            .execute()
        )
        values = result.get("values", [])

        if not values:
            print("No data found.")
            return

        print(values[0][0])
    except HttpError as err:
        print(err)
    else:
        data_frame = DataFrame(data=values)
        print(data_frame)

def update_values(s="Sheet1", v=None):
    global creds, data_frame

    if v is None:
        print("Value to update is None")
        return
    
    if isinstance(v, DataFrame):
        v = v.values.tolist()
    elif not isinstance(v, list):
        print("Value to update is not a list")
        return
    
    try:
        service = build("sheets", "v4", credentials=creds)

        body = {
            'values': v
        }

        # Call the Sheets API
        sheet = service.spreadsheets()
        result = (
            sheet.values()
            .update(spreadsheetId=SAMPLE_SPREADSHEET_ID, range=SAMPLE_RANGE_NAME, 
                    body=body, valueInputOption='RAW')
            .execute()
        )

        print(result.get('updatedRange', []))

        if result.get('updatedRange', []) == SAMPLE_RANGE_NAME:
            print("Value updated")
        else:
            print("Value not updated")
    except HttpError as err:
        print(err)

def update_data_frame(row=0, col=0, value=None):
    global data_frame

    if data_frame is None:
        print("Data frame is None")
        return

    if value is None:
        print("Value to update is None")
        return
    
    data_frame.at[row, col] = value

login()
if creds:
    get_values('Template')
    update_data_frame(0, 1, value='2024 24H SPA')
    update_values('Template', data_frame)