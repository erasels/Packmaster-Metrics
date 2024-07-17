import datetime
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Full access scope allows for reading and writing.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = "1vXWjw_8aKNXZeZZMMTpCxPYUEi07M71wc_ywYUW_-Ko"

script_dir = os.path.dirname(os.path.abspath(__file__))
# Define file paths relative to the script location.
token_path = os.path.join(script_dir, 'token.json')
credentials_path = os.path.join(script_dir, 'credentials.json')


def update_insights(insights: dict):
    sheet = auth()

    try:
        # Get the titles of all existing sheets to check if they need to be created.
        sheet_metadata = sheet.get(spreadsheetId=SPREADSHEET_ID).execute()
        existing_sheets = {s['properties']['title']: s['properties']['sheetId'] for s in sheet_metadata.get('sheets', [])}

        for sheet_name, content in insights.items():
            data = [
                       [content['description']],  # First row is description
                       content['headers']  # Second row is headers
                   ] + content['data']  # Data rows follow

            # Only prepare addSheet request if sheet does not exist.
            if sheet_name not in existing_sheets:
                requests = [{'addSheet': {'properties': {'title': sheet_name}}}]
                response = sheet.batchUpdate(spreadsheetId=SPREADSHEET_ID, body={'requests': requests}).execute()
                # Find the new sheetId from the response.
                new_sheet_id = response['replies'][0]['addSheet']['properties']['sheetId']
                existing_sheets[sheet_name] = new_sheet_id

            # Prepare requests for freezing rows and formatting headers.
            format_requests = [
                {
                    'updateSheetProperties': {
                        'properties': {
                            'sheetId': existing_sheets[sheet_name],
                            'gridProperties': {'frozenRowCount': 2}
                        },
                        'fields': 'gridProperties.frozenRowCount'
                    }
                },
                {
                    'repeatCell': {
                        'range': {
                            'sheetId': existing_sheets[sheet_name],
                            'startRowIndex': 1,
                            'endRowIndex': 2,
                            'startColumnIndex': 0,
                            'endColumnIndex': len(content['headers'])
                        },
                        'cell': {
                            'userEnteredFormat': {
                                'backgroundColor': {
                                    'red': 1.0,
                                    'green': 0.9,
                                    'blue': 0.9
                                },
                                'textFormat': {
                                    'bold': True
                                }
                            }
                        },
                        'fields': 'userEnteredFormat(backgroundColor,textFormat)'
                    }
                }
            ]

            if "Pack" in content['headers']:
                pack_column_index = content['headers'].index("Pack")
                format_requests.append({
                    'setBasicFilter': {
                        'filter': {
                            'range': {
                                'sheetId': existing_sheets[sheet_name],
                                'startRowIndex': 1,
                                'startColumnIndex': 0,
                                'endColumnIndex': len(content['headers'])
                            },
                            'filterSpecs': [{
                                'filterCriteria': {
                                    'condition': {
                                        'type': 'TEXT_NOT_CONTAINS',
                                        'values': [{
                                            'userEnteredValue': ":"
                                        }]
                                    }
                                },
                                'columnIndex': pack_column_index
                            }]
                        }
                    }
                })
            else:
                format_requests.append({
                    'setBasicFilter': {
                        'filter':{
                            'range': {
                                'sheetId': existing_sheets[sheet_name],
                                'startRowIndex': 1,
                                'startColumnIndex': 0,
                                'endColumnIndex': len(content['headers'])
                            } 
                        }
                    }
                })

            # Apply formatting requests.
            if format_requests:
                sheet.batchUpdate(spreadsheetId=SPREADSHEET_ID, body={'requests': format_requests}).execute()

            # Write data to the sheet.
            body = {
                'values': data
            }
            sheet.values().update(
                spreadsheetId=SPREADSHEET_ID, range=f"{sheet_name}!A1",
                valueInputOption="USER_ENTERED", body=body).execute()

    except HttpError as err:
        print(err)


def update_summary_sheet():
    sheet = auth()

    try:
        # Get the titles and IDs of all existing sheets
        sheet_metadata = sheet.get(spreadsheetId=SPREADSHEET_ID).execute()
        sheets = sheet_metadata.get('sheets', [])
        existing_sheets = {s['properties']['title']: s['properties']['sheetId'] for s in sheets}

        # Check if the "Summary" sheet exists, create if not
        if "Summary" not in existing_sheets:
            requests = [{'addSheet': {'properties': {'title': "Summary"}}}]
            response = sheet.batchUpdate(spreadsheetId=SPREADSHEET_ID, body={'requests': requests}).execute()
            summary_sheet_id = response['replies'][0]['addSheet']['properties']['sheetId']
            existing_sheets["Summary"] = summary_sheet_id
        else:
            summary_sheet_id = existing_sheets["Summary"]

        # Prepare data to write to "Summary" sheet
        current_time = datetime.datetime.now().strftime("%Y/%m/%d %H:%M")
        values = [
            [f"Last updated: {current_time}"],  # First row with the update time
            [],  # Second row is empty
            ["Quick navigation"],  # Third row text
        ]

        # Retrieve descriptions from each sheet and prepare navigation links
        for sheet_title in existing_sheets:
            if sheet_title == "Summary":
                continue
            sheet_id = existing_sheets[sheet_title]
            description = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=f"{sheet_title}!A1").execute().get('values', [['']])[0][0]
            link = f'=HYPERLINK("#gid={sheet_id}", "{sheet_title}")'  # Creating a hyperlink to the sheet
            values.append([link, description])  # Appending link and description to the values list

        # Update the "Summary" sheet with the new data
        body = {'values': values}
        sheet.values().update(
            spreadsheetId=SPREADSHEET_ID, range="Summary!A1",
            valueInputOption="USER_ENTERED", body=body).execute()

    except HttpError as err:
        print(err)


def auth():
    creds = None
    creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(token_path, "w") as token:
            token.write(creds.to_json())
    service = build("sheets", "v4", credentials=creds)
    sheet = service.spreadsheets()
    return sheet


if __name__ == "__main__":
    # Only for testing, should be called from main.py
    test_data = {
        "Test": {
            "description": "Description of what Sheet1 insight means",
            "headers": ["Header1", "Header2", "Header3"],
            "data": [
                ["Data1", "Data2", "Data3"],
                ["Data4", "Data5", "Data6"],
            ]
        }
    }
    #update_insights(test_data)
    update_summary_sheet()
