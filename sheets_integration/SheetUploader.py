import datetime
import os.path
import time
from zoneinfo import ZoneInfo

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Full access scope allows for reading and writing.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = "146GPNf1aCHj5URk_oMkYS064HuRcP4vgbtCAkQ9NVWo"

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
                requests = [{'addSheet': {'properties': {'title': sheet_name,
                                                         'gridProperties': {
                                                             'rowCount': len(content['data']) + 2,
                                                             'columnCount': len(content['headers']) + 1
                                                             # Adding additional column so description doesn't get cut off
                                                         }
                                                         }}}]
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
                                    'red': 0.85,
                                    'green': 0.85,
                                    'blue': 1
                                },
                                'textFormat': {
                                    'bold': True
                                },
                                'horizontalAlignment': 'CENTER',
                                'wrapStrategy': 'WRAP'
                            }
                        },
                        'fields': 'userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,wrapStrategy)'
                    }
                },
                {
                    "autoResizeDimensions": {
                        "dimensions": {
                            "sheetId": existing_sheets[sheet_name],
                            "dimension": "COLUMNS",
                            "startIndex": 0,
                            "endIndex": len(content['headers'])
                        }
                    }
                }
            ]
            # Adds a default filter depending on if there's a Pack column
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
                        'filter': {
                            'range': {
                                'sheetId': existing_sheets[sheet_name],
                                'startRowIndex': 1,
                                'startColumnIndex': 0,
                                'endColumnIndex': len(content['headers'])
                            }
                        }
                    }
                })

            # This is to make the conditional formatting for the pack wr by asc, but it was so much code
            if content['headers'][0] == "Pack" and "Overall Win Rate" in content['headers'] and "A20" in content['headers']:
                formatting_requests = pack_wr_by_asc_formatting(content, existing_sheets[sheet_name])
                format_requests.extend(formatting_requests)

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

        # Check if the "Summary" sheet exists, create and make first sheet if not
        if "Summary" not in existing_sheets:
            requests = [{'addSheet': {'properties': {'title': "Summary", 'index': 0}}}]
            response = sheet.batchUpdate(spreadsheetId=SPREADSHEET_ID, body={'requests': requests}).execute()
            summary_sheet_id = response['replies'][0]['addSheet']['properties']['sheetId']
            existing_sheets["Summary"] = summary_sheet_id
        else:
            summary_sheet_id = existing_sheets["Summary"]

        # Prepare data to write to "Summary" shee
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

        # Color formatting
        format_requests = []
        format_requests = apply_summary_formatting(summary_sheet_id)
        sheet.batchUpdate(spreadsheetId=SPREADSHEET_ID, body={'requests': format_requests}).execute()

    except HttpError as err:
        print(err)


def pack_wr_by_asc_formatting(content: dict, sheet_id: int) -> list:
    format_requests = []

    # Conditional Formatting Rules
    format_requests.append({
        'addConditionalFormatRule': {
            'rule': {
                'ranges': [{
                    'sheetId': sheet_id,
                    'startRowIndex': 2,
                    'startColumnIndex': 2,
                    'endColumnIndex': len(content['headers'])
                }],
                'booleanRule': {
                    'condition': {
                        'type': 'CUSTOM_FORMULA',
                        'values': [{
                            'userEnteredValue': '=AND(C3<$B3, C3<>"N/A")'
                        }]
                    },
                    'format': {
                        'backgroundColor': {
                            'red': 0.957,
                            'green': 0.8,
                            'blue': 0.8
                        }
                    }
                }
            },
            'index': 0
        }
    })

    format_requests.append({
        'addConditionalFormatRule': {
            'rule': {
                'ranges': [{
                    'sheetId': sheet_id,
                    'startRowIndex': 2,
                    'startColumnIndex': 2,
                    'endColumnIndex': len(content['headers'])
                }],
                'booleanRule': {
                    'condition': {
                        'type': 'CUSTOM_FORMULA',
                        'values': [{
                            'userEnteredValue': '=AND(C3>$B3, C3<>"N/A")'
                        }]
                    },
                    'format': {
                        'backgroundColor': {
                            'red': 0.718,
                            'green': 0.882,
                            'blue': 0.804
                        }
                    }
                }
            },
            'index': 1
        }
    })

    # Column Resizing
    format_requests.append({
        'updateDimensionProperties': {
            'range': {
                'sheetId': sheet_id,
                'dimension': 'COLUMNS',
                'startIndex': 2,
                'endIndex': len(content['headers'])
            },
            'properties': {
                'pixelSize': 52
            },
            'fields': 'pixelSize'
        }
    })
    format_requests.append({
        'repeatCell': {
            'range': {
                'sheetId': sheet_id,
                'startRowIndex': 1,
                'startColumnIndex': 1,
                'endColumnIndex': len(content['headers'])
            },
            'cell': {
                'userEnteredFormat': {
                    'horizontalAlignment': 'CENTER'
                }
            },
            'fields': 'userEnteredFormat.horizontalAlignment'
        }
    })

    return format_requests


