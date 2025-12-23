
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
import signal
from datetime import datetime
from dotenv import load_dotenv
from crewai import Task, Crew, Process, LLM

from agents.email_parser_agent import create_email_parser_agent
from agents.advisor_agent import create_advisor_agent  # NEW IMPORT
from agents.calendar_agent import create_calendar_agent
from utils.gmail_setup import setup_gmail, fetch_one_email
from utils.database import setup_database, store_email

# Email configuration
EMAIL_CONFIG = {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "sender_email": os.getenv("SENDER_EMAIL"),
    "sender_password": os.getenv("EMAIL_APP_PASSWORD"),
    "sender_name": "Calendar Assistant"
}

def get_llm():
    """Get LLM with rate limit handling"""
    os.environ["GROQ_API_KEY"] = "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"
    llm = LLM(
        model="groq/llama-3.1-8b-instant",
        temperature=0.1,
        max_tokens=500,
    )
    return llm

def process_incoming_email():
    """Fetch and store one email from Gmail"""
    gmail_service = setup_gmail()
    engine = setup_database()

    email = fetch_one_email(gmail_service)
    if email is None:
        return None

    email_id = store_email(engine, email)
    return {
        "email_id": email_id,
        "body": email["body"],
        "sender_email": email["sender_email"]
    }

