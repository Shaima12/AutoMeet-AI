import os
import signal
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Dict
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

# Windows compatibility
if os.name == "nt":
    unix_signals = ["SIGHUP", "SIGTSTP", "SIGQUIT", "SIGCONT"]
    for sig_name in unix_signals:
        if not hasattr(signal, sig_name):
            setattr(signal, sig_name, signal.SIGTERM)

os.environ["CREWAI_DISABLE_TRACING"] = "true"
import os
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from pydantic import BaseModel, Field
from crewai import Agent
from crewai.tools import BaseTool
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Input schemas
class AvailabilityCheckInput(BaseModel):
    start_time: str = Field(..., description="Start time (YYYY-MM-DDTHH:MM:SS)")
    end_time: str = Field(..., description="End time (YYYY-MM-DDTHH:MM:SS)")
    timezone: str = Field(default="Africa/Tunis")

class FindAlternativeInput(BaseModel):
    start_date: str = Field(..., description="Start date (YYYY-MM-DDTHH:MM:SS)")
    duration_hours: float = Field(default=1.0)
    days_ahead: int = Field(default=7)
    timezone: str = Field(default="Africa/Tunis")

class CreateEventInput(BaseModel):
    summary: str = Field(..., description="Event title")
    start_time: str = Field(..., description="Start time")
    end_time: str = Field(..., description="End time")
    description: str = Field(default="")
    attendees: str = Field(default="", description="Comma-separated email addresses")
    timezone: str = Field(default="Africa/Tunis")

class SendEmailInput(BaseModel):
    recipient: str = Field(..., description="Recipient email address")
    subject: str = Field(..., description="Email subject")
    body: str = Field(..., description="Email body content")
    meeting_details: str = Field(default="", description="Meeting details to include")

# Tool: Check Availability
class CalendarAvailabilityTool(BaseTool):
    name: str = "check_calendar_availability"
    description: str = """Checks if a time slot is available in Google Calendar.
    Input: start_time, end_time in format YYYY-MM-DDTHH:MM:SS
    Returns JSON with 'available' field (true/false)"""
    args_schema: type = AvailabilityCheckInput
    token_file: str = Field(default="token.json", exclude=True)

    def _run(self, start_time: str, end_time: str, timezone: str = "Africa/Tunis") -> str:
        try:
            creds = Credentials.from_authorized_user_file(self.token_file)
            service = build("calendar", "v3", credentials=creds)
            tz = ZoneInfo(timezone)
            
            start_dt = datetime.fromisoformat(start_time).replace(tzinfo=tz)
            end_dt = datetime.fromisoformat(end_time).replace(tzinfo=tz)

            body = {
                "timeMin": start_dt.astimezone(ZoneInfo("UTC")).isoformat(),
                "timeMax": end_dt.astimezone(ZoneInfo("UTC")).isoformat(),
                "timeZone": timezone,
                "items": [{"id": "primary"}]
            }

            result = service.freebusy().query(body=body).execute()
            busy_times = result["calendars"]["primary"]["busy"]
            
            if busy_times:
                print(f"❌ Time slot NOT available - {len(busy_times)} conflict(s)")
                return json.dumps({
                    "available": False,
                    "message": f"NOT AVAILABLE"
                })
            
            print(f"✅ Time slot is available!")
            return json.dumps({
                "available": True,
                "message": "AVAILABLE"
            })
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return json.dumps({"error": str(e), "available": False})

# Tool: Find Alternatives
class FindAlternativeSlotsTool(BaseTool):
    name: str = "find_alternative_slots"
    description: str = """Finds alternative available slots (Monday-Friday, 9 AM - 5 PM).
    Returns JSON with 'alternatives' array."""
    args_schema: type = FindAlternativeInput
    token_file: str = Field(default="token.json", exclude=True)

    def _run(self, start_date: str, duration_hours: float = 1.0, 
             days_ahead: int = 7, timezone: str = "Africa/Tunis") -> str:
        try:
            print(f"🔍 Finding alternatives...")
            creds = Credentials.from_authorized_user_file(self.token_file)
            service = build("calendar", "v3", credentials=creds)
            tz = ZoneInfo(timezone)
            start_dt = datetime.fromisoformat(start_date).replace(tzinfo=tz)
            alternatives = []

            for day_offset in range(days_ahead):
                search_date = start_dt + timedelta(days=day_offset)
                if search_date.weekday() >= 5:
                    continue
                
                max_hour = 17 - int(duration_hours)
                for hour in range(9, max_hour + 1):
                    slot_start = search_date.replace(hour=hour, minute=0, second=0, microsecond=0)
                    slot_end = slot_start + timedelta(hours=duration_hours)
                    
                    if slot_end.hour > 17:
                        continue

                    body = {
                        "timeMin": slot_start.astimezone(ZoneInfo("UTC")).isoformat(),
                        "timeMax": slot_end.astimezone(ZoneInfo("UTC")).isoformat(),
                        "timeZone": timezone,
                        "items": [{"id": "primary"}]
                    }
                    result = service.freebusy().query(body=body).execute()
                    busy = result["calendars"]["primary"]["busy"]

                    if not busy:
                        alternatives.append({
                            "formatted": f"{slot_start.strftime('%A, %B %d at %I:%M %p')} - {slot_end.strftime('%I:%M %p')}"
                        })
                        if len(alternatives) >= 5:
                            break
                if len(alternatives) >= 5:
                    break
            
            print(f"✅ Found {len(alternatives)} alternatives")
            return json.dumps({"alternatives": alternatives})
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return json.dumps({"error": str(e), "alternatives": []})

