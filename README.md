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

### 📊 Dashboard Features

- **Overview Dashboard**
  - Total meetings and completion metrics
  - Urgent meetings this week
  - Meeting trends and analytics
  - Service and relation type distribution

- **Urgent Meetings View**
  - Filtered view of urgent meetings
  - Quick access to tasks and advice
  - Interactive task completion tracking

- **Recommendations Management**
  - Project-grouped task organization
  - Progress tracking per project
  - Advice repository
  - Completion rate visualization

- **Relationship Intelligence**
  - Contact directory with full context
  - Company and service analytics
  - Relation type distribution
  - Historical decision tracking

- **Advanced Analytics**
  - Meeting distribution heatmaps
  - Project engagement metrics
  - Average duration by service
  - Custom date range filtering

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

## 📦 Installation

### Prerequisites

- Python 3.9 or higher
- PostgreSQL database (or Supabase account)
- Google Cloud Platform account (for Calendar/Gmail APIs)
- Groq API key
- Gmail account with App Password

### Step 1: Clone Repository

```bash
git clone https://github.com/yourusername/meeting-management-system.git
cd meeting-management-system
```

### Step 2: Create Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### Step 3: Install Dependencies

Create a `requirements.txt` file with these dependencies:

```txt
# Core Framework
crewai==0.28.0
crewai-tools==0.1.6

# LLM Providers
groq==0.4.2
langchain-groq==0.1.3

# Database
sqlalchemy==2.0.25
psycopg2-binary==2.9.9

# Google APIs
google-auth==2.27.0
google-auth-oauthlib==1.2.0
google-auth-httplib2==0.2.0
google-api-python-client==2.116.0

# Web Framework
streamlit==1.31.0
plotly==5.18.0
pandas==2.2.0

# Utilities
python-dotenv==1.0.0
pydantic==2.6.0
python-dateutil==2.8.2

# Email
secure-smtplib==0.1.1
```

Then install:

```bash
pip install -r requirements.txt
```

### Step 4: Set Up Google Cloud APIs

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable **Google Calendar API** and **Gmail API**
4. Create OAuth 2.0 credentials
5. Download credentials as `credentials.json`
6. Place in project root directory

### Step 5: Configure Environment Variables

Create a `.env` file in the project root:

```env
# Database
DATABASE_URL=postgresql+psycopg2://user:password@host:port/database

# Email Configuration
SENDER_EMAIL=your-email@gmail.com
EMAIL_APP_PASSWORD=your-app-password

# API Keys
GROQ_API_KEY=your-groq-api-key
```

### Step 6: Initialize Database

```python
from utils.database import setup_database
engine = setup_database()
```

The database schema will be created automatically.

### Step 7: Authenticate Google APIs

```bash
python utils/gmail_setup.py
```

This will open a browser for OAuth authentication and create `token.json`.

---

## ⚙️ Configuration

### Email Configuration

Update `main.py` with your email settings:

```python
EMAIL_CONFIG = {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "sender_email": "your-email@gmail.com",
    "sender_password": "your-app-password",
    "sender_name": "Your Name"
}
```

### LLM Configuration

Choose your LLM provider in `main.py`:

```python
# Option 1: Groq (Fast, Cloud)
llm = LLM(
    model="groq/llama-3.1-8b-instant",
    temperature=0.1,
    max_tokens=500
)

# Option 2: Ollama (Local)
llm = LLM(
    model="ollama/qwen2.5:14b",
    temperature=0.1,
    max_tokens=4000,
    provider="ollama"
)
```

### Timezone Configuration

Default timezone is `Africa/Tunis`. Change in `agents/calendar_agent.py`:

```python
timezone: str = Field(default="Your/Timezone")
```

---

## 🚀 Usage

### Running the Main Orchestration

Process incoming emails and schedule meetings:

```bash
python main.py
```

This will:
1. Fetch the latest unread email
2. Parse and extract meeting details
3. Generate personalized advice and tasks
4. Check calendar availability
5. Schedule meeting or suggest alternatives
6. Send confirmation email

### Running the Dashboard

Launch the interactive dashboard:

```bash
streamlit run dashboard.py
```

Access at: `http://localhost:8501`

### Dashboard Navigation

- **🏠 Overview**: High-level metrics and urgent meetings
- **🔥 Urgent Meetings**: Focus on this week's urgent meetings
- **📅 All Meetings**: Searchable meeting list
- **👥 Relationships**: Contact directory and analytics
- **✅ Recommendations**: Task and advice management
- **📈 Analytics**: Advanced visualizations

---

## 🗄️ Database Schema

### Tables

#### `emails`
```sql
CREATE TABLE emails (
    id SERIAL PRIMARY KEY,
    sender_email VARCHAR(255),
    sender_name VARCHAR(255),
    subject TEXT,
    body TEXT,
    received_at TIMESTAMP,
    processed BOOLEAN DEFAULT FALSE
);
```

