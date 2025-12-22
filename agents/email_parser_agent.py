import signal
import json
import os
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
import re
import json
from datetime import datetime, timezone
from crewai import Agent
from crewai.tools import tool
from groq import Client
from sqlalchemy import text

# Initialize Groq client
client = Client(api_key="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")

def generate(prompt, max_tokens=500):
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=max_tokens
    )
    return response.choices[0].message.content

def clean_text(text):
    """Clean text for embedding: remove extra whitespace, newlines, non-ASCII, unicode artifacts, underscores"""
    text = text.replace("\n", " ").replace("\r", " ")
    text = re.sub(r"\\u[0-9a-fA-F]{4}", " ", text)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^\x00-\x7F]+", " ", text)
    text = re.sub(r"[_]{2,}", " ", text)
    return text.strip()

def extract(parsed):
    text = clean_text(parsed)
    json_start_index = text.find('json')
    json_end_index = text.rfind('}')
    json_string = text[json_start_index + len('json'):json_end_index + 1]
    json_data = json.loads(json_string)
    return json_data

def parse_email(email_text):
    print("I am in parse_email Function ")
    print(email_text)

    prompt = f"""
You are an enterprise email understanding agent.

Extract ONLY structured information.
Return VALID JSON.
If information is missing, use null.

Email:
\"\"\"{email_text}\"\"\"

Fields:
- sender_role (role of the sender in the context of the email: manager, client, supplier, team_member)
- project_title
- meeting topic (what will discuss in the meeting)
- relation_type (meeting_client, collaboration,supplier_offer)
- meeting_date
- meeting_time
- duration
- urgent (true/false)
- tasks_requested (array)
- documents_to_prepare (array)
- confirmation_status (confirmed / pending)
"""
    print("*************************the output is ready************** ")
    output = generate(prompt)
    print("***************************************will extract the JSON****************")
    Json = extract(output)
    return Json

@tool("parse_email_tool")
def parse_email_tool(email_body: str) -> dict:
    """
    Parse an email body using the local LLM and return structured JSON
    with fields like sender_role, project_title, meeting_topic, etc.
    """
    print("I am in parse_email_tool Function ")
    parsed = parse_email(email_body)
    print("✅ **********************Email parsed")
    print(parsed)
    print("✅ **********************Email parsed")
    return parsed

@tool("store_parsed_email")
def store_parsed_email(email_id: int, parsed_data: dict) -> dict:
    """
    Store parsed email JSON into the parsed_emails table in the database.
    Returns a dictionary with 'success' and 'parsed_id'.
    """
    from utils.database import setup_database
    
    print("✅ **********************Email parsed")
    print(parsed_data)
    print("✅ **********************Email parsed")

    def clean_value(val, boolean=False):
        if val in ["None", None]:
            return None
        if boolean:
            return bool(val)
        return val

    cleaned_data = {
        "sender_role": clean_value(parsed_data.get("sender_role")),
        "project_title": clean_value(parsed_data.get("project_title")),
        "meeting_topic": clean_value(parsed_data.get("meeting_topic")),
        "relation_type": clean_value(parsed_data.get("relation_type")),
        "meeting_date": clean_value(parsed_data.get("meeting_date")),
        "meeting_time": clean_value(parsed_data.get("meeting_time")),
        "duration": clean_value(parsed_data.get("duration")),
        "urgent": clean_value(parsed_data.get("urgent"), boolean=True),
        "tasks_requested": json.dumps(parsed_data.get("tasks_requested", [])),
        "documents_to_prepare": json.dumps(parsed_data.get("documents_to_prepare", [])),
        "confirmation_status": clean_value(parsed_data.get("confirmation_status"), boolean=True),
    }

    engine = setup_database()
    with engine.begin() as conn:
        result = conn.execute(
            text(
                """
                INSERT INTO meetings (
                    email_id,
                    sender_role,
                    project_title,
                    meeting_topic,
                    relation_type,
                    meeting_date,
                    meeting_time,
                    duration,
                    urgent,
                    tasks_requested,
                    documents_to_prepare,
                    confirmation_status,
                    stored_at
                )
                VALUES (
                    :email_id,
                    :sender_role,
                    :project_title,
                    :meeting_topic,
                    :relation_type,
                    :meeting_date,
                    :meeting_time,
                    :duration,
                    :urgent,
                    :tasks_requested,
                    :documents_to_prepare,
                    :confirmation_status,
                    :stored_at
                )
                RETURNING id
                """
            ),
            {
                "email_id": email_id,
                **cleaned_data,
                "stored_at": datetime.now(timezone.utc)
            }
        )
        stored_id = result.fetchone()[0]
    
    message = "the parsed data is stored successfully"
    return message

def create_email_parser_agent(llm):
    """Create the email parsing agent"""
    return Agent(
        role="Email Parsing Agent",
        goal="Parse one email body and store the structured data",
        backstory="You take an email body, parse it using the local LLM, then store the structured information in the database.",
        tools=[parse_email_tool, store_parsed_email],
        llm=llm,
        max_iterations=1,
        verbose=True
    )