def auth():
    creds = None
    if os.path.exists(token_path):
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


def delete_all_sheets_except_first(spreadsheet_id=SPREADSHEET_ID):
    sheet = auth()
    sheet_metadata = sheet.get(spreadsheetId=SPREADSHEET_ID).execute()
    sheets = sheet_metadata.get('sheets', [])

    # Prepare the delete requests
    delete_requests = []
    for sheet_obj in sheets[1:]:
        sheet_id = sheet_obj['properties']['sheetId']
        delete_requests.append({
            'deleteSheet': {
                'sheetId': sheet_id
            }
        })

    body = {
        'requests': delete_requests
    }
    if delete_requests:
        sheet.batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()

    print(f"Deleted {len(delete_requests)} sheet(s).")


def apply_summary_formatting(sheet_id):
    def format_section(bg_color, start_row, stop_row):
        red, green, blue = [color / 255 if color > 1 else color for color in bg_color]
        return [
            {
                'repeatCell': {
                    'range': {
                        'sheetId': sheet_id,
                        'startRowIndex': start_row - 1,
                        'endRowIndex': stop_row,
                        'startColumnIndex': 0,
                        'endColumnIndex': 2
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'backgroundColor': {'red': red, 'green': green, 'blue': blue}
                        }
                    },
                    'fields': 'userEnteredFormat.backgroundColor'
                }
            }
        ]

    sections = [
        ([182, 215, 168], 1, 1),
        ([217, 217, 217], 3, 3),
        ([217, 210, 233], 4, 5),
        ([201, 218, 248], 6, 9),
        ([239, 239, 239], 10, 12),
        ([252, 229, 205], 13, 14),
        ([208, 224, 227], 15, 18),
        ([230, 184, 175], 19, 20),
        ([217, 210, 233], 21, 24)
    ]

    format_requests = []
    for color, start, end in sections:
        format_requests.extend(format_section(color, start, end))

    # Add column formatting
    format_requests.extend([
        # Column 1 formatting: bold and size 13
        {
            'repeatCell': {
                'range': {
                    'sheetId': sheet_id,
                    'startColumnIndex': 0,
                    'endColumnIndex': 1
                },
                'cell': {
                    'userEnteredFormat': {
                        'textFormat': {
                            'bold': True,
                            'fontSize': 13
                        }
                    }
                },
                'fields': 'userEnteredFormat.textFormat(bold,fontSize)'
            }
        },
        # Column 2 formatting: size 11, not bold
        {
            'repeatCell': {
                'range': {
                    'sheetId': sheet_id,
                    'startColumnIndex': 1,
                    'endColumnIndex': 2
                },
                'cell': {
                    'userEnteredFormat': {
                        'textFormat': {
                            'fontSize': 11
                        }
                    }
                },
                'fields': 'userEnteredFormat.textFormat.fontSize'
            }
        },
        # Set column 1 width to 400px
        {
            'updateDimensionProperties': {
                'range': {
                    'sheetId': sheet_id,
                    'dimension': 'COLUMNS',
                    'startIndex': 0,
                    'endIndex': 1
                },
                'properties': {
                    'pixelSize': 400
                },
                'fields': 'pixelSize'
            }
        },
        # Set column 2 width to 750px
        {
            'updateDimensionProperties': {
                'range': {
                    'sheetId': sheet_id,
                    'dimension': 'COLUMNS',
                    'startIndex': 1,
                    'endIndex': 2
                },
                'properties': {
                    'pixelSize': 750
                },
                'fields': 'pixelSize'
            }
        },
        # Set cell A3 to size 16 font
        {
            'repeatCell': {
                'range': {
                    'sheetId': sheet_id,
                    'startRowIndex': 2,
                    'endRowIndex': 3,
                    'startColumnIndex': 0,
                    'endColumnIndex': 1
                },
                'cell': {
                    'userEnteredFormat': {
                        'textFormat': {
                            'fontSize': 16
                        }
                    }
                },
                'fields': 'userEnteredFormat.textFormat.fontSize'
            }
        }
    ])

    return format_requests


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
    # update_insights(test_data)
    update_summary_sheet()
