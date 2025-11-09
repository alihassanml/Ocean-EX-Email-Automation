from fastapi import FastAPI, Query, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from email.message import EmailMessage
import smtplib
import ssl
import os
import json
from datetime import datetime
from dotenv import load_dotenv
from email_templates import templates
from typing import List, Dict

app = FastAPI()

# Setup templates
templates_html = Jinja2Templates(directory="templates")

# CORS middleware for API endpoints
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load credentials
load_dotenv()
EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = int(os.getenv("EMAIL_PORT"))
EMAIL_USER = os.getenv("EMAIL")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

# JSON file path
EMAILS_JSON_FILE = "emails_data.json"
STATUS_JSON_FILE = "email_status.json"

# Email attachments
MEDIA_DIR = "data/media"
ATTACHMENTS = [
    os.path.join(MEDIA_DIR, "image.jpeg"),
    os.path.join(MEDIA_DIR, "Pool bar inside the Bar area demo.mp4"),
    os.path.join(MEDIA_DIR, "Pool bar walk around in the Pool Zone demo.mp4"),
    os.path.join(MEDIA_DIR, "Pool bar Walk around video with LED on.mp4"),
    os.path.join(MEDIA_DIR, "Cruise Line Brochure.pdf"),
    os.path.join(MEDIA_DIR, "Resort digital brochure.pdf"),
]

def load_emails_from_json():
    """Load emails from JSON file."""
    try:
        if os.path.exists(EMAILS_JSON_FILE):
            with open(EMAILS_JSON_FILE, 'r') as f:
                return json.load(f)
        else:
            return []
    except Exception as e:
        print(f"Error loading emails: {e}")
        return []

def save_status_to_json(email_record):
    """Save or update email status in JSON file."""
    try:
        # Load existing status
        if os.path.exists(STATUS_JSON_FILE):
            with open(STATUS_JSON_FILE, 'r') as f:
                status_data = json.load(f)
        else:
            status_data = []
        
        # Check if email already exists, update it
        found = False
        for record in status_data:
            if record['email'] == email_record['email'] and record['day'] == email_record['day']:
                record.update(email_record)
                found = True
                break
        
        if not found:
            status_data.append(email_record)
        
        # Save back to file
        with open(STATUS_JSON_FILE, 'w') as f:
            json.dump(status_data, f, indent=4)
    except Exception as e:
        print(f"Error saving status: {e}")

def send_email(to_email, name, subject, body):
    """Send email with attachments."""
    msg = EmailMessage()
    msg["From"] = EMAIL_USER
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body.format(FirstName=name.split()[0]))

    # Attach media files
    for file_path in ATTACHMENTS:
        if os.path.exists(file_path):
            with open(file_path, "rb") as f:
                data = f.read()
                file_name = os.path.basename(file_path)
                msg.add_attachment(data, maintype="application", subtype="octet-stream", filename=file_name)

    # Send email
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(EMAIL_HOST, EMAIL_PORT, context=context) as server:
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        server.send_message(msg)

def process_emails_background(day: int):
    """Background task to process emails."""
    emails_list = load_emails_from_json()
    
    if day not in templates:
        print(f"Invalid day: {day}")
        return

    email_data = templates[day]

    for person in emails_list:
        email_record = {
            "email": person["email"],
            "name": person["name"],
            "day": day,
            "status": "Pending",
            "timestamp": datetime.now().isoformat(),
            "error": None
        }
        
        try:
            send_email(
                to_email=person["email"],
                name=person["name"],
                subject=email_data["subject"],
                body=email_data["body"],
            )
            email_record["status"] = "Success"
            print(f"Email sent successfully to {person['email']}")
        except Exception as e:
            email_record["status"] = "Failed"
            email_record["error"] = str(e)
            print(f"Failed to send to {person['email']}: {e}")
        
        # Save status after each email
        save_status_to_json(email_record)

# Route to serve the HTML page
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Serve the main dashboard page."""
    return templates_html.TemplateResponse("index.html", {"request": request})

@app.post("/upload-emails/")
def upload_emails(emails: List[Dict[str, str]]):
    """Upload emails list to JSON file."""
    try:
        with open(EMAILS_JSON_FILE, 'w') as f:
            json.dump(emails, f, indent=4)
        return {"status": "success", "message": f"{len(emails)} emails uploaded successfully"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/emails/")
def get_emails():
    """Get all emails from JSON file."""
    emails = load_emails_from_json()
    return {"emails": emails, "count": len(emails)}

@app.get("/send-emails/")
def send_emails(background_tasks: BackgroundTasks, day: int = Query(..., ge=1, le=3)):
    """Send email template based on the selected day (runs in background)."""
    emails_list = load_emails_from_json()
    
    if not emails_list:
        return {"status": "error", "message": "No emails found in JSON file"}
    
    if day not in templates:
        return {"status": "error", "message": "Invalid day. Use 1, 2, or 3."}
    
    # Add background task
    background_tasks.add_task(process_emails_background, day)
    
    return {
        "status": "processing",
        "message": f"Email sending started in background for Day {day}",
        "total_emails": len(emails_list),
        "day": day
    }

@app.get("/email-status/")
def get_email_status():
    """Get status of all sent emails."""
    try:
        if os.path.exists(STATUS_JSON_FILE):
            with open(STATUS_JSON_FILE, 'r') as f:
                status_data = json.load(f)
            
            # Calculate statistics
            total = len(status_data)
            success = len([r for r in status_data if r['status'] == 'Success'])
            failed = len([r for r in status_data if r['status'] == 'Failed'])
            pending = len([r for r in status_data if r['status'] == 'Pending'])
            
            return {
                "status": "success",
                "records": status_data,
                "statistics": {
                    "total": total,
                    "success": success,
                    "failed": failed,
                    "pending": pending
                }
            }
        else:
            return {
                "status": "success",
                "records": [],
                "statistics": {
                    "total": 0,
                    "success": 0,
                    "failed": 0,
                    "pending": 0
                }
            }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.delete("/clear-status/")
def clear_status():
    """Clear all email status records."""
    try:
        if os.path.exists(STATUS_JSON_FILE):
            os.remove(STATUS_JSON_FILE)
        return {"status": "success", "message": "Status cleared successfully"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)