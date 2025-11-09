import pandas as pd
import json

# Google Sheet as CSV
SHEET_URL = "https://docs.google.com/spreadsheets/d/1lhur_ygXHzSVKDsM0G2f8QDmVNzlLE9OqRXdtTVd1Qs/export?format=csv"

def migrate_to_json():
    """Convert Google Sheets data to JSON file."""
    try:
        # Read from Google Sheets
        print("Reading data from Google Sheets...")
        df = pd.read_csv(SHEET_URL)
        
        # Convert to list of dictionaries
        emails_list = []
        for _, row in df.iterrows():
            emails_list.append({
                "email": row["Email"],
                "name": row["Name"]
            })
        
        # Save to JSON file
        with open('emails_data.json', 'w') as f:
            json.dump(emails_list, f, indent=4)
        
        print(f"✅ Successfully migrated {len(emails_list)} emails to emails_data.json")
        print("\nPreview of first 3 records:")
        print(json.dumps(emails_list[:3], indent=2))
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    migrate_to_json()