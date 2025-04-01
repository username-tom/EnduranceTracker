'''
Helpers for Google Sheets API
'''


import sys
import os
OWD = os.getcwd()
sys.path.append(OWD)
os.chdir(OWD)

from docs.conf import *

class TrackerError(Exception):
    pass

import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from time import sleep
from pandas import DataFrame, to_datetime, concat
from tkinter import messagebox
import numpy as np
from datetime import timedelta

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

creds = None
data = DataFrame()

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

def get_sheets(id=SHEET_ID):
    global creds

    if creds is None:
        messagebox.showerror("Error", "Credentials is None")
        return

    try:
        service = build("sheets", "v4", credentials=creds)

        # Call the Sheets API
        sheet = service.spreadsheets()
        result = sheet.get(spreadsheetId=id).execute()
        sheets = result.get('sheets', [])

        if not sheets:
            messagebox.showerror("Error", "No sheets found.")
            return

        to_return = {}
        for sheet in sheets:
            # print(sheet.get('properties', {}).get('title', ''))
            to_return[sheet.get('properties', {}).get('title', '')] = sheet.get('properties', {}).get('sheetId', '')
        # print(to_return)
        return to_return
    except HttpError as err:
        messagebox.showerror("Error", err)
        return

def get_values(s="Template", range=SAMPLE_RANGE_NAME):
    global creds, data, SHEET_ID

    try:
        service = build("sheets", "v4", credentials=creds)

        # Call the Sheets API
        sheet = service.spreadsheets()
        result = (
            sheet.values()
            .get(spreadsheetId=SHEET_ID, range=f"{s}!{range}")
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
        data = DataFrame(data=values)
        # print(data)
        return data

def update_values(s="Template", v=None, range=SAMPLE_RANGE_NAME):
    global creds, data, SHEET_ID

    if v is None:
        raise TrackerError("Value to update is None")
    
    if isinstance(v, DataFrame):
        v = v.values.tolist()
        body = {
            'values': v
        }
    elif v is None:
        body = {
            'values': data.values.tolist()
        }
    elif isinstance(v, list):
        body = {
            'values': DataFrame(data=v).T.values.tolist()
        }
    else:
        body = {
            'values': DataFrame(data=v).values.tolist()
        }

    # print(body)
    
    try:
        service = build("sheets", "v4", credentials=creds)

        # body = {
        #     'values': v
        # }

        # Call the Sheets API
        sheet = service.spreadsheets()
        result = (
            sheet.values()
            .update(spreadsheetId=SHEET_ID, range=f"{s}!{range}", 
                    body=body, valueInputOption='RAW')
            .execute()
        )

        # print(result.get('updatedRange', []))

        if str(result.get('updatedRange', [])).split('!')[0].strip("\'") == s:
            print("Value updated")
        else:
            # print(str(result.get('updatedRange', [])).split('!')[0].strip("\'"), s)
            print("Value not updated")
    except HttpError as err:
        messagebox.showerror("Error", err)


def copy_template_to_new_sheet(template_id, new_sheet_id):
    global creds

    try:
        # if "Template" in get_sheets():
        #     # Delete the template sheet if it exists
        #     delete_event("Template")

        service = build('sheets', 'v4', credentials=creds)
        # Get the template sheet
        template_sheet = service.spreadsheets().get(spreadsheetId=template_id).execute()
        # template_sheet_data = template_sheet['sheets'][0]['properties']['title']
        template_sheet_data = "Template"

        # Copy the template sheet to the new spreadsheet
        request = {
            'destinationSpreadsheetId': new_sheet_id
        }
        response = service.spreadsheets().sheets().copyTo(
            spreadsheetId=template_id,
            sheetId=template_sheet['sheets'][0]['properties']['sheetId'],
            body=request
        ).execute()

        # Rename the copied sheet to the first page of the new spreadsheet
        new_sheet_title = response['title']
        service.spreadsheets().batchUpdate(
            spreadsheetId=new_sheet_id,
            body={
                'requests': [
                    {
                        'updateSheetProperties': {
                            'properties': {
                                'sheetId': response['sheetId'],
                                'title': template_sheet_data
                            },
                            'fields': 'title'
                        }
                    }
                ]
            }
        ).execute()

        # Get all sheets in the new spreadsheet
        new_sheets = service.spreadsheets().get(spreadsheetId=new_sheet_id).execute().get('sheets', [])

        # Delete all sheets except the copied template
        requests = []
        for sheet in new_sheets:
            if sheet['properties']['title'] != template_sheet_data:
                requests.append({
                    'deleteSheet': {
                        'sheetId': sheet['properties']['sheetId']
                    }
            })

        if requests:
            service.spreadsheets().batchUpdate(
            spreadsheetId=new_sheet_id,
            body={'requests': requests}
            ).execute()

    except HttpError as error:
        print(f"An error occurred: {error}")
        return None

def add_event(name=''):
    global creds, data

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
            sheet.batchUpdate(spreadsheetId=SHEET_ID, body=body)
            .execute()
        )

        #TODO: add result check here

    except HttpError as err:
        messagebox.showerror("Failed to add new event", err)
    else:
        print("Event added")

        update_data_frame_value(0, 1, value=name)
        update_values(name, data)

def delete_event(name=''):
    global creds

    if name == '':
        messagebox.showerror("Error", "Event name is empty")
        return
    
    if creds is None:
        messagebox.showerror("Error", "Credentials is None")
        return
    
    try:
        service = build("sheets", "v4", credentials=creds)

        body = {
            "requests":{
                "deleteSheet":{
                    "sheetId":name
                }
            }
        }

        # Call the Sheets API
        sheet = service.spreadsheets()
        result = (
            sheet.batchUpdate(spreadsheetId=SHEET_ID, body=body)
            .execute()
        )
    except HttpError as err:
        messagebox.showerror("Failed to delete event", err)
    else:
        print("Event deleted")


def update_data_frame_value(row=0, col=0, index='', value=None):
    global data

    if data is None:
        messagebox.showerror("Error", "Data frame is None")
        return

    if value is None:
        messagebox.showerror("Error", "Value to update is None")
        return
    
    if index not in INDEX:
        data.at[row, col] = value
    else:
        data.at[INDEX[index][0], INDEX[index][1]] = value

def get_data_frame_value(row=0, col=0, index=''):
    global data

    if data is None:
        raise TrackerError("Data frame is None")

    if index not in INDEX:
        return data.at[row, col]
    else:
        return data.at[INDEX[index][0], INDEX[index][1]]

def tz_diff(dt, tz1, tz2):
    date = to_datetime(dt)
    return date.tz_localize(tz1).tz_convert(tz2)


def format_timedelta(t: timedelta):
    return f'{int(t.total_seconds() // 3600):02d}:' \
           f'{int((t.total_seconds() // 60) % 60):02d}:' \
           f'{int(t.total_seconds() % 60):02d}'


# Test the functions
# login()
# if creds:
#     get_sheets()
    # get_values('Template')
    # update_data_frame_value(0, 1, value='2024 24H SPA')
    # update_values('Template', data)
    # add_event('2024 24H SPA')