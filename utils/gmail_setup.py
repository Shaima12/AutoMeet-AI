import os
import base64
from email import message_from_bytes
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SUBJECT_KEYWORDS = ["meet", "meeting", "collaboration", "client", "partenaria"]
MAX_BODY_LENGTH = 2000

def setup_gmail():
    """Setup Gmail API connection"""
    print("🔐 Setting up Gmail...")
    
    SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
    creds = None
    
    if os.path.exists("credentials/token.json"):
        creds = Credentials.from_authorized_user_file("credentials/token.json", SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("credentials/token.json", "w") as token:
            token.write(creds.to_json())

    print("✅ Gmail connected\n")
    return build("gmail", "v1", credentials=creds)

def is_relevant_subject(subject: str) -> bool:
    """Check if email subject contains relevant keywords"""
    return any(keyword in subject.lower() for keyword in SUBJECT_KEYWORDS)

def fetch_one_email(gmail_service):
    """Fetch one relevant email from Gmail"""
    results = gmail_service.users().messages().list(userId="me", maxResults=10).execute()
    messages = results.get("messages", [])

    for msg in messages:
        raw_msg = gmail_service.users().messages().get(userId="me", id=msg["id"], format="raw").execute()
        decoded = base64.urlsafe_b64decode(raw_msg["raw"])
        mime_msg = message_from_bytes(decoded)

        subject = mime_msg.get("Subject", "No Subject")
        if not is_relevant_subject(subject):
            continue

        # Extract body
        body = ""
        if mime_msg.is_multipart():
            for part in mime_msg.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode(errors="ignore")
                    break
        else:
            body = mime_msg.get_payload(decode=True).decode(errors="ignore")

        from_header = mime_msg.get("From", "")
        if "<" in from_header:
            sender_name = from_header.split("<")[0].strip().strip('"')
            sender_email = from_header.split("<")[1].split(">")[0]
        else:
            sender_name = from_header
            sender_email = from_header

        email = {
            "sender_email": sender_email,
            "sender_name": sender_name,
            "subject": subject,
            "body": body[:MAX_BODY_LENGTH],
        }

        print(f"✅ Relevant email found: {subject}")
        return email

    print("⏳ No relevant email found")
    return None