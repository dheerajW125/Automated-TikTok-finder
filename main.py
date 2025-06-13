import time
import json
import gspread
from google.oauth2.service_account import Credentials
from tiktok_extractor import TikTokDataExtractor
from profile_matcher import TikTokProfileMatcher    
from rapid_api import fetch_tiktok_user_info
from sheet_writing import write_to_google_sheet  # Your function from earlier

SERVICE_ACCOUNT_FILE = "/home/ubuntu/TikTok-finder/creds.json"
SPREADSHEET_ID = "1KScxO33CGnVrFnY9qAdTfpgpgPQQkbtwQZUCIpyf3Jk"
INPUT_SHEET = "People data"
OUTPUT_SHEET = "search results "
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def process_name(name_to_search):
    extractor = TikTokDataExtractor()
    matcher = TikTokProfileMatcher()
    
    # 1. Search TikTok profiles
    usernames, metadata, logs = extractor.batch_search_tiktok_profiles(name_to_search)

    print(f"\n[TIKTOK PROFILES FOUND for {name_to_search}]")
    for user in usernames:
        print(f"Profile_url - https://www.tiktok.com/@{user}")
        for key, value in metadata[user].items():
            print(f"  {key}: {value}")
        print()

    # 2. Gemini AI ranking
    gemini_result = matcher.evaluate_profiles_with_gemini(
        name=name_to_search,
        location="",  # Extend if needed
        usernames_with_metadata=metadata
    )
    
    print(f"\n[🔍 GEMINI AI EVALUATION for {name_to_search}]")
    print(json.dumps(gemini_result, indent=2))

    best_match = gemini_result["best_match"]
    confidence = gemini_result.get("confidence_score")
    reasoning = gemini_result.get("reasoning")

    # 3. Fetch detailed user info from TikTok API
    result_data = fetch_tiktok_user_info(best_match)
    data = json.loads(result_data)

    user = data['userInfo']['user']
    stats = data['userInfo']['statsV2']  # 'statsV2' returns string values
    is_influencer = int(stats.get("followerCount", 0) or 0) > 5000
    share = data.get('shareMeta', {})

    # 4. Prepare dict for Google Sheets
    extracted = {
        "id": user.get("id"),
        "name": user.get("uniqueId"),
        "uniqueId": user.get("uniqueId"),
        "nickname": user.get("nickname"),
        "email": None,  # Not in API
        "verified": user.get("verified"),
        "bioLink": user.get("bioLink", {}).get("link"),
        "privateAccount": user.get("privateAccount"),
        "location": user.get("region"),
        "followerCount": stats.get("followerCount"),
        "followingCount": stats.get("followingCount"),
        "is_influencer": is_influencer,
        "heartCount": stats.get("heartCount"),
        "videoCount": stats.get("videoCount"),
        "diggCount": stats.get("diggCount"),
        "friendCount": stats.get("friendCount"),
        "share_title": share.get("title"),
        "share_desc": share.get("desc"),
        "gemini_best_match": best_match,
        "confidence_score": confidence,
        "reasoning": reasoning
    }
    
    print(f"Extracted data for {name_to_search}: {extracted}")

    return extracted


def main():
    # Setup Google Sheets auth
    credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    gc = gspread.authorize(credentials)
    spreadsheet = gc.open_by_key(SPREADSHEET_ID)

    # Step 1: Check trigger
    trigger_sheet = spreadsheet.worksheet("Trigger")
    trigger_data = trigger_sheet.get_all_records()

    print("Trigger sheet rows read:")
    for idx, row in enumerate(trigger_data, start=2):
        print(f"Row {idx} - Trigger_Name: '{row['Trigger_Name']}', Status: '{row['Status']}'")

    trigger_row_index = None
    trigger_name = None
    trigger_status = None

    # Look for the row where Trigger_Name == "start" (case-insensitive, stripped)
    for idx, row in enumerate(trigger_data, start=2):
        name = str(row["Trigger_Name"]).strip().lower()
        status = str(row["Status"]).strip().lower()
        print(f"Checking row {idx}: Trigger_Name='{name}', Status='{status}'")
        if name == "start":
            trigger_row_index = idx
            trigger_name = name
            trigger_status = status
            print(f"Trigger found at row {idx} with status '{status}'")
            break

    if trigger_name != "start":
        print("[TRIGGER] Script is not allowed to run (Trigger_Name is not 'start'). Exiting.")
        return

    # Update Status to 'running' before processing
    print(f"Updating Trigger sheet status at row {trigger_row_index} to 'running'")
    trigger_sheet.update_cell(trigger_row_index, 2, "running")  # Column B = Status

    # Step 2: Read People data sheet
    people_sheet = spreadsheet.worksheet(INPUT_SHEET)
    people_data = people_sheet.get_all_records()

    for idx, person in enumerate(people_data, start=2):  # start=2 to match Google Sheets row number
        name = person.get("Name")
        status_raw = person.get("Status", "")
        status = str(status_raw).strip().lower()

        # Debug print to check status values exactly
        print(f"Row {idx}: Name='{name}', Raw Status='{status_raw}', Processed Status='{status}'")

        # Skip if no name or already running/completed
        if not name or status in ["running", "completed"]:
            print(f"Skipping row {idx} - status='{status}'")
            continue

        print(f"\n--- Processing: {name} ---")
        try:
            extracted = process_name(name)
            write_to_google_sheet(
                extracted=extracted,
                spreadsheet_id=SPREADSHEET_ID,
                worksheet_name=OUTPUT_SHEET,
                service_account_file=SERVICE_ACCOUNT_FILE
            )

            # Update person's status to "completed"
            people_sheet.update_cell(idx, 4, "completed")  # Column D = Status

        except Exception as e:
            print(f"Error processing {name}: {e}")
            people_sheet.update_cell(idx, 4, f"error: {str(e)[:50]}")  # Log error briefly

    # Step 3: Update trigger sheet to stopped
    if trigger_row_index:
        print(f"Updating Trigger sheet at row {trigger_row_index} to stop/stopped")
        trigger_sheet.update_cell(trigger_row_index, 1, "stop")    # Column A = Trigger_Name
        trigger_sheet.update_cell(trigger_row_index, 2, "stopped") # Column B = Status
        print("[TRIGGER] Script finished. Trigger updated to 'stop' and 'stopped'.")

def polling_loop():
    while True:
        try:
            main()
        except Exception as e:
            print(f"Error in main loop: {e}")
        print("Sleeping for 30 seconds before checking trigger again...")
        time.sleep(30)

if __name__ == "__main__":
    polling_loop()