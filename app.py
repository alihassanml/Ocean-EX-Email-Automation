from fastapi import FastAPI, Query
from email.message import EmailMessage
import pandas as pd
import smtplib
import ssl
import os
from dotenv import load_dotenv
from email_templates import templates

app = FastAPI()

# Load credentials
load_dotenv()
EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = int(os.getenv("EMAIL_PORT"))
EMAIL_USER = os.getenv("EMAIL")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

# Google Sheet as CSV
SHEET_URL = "https://docs.google.com/spreadsheets/d/1lhur_ygXHzSVKDsM0G2f8QDmVNzlLE9OqRXdtTVd1Qs/export?format=csv"

# Email attachments
MEDIA_DIR = "data/media"
ATTACHMENTS = [
    os.path.join(MEDIA_DIR, "image.jpeg"),
    os.path.join(MEDIA_DIR, "Pool bar inside the Bar area demo.mp4"),
    os.path.join(MEDIA_DIR, "Pool bar walk around in the Pool Zone demo.mp4"),
    os.path.join(MEDIA_DIR, "Pool bar Walk around video with LED on.mp4"),
]

def send_email(to_email, name, subject, body):
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

@app.get("/send-emails/")
def send_emails(day: int = Query(..., ge=1, le=3)):
    """Send email template based on the selected day."""
    df = pd.read_csv(SHEET_URL)

    if day not in templates:
        return {"error": "Invalid day. Use 1, 2, or 3."}

    email_data = templates[day]
    sent_count = 0

    for _, row in df.iterrows():
        try:
            send_email(
                to_email=row["Email"],
                name=row["Name"],
                subject=email_data["subject"],
                body=email_data["body"],
            )
            sent_count += 1
        except Exception as e:
            print(f"Failed to send to {row['Email']}: {e}")

    return {"status": "success", "sent": sent_count, "day": day}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)