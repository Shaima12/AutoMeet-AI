# 📅 AI-Powered Meeting Management System

<div align="center">

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![CrewAI](https://img.shields.io/badge/CrewAI-Latest-green.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

An intelligent meeting management system that automates email parsing, calendar scheduling, and provides AI-powered meeting preparation advice using multi-agent orchestration.

[Features](#-features) • [Architecture](#-architecture) • [Installation](#-installation) • [Usage](#-usage) • [Documentation](#-documentation)

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Architecture](#-architecture)
- [Technology Stack](#-technology-stack)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [Database Schema](#-database-schema)
- [API Documentation](#-api-documentation)
- [Dashboard](#-dashboard)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🌟 Overview

This system transforms how you manage meetings by automating the entire workflow from email reception to calendar scheduling, with AI-powered preparation assistance. It uses multiple specialized AI agents working together to handle different aspects of meeting management.

### What It Does

1. **📧 Email Processing**: Automatically fetches and parses meeting request emails
2. **🤖 AI Parsing**: Extracts structured information (date, time, topic, urgency, etc.)
3. **💡 Smart Advice**: Generates personalized tasks and strategic advice for each meeting
4. **📅 Calendar Integration**: Checks availability and schedules meetings in Google Calendar
5. **✉️ Email Notifications**: Sends professional confirmation emails automatically
6. **📊 Analytics Dashboard**: Visualizes meeting data and tracks task completion

---

## ✨ Features

### 🎯 Core Features

- **Intelligent Email Parsing**
  - Extracts meeting details using LLM (Groq/Ollama)
  - Identifies sender role, project context, urgency level
  - Parses dates, times, and duration automatically
  
- **Multi-Agent Orchestration**
  - Email Parser Agent: Structures incoming emails
  - Advisor Agent: Generates contextual advice and tasks
  - Calendar Agent: Manages scheduling and availability
  - Email Sender Agent: Handles notifications

- **Smart Scheduling**
  - Real-time Google Calendar availability checking
  - Automatic alternative slot suggestions
  - Business hours enforcement (Mon-Fri, 9 AM - 5 PM)
  - Timezone-aware scheduling (Africa/Tunis default)

- **Meeting Preparation Intelligence**
  - 5 personalized tasks per meeting
  - 5 strategic advice items per meeting
  - Context-aware recommendations based on:
    - Person relationship history
    - Project details
    - Previous meeting decisions
    - Sender role and urgency


### Dashboard Navigation

- **🏠 Overview**: High-level metrics and urgent meetings
- **🔥 Urgent Meetings**: Focus on this week's urgent meetings
- **📅 All Meetings**: Searchable meeting list
- **👥 Relationships**: Contact directory and analytics
- **✅ Recommendations**: Task and advice management
---
## 🏗️ Architecture

### System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Gmail Inbox                              │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Email Fetcher (Gmail API)                     │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Email Parser Agent (CrewAI)                    │
│  • Groq LLM (llama-3.1-8b-instant)                              │
│  • Extracts: sender_role, project, date, time, urgency, etc.   │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PostgreSQL Database                           │
│  Tables: emails, meetings, personnes, recommendations           │
└──────────────┬───────────────────────────┬──────────────────────┘
               │                           │
               ▼                           ▼
┌──────────────────────────┐   ┌─────────────────────────────────┐
│   Advisor Agent          │   │   Calendar Agent                 │
│  • Fetch person context  │   │  • Check availability            │
│  • Generate tasks/advice │   │  • Find alternatives             │
│  • Store recommendations │   │  • Create calendar events        │
└──────────────┬───────────┘   └─────────────┬───────────────────┘
               │                               │
               │                               ▼
               │                    ┌─────────────────────────────┐
               │                    │  Email Sender Agent         │
               │                    │  • Send confirmations       │
               │                    └─────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────────┐
│              Streamlit Dashboard (Visualization)                 │
│  • Overview • Urgent Meetings • Recommendations • Analytics     │
└─────────────────────────────────────────────────────────────────┘
```

### Agent Workflow

```
Email Received → Parse Email → Store Parsed Data
                                      ↓
                            Fetch Person Context
                                      ↓
                            Generate Advice & Tasks
                                      ↓
                            Store Recommendations
                                      ↓
                            Check Calendar Availability
                                      ↓
                    ┌─────────────────┴─────────────────┐
                    ▼                                   ▼
            Available: Create Event          Not Available: Find Alternatives
                    │                                   │
                    └─────────────────┬─────────────────┘
                                      ▼
                            Send Email Confirmation
```

---

## 🛠️ Technology Stack

### Backend
- **Python 3.9+**: Core programming language
- **CrewAI**: Multi-agent orchestration framework
- **Groq API**: Fast LLM inference (llama-3.1-8b-instant)
- **Ollama**: Local LLM option (qwen2.5:14b)
- **SQLAlchemy**: Database ORM
- **PostgreSQL**: Primary database (Supabase hosted)

### APIs & Integrations
- **Google Calendar API**: Calendar management
- **Gmail API**: Email fetching
- **SMTP**: Email sending (Gmail SMTP)

### Frontend
- **Streamlit**: Interactive dashboard
- **Plotly**: Data visualization
- **Pandas**: Data manipulation

### Tools & Libraries
- **python-dotenv**: Environment management
- **Pydantic**: Data validation
- **zoneinfo**: Timezone handling

---

## 📁 Project Structure

```
meeting-management-system/
│
├── agents/
│   ├── __init__.py
│   ├── email_parser_agent.py      # Email parsing agent with LLM
│   ├── advisor_agent.py            # Advice and task generation agent
│   └── calendar_agent.py           # Calendar scheduling agent
│
├── utils/
│   ├── __init__.py
│   ├── database.py                 # Database setup and operations
│   └── gmail_setup.py              # Gmail API authentication
│
├── main.py                         # Main orchestration script
├── dashboard.py                    # Streamlit dashboard
├── requirements.txt                # Python dependencies
├── .env                            # Environment variables (create this)
├── .env.example                    # Environment template
├── credentials.json                # Google OAuth credentials (create this)
├── token.json                      # Google OAuth token (auto-generated)
├── README.md                       # This file
└── LICENSE                         # MIT License
```

---