# Tool: Create Event
class CreateCalendarEventTool(BaseTool):
    name: str = "create_calendar_event"
    description: str = """Creates a Google Calendar event."""
    args_schema: type = CreateEventInput
    token_file: str = Field(default="token.json", exclude=True)

    def _run(self, summary: str, start_time: str, end_time: str,
             description: str = "", attendees: str = "", timezone: str = "Africa/Tunis") -> str:
        try:
            print(f"📅 Creating event: {summary}")
            creds = Credentials.from_authorized_user_file(self.token_file)
            service = build("calendar", "v3", credentials=creds)
            tz = ZoneInfo(timezone)
            
            start_dt = datetime.fromisoformat(start_time).replace(tzinfo=tz)
            end_dt = datetime.fromisoformat(end_time).replace(tzinfo=tz)

            event = {
                "summary": summary,
                "description": description,
                "start": {"dateTime": start_dt.isoformat(), "timeZone": timezone},
                "end": {"dateTime": end_dt.isoformat(), "timeZone": timezone}
            }
            
            if attendees:
                event["attendees"] = [{"email": email.strip()} for email in str(attendees).split(",")]

            created = service.events().insert(calendarId="primary", body=event).execute()
            print(f"✅ Event created!")
            return json.dumps({"success": True, "message": "Event created successfully"})
        except Exception as e:
            print(f"❌ Failed: {str(e)}")
            return json.dumps({"error": str(e), "success": False})

# Tool: Send Email
class SendEmailTool(BaseTool):
    name: str = "send_email"
    description: str = """Sends an email notification."""
    args_schema: type = SendEmailInput
    email_config: dict = Field(default_factory=dict, exclude=True)

    def _run(self, recipient: str, subject: str, body: str, meeting_details: str = "") -> str:
        try:
            print(f"\n📧 Sending email to {recipient}...")
            
            msg = MIMEMultipart("alternative")
            msg["From"] = f"{self.email_config['sender_name']} <{self.email_config['sender_email']}>"
            msg["To"] = recipient
            msg["Subject"] = subject
            
            formatted_details = meeting_details.replace('\\n', '\n').replace('\n', '<br>') if meeting_details else ""
            
            html_body = f"""
            <html>
              <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <p>{body.replace(chr(10), '<br>')}</p>
                {f'<div style="margin-top: 20px; padding: 15px; background-color: #f5f5f5; border-left: 4px solid #4CAF50;">{formatted_details}</div>' if formatted_details else ''}
                <p style="margin-top: 30px; font-size: 12px; color: #666;">
                  This is an automated message from Calendar Assistant.
                </p>
              </body>
            </html>
            """
            
            msg.attach(MIMEText(html_body, "html"))
            
            with smtplib.SMTP(self.email_config["smtp_server"], self.email_config["smtp_port"]) as server:
                server.starttls()
                server.login(self.email_config["sender_email"], self.email_config["sender_password"])
                server.send_message(msg)
            
            print(f"✅ Email sent!")
            return json.dumps({"success": True, "message": f"Email sent to {recipient}"})
        except Exception as e:
            print(f"❌ Failed: {str(e)}")
            return json.dumps({"success": False, "error": str(e)})

def create_calendar_agent(token_file: str, email_config: dict, llm, email_only=False):
    """Create the calendar scheduling agent"""
    
    if email_only:
        # Agent spécialisé pour SEULEMENT envoyer des emails
        tools = [SendEmailTool(email_config=email_config)]
        role = "Email Sender"
        goal = "Send professional email notifications"
        backstory = "You write and send emails. You MUST use the send_email tool."
    else:
        # Agent normal avec tous les outils
        tools = [
            CalendarAvailabilityTool(token_file=token_file),
            FindAlternativeSlotsTool(token_file=token_file),
            CreateCalendarEventTool(token_file=token_file),
            SendEmailTool(email_config=email_config)
        ]
        role = "Calendar Assistant"
        goal = "Check availability, schedule meetings, and send emails"
        backstory = "You are a helpful calendar assistant."
    
    return Agent(
        role=role,
        goal=goal,
        backstory=backstory,
        tools=tools,
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=25
    )