def run_orchestration():
    """Main orchestration: Email Parser -> Advisor -> Calendar Agent"""
    
    print("\n" + "="*70)
    print("STARTING EMAIL-TO-CALENDAR ORCHESTRATION WITH ADVISOR")
    print("="*70 + "\n")
    
    # Step 1: Fetch incoming email
    print("📧 Step 1: Fetching incoming email...")
    email_data = process_incoming_email()
    
    if not email_data:
        print("⏳ No email to process")
        return None
    
    print(f"✅ Email received (ID: {email_data['email_id']})")
    print(f"📌 From: {email_data['sender_email']}")
    print(f"📄 Body preview: {email_data['body'][:200]}...\n")
    
    # Initialize LLM
    def get_llm():
        return LLM(
            model="ollama/qwen2.5:14b",  # Better than llama3
            temperature=0.1,
            max_tokens=4000,
            provider="ollama"
        )

    llm = get_llm()
    print("✅ LLM initialized\n")
    
    # Create agents
    email_parser_agent = create_email_parser_agent(llm)
    advisor_agent = create_advisor_agent(llm)  # NEW AGENT
    
    calendar_agent = create_calendar_agent(
        token_file="token.json",
        email_config=EMAIL_CONFIG,
        llm=llm,
        email_only=False
    )
    
    email_sender_agent = create_calendar_agent(
        token_file="token.json",
        email_config=EMAIL_CONFIG,
        llm=llm,
        email_only=True
    )
    
    print("✅ Agents created\n")
    
    # TASK 1: Parse email and store structured data (NO CHANGES)
    task1 = Task(
        description=f"""
Parse and store email ID {email_data['email_id']}.

Steps you MUST follow:
1. Call parse_email_tool with the email content: {email_data['body']}
2. You will receive a JSON object with fields like:
   - sender_role
   - project_title
   - meeting_topic
   - meeting_date
   - meeting_time
   - duration
   - etc.
3. Call store_parsed_email with:
   - email_id = {email_data['email_id']}
   - parsed_data = EXACT JSON from step 1
4. Return the parsed JSON EXACTLY as received from parse_email_tool.

IMPORTANT: Return the complete parsed JSON object, not just a confirmation message.
""",
        agent=email_parser_agent,
        expected_output="Complete parsed JSON with meeting details"
    )
    
    # TASK 2: Generate advice and tasks (NEW TASK)
    task2 = Task(
        description=f"""
Generate personalized advice and tasks for the upcoming meeting.

Sender email: {email_data['sender_email']}

Steps you MUST follow:
1. Call fetch_person_context with sender_email: "{email_data['sender_email']}"
   This will return person information including name, role, project details, etc.

2. Look at the parsed email data from the previous task (task1)

3. Call generate_advice with:
   - parsed_email: the complete JSON from task1
   - person_context: the data from step 1
   
   This will return a dict with 'tasks' (list of 5 items) and 'advice' (list of 5 items)

4. Extract project_title from the parsed email JSON (from task1)

5. Call store_advice with:
   - email_id: {email_data['email_id']}
   - project_title: [extracted from task1]
   - tasks: [the tasks list from step 3]
   - advice: [the advice list from step 3]

6. Return: "ADVICE GENERATED AND STORED"

IMPORTANT: Follow all steps in order. Use the exact tools mentioned.
""",
        agent=advisor_agent,
        expected_output="'ADVICE GENERATED AND STORED'",
        context=[task1]
    )
    
    # TASK 3: Check availability (RENUMBERED, NO OTHER CHANGES)
    task3 = Task(
        description=f"""
Look at the parsed meeting data from task 1.

Extract these fields from the parsed data:
- meeting_date (format: YYYY-MM-DD)
- meeting_time (format: HH:MM)
- duration (in hours, default to 1.0 if not specified)

Construct start_time and end_time:
- start_time = meeting_date + "T" + meeting_time + ":00"
- end_time = start_time + duration hours

Example: If meeting_date="2025-12-20", meeting_time="10:00", duration=1
Then: start_time="2025-12-20T10:00:00", end_time="2025-12-20T11:00:00"

Use check_calendar_availability with:
- start_time: [calculated start_time]
- end_time: [calculated end_time]
- timezone: Africa/Tunis

Return ONLY: "AVAILABLE" or "NOT AVAILABLE" based on the result.
""",
        agent=calendar_agent,
        expected_output="Either 'AVAILABLE' or 'NOT AVAILABLE'",
        context=[task1]
    )
    
    # TASK 4: Create event OR find alternatives (RENUMBERED, NO OTHER CHANGES)
    task4 = Task(
        description=f"""
Look at the previous task result and the parsed meeting data from task 1.

If availability check says "AVAILABLE":
  Extract from parsed data:
  - project_title (use as summary)
  - meeting_topic (use as description)
  - meeting_date and meeting_time (to construct start_time)
  - duration (to calculate end_time)
  - sender_email: {email_data['sender_email']} (use as attendees)
  
  Use create_calendar_event with these values:
  * summary: [project_title]
  * start_time: [meeting_date + "T" + meeting_time + ":00"]
  * end_time: [start_time + duration hours]
  * description: [meeting_topic]
  * attendees: {email_data['sender_email']}
  * timezone: Africa/Tunis
  
  After creating, return: "EVENT CREATED"

If availability check says "NOT AVAILABLE":
  Use find_alternative_slots with:
  * start_date: [meeting_date + "T" + meeting_time + ":00"]
  * duration_hours: [parsed duration or 1.0]
  * days_ahead: 7
  * timezone: Africa/Tunis
  
  Return: "ALTERNATIVES FOUND: " followed by the list of alternatives
""",
        agent=calendar_agent,
        expected_output="'EVENT CREATED' or 'ALTERNATIVES FOUND: [list]'",
        context=[task1, task3]
    )
    
    # TASK 5: Send email notification (RENUMBERED, NO OTHER CHANGES)
   # TASK 5: Send email notification (FIXED VERSION)
    task5 = Task(
        description=f"""
    The previous task said "EVENT CREATED" which means the meeting was successfully scheduled.

    You MUST now send a confirmation email.

    Use send_email tool with these EXACT parameters:
    - recipient: {email_data['sender_email']}
    - subject: ✅ Meeting Confirmed: Role-Based Weighting Discussion
    - body: Hello,

    Your meeting has been successfully scheduled for Monday, December 23, 2025 at 01:00 PM - 02:00 PM (Africa/Tunis timezone).

    Topic: Introducing role-based weighting to improve decision quality

    Please let me know if you need any changes.

    Kind regards,
    Ichaoui Chaima
    - meeting_details: Meeting: Role-Based Weighting Discussion
    Time: Monday, December 23, 2025 at 01:00 PM - 02:00 PM
    Description: Introducing role-based weighting to improve decision quality

    After calling send_email, return EXACTLY: "EMAIL SENT"

    DO NOT extract data. DO NOT analyze. JUST CALL send_email with the parameters above.
    """,
        agent=email_sender_agent,
        expected_output="'EMAIL SENT'",
        context=[task1, task3, task4]
    ) 
    # Create unified crew with ALL agents
    crew = Crew(
        agents=[email_parser_agent, advisor_agent, calendar_agent, email_sender_agent],
        tasks=[task1, task2, task3, task4, task5],  # NOW 5 TASKS
        process=Process.sequential,
        verbose=True
    )
    
    print("🚀 Starting orchestration...\n")
    result = crew.kickoff()
    
    print("\n" + "="*70)
    print("✅ ORCHESTRATION COMPLETED")
    print("="*70)
    print(f"\n{result}\n")
    print("📬 Check:")
    print("  - Email inbox for confirmation")
    print("  - Google Calendar for event")
    print("  - Database 'recommendations' table for advice and tasks")
    print("="*70 + "\n")
    
    return result

if __name__ == "__main__":
    if not EMAIL_CONFIG["sender_email"] or not EMAIL_CONFIG["sender_password"]:
        print("\n❌ ERROR: Missing email credentials in .env file!")
        print("Please set SENDER_EMAIL and EMAIL_APP_PASSWORD")
        exit(1)
    
    print(f"\n✅ Email configured: {EMAIL_CONFIG['sender_email']}")
    
    result = run_orchestration()