#### `meetings`
```sql
CREATE TABLE meetings (
    id SERIAL PRIMARY KEY,
    email_id INTEGER REFERENCES emails(id),
    sender_role VARCHAR(100),
    project_title VARCHAR(255),
    meeting_topic TEXT,
    relation_type VARCHAR(100),
    meeting_date VARCHAR(50),
    meeting_time VARCHAR(20),
    duration VARCHAR(20),
    urgent BOOLEAN,
    tasks_requested JSONB,
    documents_to_prepare JSONB,
    confirmation_status VARCHAR(50),
    stored_at TIMESTAMP
);
```

#### `personnes`
```sql
CREATE TABLE personnes (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    email VARCHAR(255) UNIQUE,
    role VARCHAR(100),
    service VARCHAR(100),
    company VARCHAR(255),
    relation_type VARCHAR(100),
    project_title VARCHAR(255),
    project_description TEXT,
    latest_decision TEXT
);
```

#### `recommendations`
```sql
CREATE TABLE recommendations (
    id SERIAL PRIMARY KEY,
    email_id INTEGER REFERENCES emails(id),
    project_title VARCHAR(255),
    type VARCHAR(20), -- 'task' or 'advice'
    content TEXT,
    completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP
);
```

---

## 📚 API Documentation

### Email Parser Agent

**Tools:**
- `parse_email_tool(email_body: str) -> dict`: Parses email and returns structured JSON
- `store_parsed_email(email_id: int, parsed_data: dict) -> dict`: Stores parsed data in database

**Output Schema:**
```python
{
    "sender_role": str,
    "project_title": str,
    "meeting_topic": str,
    "relation_type": str,
    "meeting_date": str,
    "meeting_time": str,
    "duration": str,
    "urgent": bool,
    "tasks_requested": list,
    "documents_to_prepare": list,
    "confirmation_status": str
}
```

### Advisor Agent

**Tools:**
- `fetch_person_context(sender_email: str) -> dict`: Retrieves person and project information
- `generate_advice(parsed_email: dict, person_context: dict) -> dict`: Generates tasks and advice
- `store_advice(email_id: int, project_title: str, tasks: list, advice: list) -> str`: Stores recommendations

**Output Schema:**
```python
{
    "tasks": [str, str, str, str, str],  # 5 tasks
    "advice": [str, str, str, str, str]  # 5 advice items
}
```

### Calendar Agent

**Tools:**
- `check_calendar_availability(start_time: str, end_time: str, timezone: str) -> str`
- `find_alternative_slots(start_date: str, duration_hours: float, days_ahead: int, timezone: str) -> str`
- `create_calendar_event(summary: str, start_time: str, end_time: str, description: str, attendees: str, timezone: str) -> str`
- `send_email(recipient: str, subject: str, body: str, meeting_details: str) -> str`

---

## 📊 Dashboard

### Overview Page
![Dashboard Overview](https://via.placeholder.com/800x400?text=Dashboard+Overview)

### Features:
- **Metrics Cards**: Total meetings, task completion rate, urgent meetings
- **Urgent Meetings Widget**: Quick access to this week's urgent meetings
- **Charts**: 
  - Meeting distribution by relation type (pie chart)
  - 30-day meeting trend (line chart)
  - Meetings by service (bar chart)
  - Confirmation status (bar chart)

### Urgent Meetings Page
- Filtered view of urgent meetings for current week
- Expandable cards with full meeting details
- Direct access to tasks and advice
- Real-time task completion tracking

### Recommendations Page
- Project-based organization
- Task checkboxes with persistence
- Advice display with custom styling
- Progress bars per project

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/AmazingFeature
   ```
3. **Commit your changes**
   ```bash
   git commit -m 'Add some AmazingFeature'
   ```
4. **Push to the branch**
   ```bash
   git push origin feature/AmazingFeature
   ```
5. **Open a Pull Request**

### Development Guidelines

- Follow PEP 8 style guide
- Add docstrings to all functions
- Include type hints
- Write unit tests for new features
- Update documentation

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **CrewAI** for the multi-agent framework
- **Groq** for fast LLM inference
- **Anthropic** for Claude API integration concepts
- **Streamlit** for the amazing dashboard framework
- **Google** for Calendar and Gmail APIs

---

## 📞 Support

For issues, questions, or suggestions:

- 📧 Email: support@yourproject.com
- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/meeting-management-system/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/yourusername/meeting-management-system/discussions)

---

## 🗺️ Roadmap

- [ ] Multi-language support
- [ ] Slack integration
- [ ] Microsoft Teams calendar support
- [ ] Mobile app
- [ ] Voice-to-meeting scheduling
- [ ] AI-powered meeting summaries
- [ ] Zoom/Meet link generation
- [ ] Recurring meeting support
- [ ] Meeting notes and action items tracking
- [ ] Integration with project management tools (Jira, Asana)

---

<div align="center">

**[⬆ Back to Top](#-ai-powered-meeting-management-system)**

Made with ❤️ by Your Team

</div>
