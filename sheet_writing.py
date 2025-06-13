import gspread
from google.oauth2.service_account import Credentials

def write_to_google_sheet(
    extracted: dict,
    spreadsheet_id: str = "1KScxO33CGnVrFnY9qAdTfpgpgPQQkbtwQZUCIpyf3Jk",
    worksheet_name: str = "search results sheet",
    service_account_file: str = "/home/ubuntu/TikTok-finder/creds.json"
):
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    credentials = Credentials.from_service_account_file(
        service_account_file,
        scopes=scopes
    )

    gc = gspread.authorize(credentials)
    spreadsheet = gc.open_by_key(spreadsheet_id)

    try:
        worksheet = spreadsheet.worksheet(worksheet_name)
    except gspread.exceptions.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title=worksheet_name, rows="100", cols="20")

    existing_headers = worksheet.row_values(1)

    # Create headers if not present
    if not existing_headers:
        worksheet.append_row(list(extracted.keys()))
        existing_headers = list(extracted.keys())
    else:
        # Add missing headers if any new keys appear
        new_keys = [key for key in extracted if key not in existing_headers]
        if new_keys:
            print(f"⚠️ Adding new headers to sheet: {new_keys}")
            updated_headers = existing_headers + new_keys
            worksheet.delete_row(1)
            worksheet.insert_row(updated_headers, index=1)
            existing_headers = updated_headers

    # Check for duplicate ID
    if "id" in existing_headers:
        id_col_index = existing_headers.index("id") + 1
        id_column_values = worksheet.col_values(id_col_index)
        if str(extracted.get("id")) in id_column_values:
            print(f"⚠️ Duplicate ID found: {extracted.get('id')} — Skipping write.")
            return

    # Align data to headers
    row_data = [extracted.get(header, "") for header in existing_headers]
    worksheet.append_row(row_data)
    print("✅ Data written to Google Sheet successfully.")
