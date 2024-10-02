import sys
import os
OWD = os.getcwd()
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
from tkinter import messagebox

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

def get_values(s="Template"):
    global creds, data_frame

    try:
        service = build("sheets", "v4", credentials=creds)

        # Call the Sheets API
        sheet = service.spreadsheets()
        result = (
            sheet.values()
            .get(spreadsheetId=SAMPLE_SPREADSHEET_ID, range=f"{s}{SAMPLE_RANGE_NAME}")
            .execute()
        )
        values = result.get("values", [])

        if not values:
            messagebox.showerror("Error", "No data found.")
            return

        # print(values[0][0])
    except HttpError as err:
        messagebox.showerror("Error", err)
    else:
        data_frame = DataFrame(data=values)
        # print(data_frame)

def update_values(s="Template", v=None):
    global creds, data_frame

    if v is None:
        messagebox.showerror("Error", "Value to update is None")
        return
    
    if isinstance(v, DataFrame):
        v = v.values.tolist()
    elif not isinstance(v, list):
        messagebox.showerror("Error", "Value to update is not a list")
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
            .update(spreadsheetId=SAMPLE_SPREADSHEET_ID, range=f"{s}{SAMPLE_RANGE_NAME}", 
                    body=body, valueInputOption='RAW')
            .execute()
        )

        print(result.get('updatedRange', []))

        if str(result.get('updatedRange', [])).split('!')[0] == s.strip("\'"):
            print("Value updated")
        else:
            print("Value not updated")
    except HttpError as err:
        messagebox.showerror("Error", err)

def add_event(name=''):
    global creds, data_frame

    if name == '':
        messagebox.showerror("Error", "Event name is empty")
        return
    
    if creds is None:
        messagebox.showerror("Error", "Credentials is None")
        return
    
    get_values('Template')
    
    try:
        service = build("sheets", "v4", credentials=creds)

        body = {
            "requests":{
                "addSheet":{
                    "properties":{
                        "title":name
                    }
                }
            }
        }

        # Call the Sheets API
        sheet = service.spreadsheets()
        result = (
            sheet.batchUpdate(spreadsheetId=SAMPLE_SPREADSHEET_ID, body=body)
            .execute()
        )

    except HttpError as err:
        messagebox.showerror("Failed to add new event", err)
    else:
        print("Event added")
    
        update_values(name, data_frame)


def update_data_frame_value(row=0, col=0, index='', value=None):
    global data_frame

    if data_frame is None:
        messagebox.showerror("Error", "Data frame is None")
        return

    if value is None:
        messagebox.showerror("Error", "Value to update is None")
        return
    
    if index not in INDEX:
        data_frame.at[row, col] = value
    else:
        data_frame.at[INDEX[index][0], INDEX[index][1]] = value

def get_data_frame_value(row=0, col=0, index=''):
    global data_frame

    if data_frame is None:
        messagebox.showerror("Error", "Data frame is None")
        return

    if index not in INDEX:
        return data_frame.at[row, col]
    else:
        return data_frame.at[INDEX[index][0], INDEX[index][1]]

# Test the functions
login()
if creds:
    get_values('Template')
    update_data_frame_value(0, 1, value='2024 24H SPA')
    update_values('Template', data_frame)
    add_event('2024 24H SPA')