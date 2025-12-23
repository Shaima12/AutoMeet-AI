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

import signal
import json
import os
import re
from datetime import datetime, timezone
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

from crewai import Agent
from crewai.tools import tool
from groq import Client
from sqlalchemy import text

# Initialize Groq client
client = Client(api_key="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")

def generate(prompt, max_tokens=800):
    """Generate text using Groq LLM"""
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=max_tokens
    )
    return response.choices[0].message.content

@tool("fetch_person_context")
def fetch_person_context(sender_email: str) -> dict:
    """
    Fetch person context from database by email.
    Returns person information and project details.
    """
    from utils.database import setup_database
    
    print(f"🔍 Fetching person context for: {sender_email}")
    
    engine = setup_database()
    with engine.begin() as conn:
        result = conn.execute(
            text("""
                SELECT 
                    name, 
                    email, 
                    role, 
                    service, 
                    company, 
                    relation_type, 
                    project_title, 
                    project_description, 
                    latest_decision
                FROM personnes
                WHERE email = :email
                LIMIT 1
            """),
            {"email": sender_email}
        )
        row = result.fetchone()
    
    if not row:
        print(f"⚠️ No person found for {sender_email}")
        return {
            "name": "Unknown",
            "email": sender_email,
            "role": "Unknown",
            "service": "Unknown",
            "company": "Unknown",
            "relation_type": "Unknown",
            "project_title": "Unknown Project",
            "project_description": "No description available",
            "latest_decision": "No previous decisions recorded"
        }
    
    person_data = {
        "name": row[0],
        "email": row[1],
        "role": row[2],
        "service": row[3],
        "company": row[4],
        "relation_type": row[5],
        "project_title": row[6],
        "project_description": row[7],
        "latest_decision": row[8]
    }
    
    print(f"✅ Person context fetched: {person_data['name']} ({person_data['role']})")
    return person_data

@tool("generate_advice")
def generate_advice(parsed_email: dict, person_context: dict) -> dict:
    """
    Generate 5 tasks and 5 advice based on parsed email and person context.
    Returns structured advice and tasks.
    """
    print("🧠 Generating advice and tasks...")
    
    prompt = f"""
You are a senior executive advisor for a business owner.

Your role is to help prepare for an upcoming meeting using:
- The meeting request extracted from the email
- Context about the person and the ongoing project

========================
MEETING CONTEXT (JSON)
========================
{json.dumps(parsed_email, indent=2)}

========================
PERSON & PROJECT CONTEXT
========================
Name: {person_context["name"]}
Role: {person_context["role"]}
Service / Position: {person_context["service"]}
Project Title: {person_context["project_title"]}
Project Description: {person_context["project_description"]}
Latest Decision from Last Meeting: {person_context["latest_decision"]}

========================
YOUR TASK
========================
Analyze all the information and provide **clear, practical, and business-relevant guidance**.

OUTPUT STRICTLY IN THIS FORMAT (no extra text, no markdown):

TASKS:
- [Task 1: specific action item]
- [Task 2: specific action item]
- [Task 3: specific action item]
- [Task 4: specific action item]
- [Task 5: specific action item]

ADVICE:
- [Advice 1: strategic recommendation]
- [Advice 2: strategic recommendation]
- [Advice 3: strategic recommendation]
- [Advice 4: strategic recommendation]
- [Advice 5: strategic recommendation]

RULES:
- Be concise and actionable
- Avoid generic advice
- Base your reasoning on meeting type, urgency, project context, role expectations, and latest decision
- Each task should be a concrete preparation action
- Each advice should be a strategic insight for meeting success
"""
    
    output = generate(prompt, max_tokens=800)
    print("✅ Advice generated")
    
    # Parse the output
    parsed = parse_advisor_output(output)
    return parsed

def parse_advisor_output(llm_output: str) -> dict:
    """
    Parse the LLM output to extract tasks and advice.
    """
    def extract_section(section_name):
        pattern = rf"{section_name}:\s*\n(.*?)(?=\n[A-Z]+:|\Z)"
        match = re.search(pattern, llm_output, re.S | re.I)
        
        if not match:
            return []
        
        section_text = match.group(1).strip()
        lines = section_text.split("\n")
        items = []
        
        for line in lines:
            line = line.strip()
            if line.startswith("-"):
                line = line[1:].strip()
            if line:
                items.append(line)
        
        return items[:5]  # Limit to 5 items
    
    tasks = extract_section("TASKS")
    advice = extract_section("ADVICE")
    
    # Ensure we have exactly 5 of each
    while len(tasks) < 5:
        tasks.append("Review meeting materials")
    while len(advice) < 5:
        advice.append("Stay focused on meeting objectives")
    
    return {
        "tasks": tasks[:5],
        "advice": advice[:5]
    }

@tool("store_advice")
def store_advice(email_id: int, project_title: str, tasks: list, advice: list) -> str:
    """
    Store tasks and advice in the recommendations table.
    Each task and advice is stored as a separate row.
    """
    from utils.database import setup_database
    
    print(f"💾 Storing {len(tasks)} tasks and {len(advice)} advice items...")
    
    engine = setup_database()
    stored_count = 0
    
    with engine.begin() as conn:
        # Store tasks
        for task in tasks:
            conn.execute(
                text("""
                    INSERT INTO recommendations (
                        email_id, 
                        project_title, 
                        type, 
                        content, 
                        created_at
                    )
                    VALUES (:email_id, :project_title, :type, :content, :created_at)
                """),
                {
                    "email_id": email_id,
                    "project_title": project_title,
                    "type": "task",
                    "content": task,
                    "created_at": datetime.now(timezone.utc)
                }
            )
            stored_count += 1
        
        # Store advice
        for adv in advice:
            conn.execute(
                text("""
                    INSERT INTO recommendations (
                        email_id, 
                        project_title, 
                        type, 
                        content, 
                        created_at
                    )
                    VALUES (:email_id, :project_title, :type, :content, :created_at)
                """),
                {
                    "email_id": email_id,
                    "project_title": project_title,
                    "type": "advice",
                    "content": adv,
                    "created_at": datetime.now(timezone.utc)
                }
            )
            stored_count += 1
    
    print(f"✅ Stored {stored_count} recommendations")
    return f"Successfully stored {len(tasks)} tasks and {len(advice)} advice items"

def create_advisor_agent(llm):
    """Create the advisor agent"""
    return Agent(
        role="Meeting Advisor",
        goal="Fetch person context, generate strategic advice and actionable tasks, then store them",
        backstory=(
            "You are a senior business advisor who helps executives prepare for meetings. "
            "You analyze meeting requests, understand project context, and provide "
            "actionable tasks and strategic advice to ensure meeting success."
        ),
        tools=[fetch_person_context, generate_advice, store_advice],
        llm=llm,
        max_iterations=15,
        verbose=True,
        allow_delegation=False
    )