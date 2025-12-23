import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
import json

# Page Configuration
st.set_page_config(
    page_title="Meeting Management Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Database Connection
@st.cache_resource

    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        connect_args={"sslmode": "require"}
    )
    return engine

engine = get_database_connection()

# Data Loading Functions
@st.cache_data(ttl=300)
def load_meetings():
    query = """
    SELECT 
        m.*,
        COALESCE(p1.name, p2.name, 'Unknown Contact') as person_name,
        COALESCE(p1.email, p2.email) as person_email,
        COALESCE(p1.company, p2.company, 'No Company') as company,
        COALESCE(p1.service, p2.service, 'General') as service,
        COALESCE(p1.project_description, p2.project_description) as project_description,
        COALESCE(p1.latest_decision, p2.latest_decision) as latest_decision
    FROM meetings m
    LEFT JOIN personnes p1 ON m.email_id = p1.id
    LEFT JOIN personnes p2 ON m.project_title = p2.project_title AND m.email_id != p2.id
    ORDER BY m.meeting_date DESC, m.meeting_time DESC
    """
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)
    return df

@st.cache_data(ttl=300)
def load_recommendations():
    query = """
    SELECT 
        r.id,
        r.email_id,
        r.project_title,
        r.type,
        r.content,
        r.completed,
        r.created_at,
        m.meeting_topic,
        m.meeting_date,
        m.meeting_time,
        p.name as person_name
    FROM recommendations r
    LEFT JOIN meetings m ON r.email_id = m.email_id
    LEFT JOIN personnes p ON r.project_title = p.project_title
    ORDER BY r.created_at DESC
    """
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)
    return df

@st.cache_data(ttl=300)
def load_personnes():
    query = "SELECT * FROM personnes ORDER BY name"
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)
    return df

def parse_meeting_date(date_str):
    """Parse various date formats to datetime"""
    if pd.isna(date_str) or date_str is None or date_str == '':
        return pd.NaT
    
    date_str = str(date_str).strip()
    
    # Try multiple date formats
    formats = [
        '%Y-%m-%d',
        '%d/%m/%Y',
        '%d %B %Y',
        '%d-%m-%Y',
        '%Y/%m/%d',
        '%d.%m.%Y',
    ]
    
    for fmt in formats:
        try:
            return pd.to_datetime(date_str, format=fmt)
        except:
            continue
    
    try:
        return pd.to_datetime(date_str, dayfirst=True)
    except:
        return pd.NaT

def get_urgent_meetings_this_week(df_meetings):
    """Get urgent meetings for current week"""
    if len(df_meetings) == 0:
        return pd.DataFrame()
    
    today = datetime.now().date()
    week_end = today + timedelta(days=7)
    
    df_meetings = df_meetings.copy()
    df_meetings['meeting_date_dt'] = df_meetings['meeting_date'].apply(parse_meeting_date)
    
    urgent_this_week = df_meetings[
        ((df_meetings['urgent'] == True) | (df_meetings['urgent'] == 't') | (df_meetings['urgent'] == 'true')) & 
        (df_meetings['meeting_date_dt'].notna()) &
        (df_meetings['meeting_date_dt'].dt.date >= today) &
        (df_meetings['meeting_date_dt'].dt.date <= week_end)
    ].copy()
    
    return urgent_this_week

def get_recommendations_for_meeting(email_id):
    """Get tasks and advices for a specific meeting"""
    query = """
    SELECT * FROM recommendations 
    WHERE email_id = %s
    ORDER BY type DESC, created_at DESC
    """
    with engine.connect() as conn:
        df = pd.read_sql(query, conn, params=(email_id,))
    return df

def update_task_completion(recommendation_id, completed):
    """Update task completion status"""
    query = """
    UPDATE recommendations 
    SET completed = %s 
    WHERE id = %s
    """
    with engine.begin() as conn:
        conn.execute(text(query), (completed, recommendation_id))

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .advice-item {
        padding: 10px;
        margin: 5px 0;
        border-left: 4px solid #2196F3;
        background: #e3f2fd;
        border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/calendar.png", width=80)
    st.title("📊 Dashboard")
    
    if 'view_switch' in st.session_state:
        default_view = st.session_state['view_switch']
        del st.session_state['view_switch']
    else:
        default_view = "🏠 Overview"
    
    view_option = st.radio(
        "Navigation",
        ["🏠 Overview", "🔥 Urgent Meetings", "📅 All Meetings", 
         "👥 Relationships", "✅ Recommendations", "📈 Analytics"],
        index=["🏠 Overview", "🔥 Urgent Meetings", "📅 All Meetings", 
               "👥 Relationships", "✅ Recommendations", "📈 Analytics"].index(default_view) if default_view in ["🏠 Overview", "🔥 Urgent Meetings", "📅 All Meetings", "👥 Relationships", "✅ Recommendations", "📈 Analytics"] else 0,
        label_visibility="collapsed"
    )
    
    st.divider()
    
    st.subheader("Filters")
    date_range = st.selectbox("Date Range", 
                              ["This Week", "This Month", "Last Month", "All Time"])
    
    relation_filter = st.multiselect(
        "Relation Type",
        ["client", "supplier", "collaborator"],
        default=["client", "supplier", "collaborator"]
    )
    
    confirmation_filter = st.multiselect(
        "Confirmation Status",
        ["confirmed", "pending", "cancelled"],
        default=["confirmed", "pending"]
    )
    
    st.divider()
    
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()

# Load Data
try:
    df_meetings = load_meetings()
    df_recommendations = load_recommendations()
    df_personnes = load_personnes()
    
    with st.sidebar:
        with st.expander("🔍 Debug Info"):
            st.write(f"Meetings loaded: {len(df_meetings)}")
            st.write(f"Recommendations loaded: {len(df_recommendations)}")
            st.write(f"Persons loaded: {len(df_personnes)}")
            if len(df_meetings) > 0:
                st.write(f"Urgent values: {df_meetings['urgent'].unique()}")
                st.write(f"Sample dates: {df_meetings['meeting_date'].head(3).tolist()}")
            
            st.write("--- Recommendations Debug ---")
            if len(df_recommendations) > 0:
                st.write("Sample recommendation data:")
                sample_rec = df_recommendations.iloc[0]
                st.write(f"Email ID: {sample_rec.get('email_id', 'N/A')}")
                st.write(f"Project Title: {sample_rec.get('project_title', 'N/A')}")
                st.write(f"Meeting Topic: {sample_rec.get('meeting_topic', 'N/A')}")
                st.write(f"Meeting Date: {sample_rec.get('meeting_date', 'N/A')}")
                st.write(f"Person Name: {sample_rec.get('person_name', 'N/A')}")
                
            st.write("--- Meetings Debug ---")
            if len(df_meetings) > 0:
                st.write("Sample meeting data:")
                sample_meet = df_meetings.iloc[0]
                st.write(f"Email ID: {sample_meet.get('email_id', 'N/A')}")
                st.write(f"Project Title: {sample_meet.get('project_title', 'N/A')}")
                st.write(f"Meeting Topic: {sample_meet.get('meeting_topic', 'N/A')}")
                st.write(f"Meeting Date: {sample_meet.get('meeting_date', 'N/A')}")
except Exception as e:
    st.error(f"Error loading data: {str(e)}")
    st.stop()

# Apply Filters
if relation_filter:
    df_meetings = df_meetings[df_meetings['relation_type'].isin(relation_filter)]
if confirmation_filter:
    df_meetings = df_meetings[df_meetings['confirmation_status'].isin(confirmation_filter)]

# Main Content
st.markdown('<h1 class="main-header">📊 Meeting Management Dashboard</h1>', unsafe_allow_html=True)

# ==================== OVERVIEW ====================
if view_option == "🏠 Overview":
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Meetings", len(df_meetings), "+5 this week")
    
    with col2:
        completed_recs = df_recommendations[df_recommendations['completed'] == True]
        completion_rate = (len(completed_recs) / len(df_recommendations) * 100) if len(df_recommendations) > 0 else 0
        st.metric("Task Completion", f"{completion_rate:.0f}%", "+12%")
    
    with col3:
        urgent_count = len(df_meetings[
            (df_meetings['urgent'] == True) | 
            (df_meetings['urgent'] == 't') | 
            (df_meetings['urgent'] == 'true')
        ])
        urgent_this_week = get_urgent_meetings_this_week(df_meetings.copy())
        urgent_week_count = len(urgent_this_week)
        st.metric("Urgent Meetings", urgent_count, f"🔥 {urgent_week_count} this week")
    
    st.divider()
    
    st.subheader("🔥 Urgent Meetings This Week")
    urgent_this_week = get_urgent_meetings_this_week(df_meetings.copy())
    
    if len(urgent_this_week) > 0:
        st.warning(f"⚠️ You have {len(urgent_this_week)} urgent meeting(s) this week")
        
        for idx in range(len(urgent_this_week)):
            row = urgent_this_week.iloc[idx]
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
            
            # Extract scalar values - get the actual value not Series
            person_name = row['person_name'] if isinstance(row['person_name'], str) else 'Unknown Contact'
            project_title = row['project_title'] if isinstance(row['project_title'], str) else 'No Project'
            meeting_date = row['meeting_date'] if isinstance(row['meeting_date'], str) else 'TBD'
            meeting_time = row['meeting_time'] if isinstance(row['meeting_time'], str) else 'TBD'
            meeting_topic = row['meeting_topic'] if isinstance(row['meeting_topic'], str) else 'General Meeting'
            
            try:
                meeting_id = int(row['id'])
            except:
                meeting_id = idx
            
            try:
                email_id = int(row['email_id'])
            except:
                email_id = None
            
            with col1:
                st.write(f"👤 **{person_name}** - {project_title}")
            
            with col2:
                st.write(f"📅 {meeting_date} at {meeting_time}")
            
            with col3:
                st.write(f"📋 {meeting_topic}")
            
            with col4:
                if st.button("View", key=f"overview_btn_{meeting_id}"):
                    st.session_state['selected_meeting_id'] = email_id
                    st.session_state['view_switch'] = '🔥 Urgent Meetings'
    else:
        st.success("✨ No urgent meetings scheduled for this week!")
    
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Meetings by Relation Type")
        relation_counts = df_meetings['relation_type'].value_counts().reset_index()
        relation_counts.columns = ['Relation Type', 'Count']
        
        fig = px.pie(relation_counts, values='Count', names='Relation Type',
                     color_discrete_sequence=px.colors.qualitative.Set3)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("📈 Meeting Trend (Last 30 Days)")
        df_temp = df_meetings.copy()
        df_temp['meeting_date_dt'] = df_temp['meeting_date'].apply(parse_meeting_date)
        df_temp = df_temp[df_temp['meeting_date_dt'].notna()].copy()
        df_temp['date_only'] = df_temp['meeting_date_dt'].dt.date
        
        trend_data = df_temp.groupby('date_only').size().reset_index(name='count')
        trend_data = trend_data.sort_values('date_only')
        
        if len(trend_data) > 0:
            fig = px.line(trend_data, x='date_only', y='count', 
                          labels={'date_only': 'Date', 'count': 'Meetings'},
                          markers=True)
            fig.update_traces(line_color='#667eea', line_width=3)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No meeting trend data available")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🏢 Meetings by Service")
        service_counts = df_meetings['service'].value_counts().head(10).reset_index()
        service_counts.columns = ['Service', 'Count']
        
        fig = px.bar(service_counts, x='Count', y='Service', orientation='h',
                     color='Count', color_continuous_scale='Viridis')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("✅ Confirmation Status")
        status_counts = df_meetings['confirmation_status'].value_counts().reset_index()
        status_counts.columns = ['Status', 'Count']
        
        colors = {'confirmed': '#4CAF50', 'pending': '#FFC107', 'cancelled': '#F44336'}
        fig = px.bar(status_counts, x='Status', y='Count',
                     color='Status', color_discrete_map=colors)
        st.plotly_chart(fig, use_container_width=True)

# ==================== URGENT MEETINGS ====================
elif view_option == "🔥 Urgent Meetings":
    st.header("🔥 Urgent Meetings This Week")
    
    urgent_meetings = get_urgent_meetings_this_week(df_meetings.copy())
    
    if len(urgent_meetings) == 0:
        st.success("✨ No urgent meetings scheduled for this week!")
    else:
        st.warning(f"⚠️ You have {len(urgent_meetings)} urgent meeting(s) this week")
        
        for idx in range(len(urgent_meetings)):
            row = urgent_meetings.iloc[idx]
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
                
                # Extract scalar values safely
                person_name = row['person_name'] if isinstance(row['person_name'], str) else 'Contact Unknown'
                project_title = row['project_title'] if isinstance(row['project_title'], str) else 'No Project'
                meeting_topic = row['meeting_topic'] if isinstance(row['meeting_topic'], str) else 'General Meeting'
                meeting_date = row['meeting_date'] if isinstance(row['meeting_date'], str) else 'Date TBD'
                meeting_time = row['meeting_time'] if isinstance(row['meeting_time'], str) else 'Time TBD'
                duration = row['duration'] if isinstance(row['duration'], str) else 'N/A'
                service = row['service'] if isinstance(row['service'], str) else 'General'
                relation_type = row['relation_type'] if isinstance(row['relation_type'], str) else 'unknown'
                
                try:
                    meeting_id = int(row['id'])
                except:
                    meeting_id = idx
                
                try:
                    email_id = int(row['email_id'])
                except:
                    email_id = None
                
                with col1:
                    st.markdown(f"### 👤 {person_name}")
                    st.write(f"**📁 Project:** {project_title}")
                    st.write(f"**📋 Topic:** {meeting_topic}")
                
                with col2:
                    st.write(f"📅 **Date:** {meeting_date}")
                    st.write(f"⏰ **Time:** {meeting_time}")
                
                with col3:
                    st.write(f"⏱️ **Duration:** {duration} min")
                    st.write(f"🏢 **Service:** {service}")
                
                with col4:
                    relation_emoji = {"client": "💼", "supplier": "🤝", "collaborator": "👥"}
                    st.write(f"{relation_emoji.get(relation_type, '📋')} {relation_type.title()}")
                    
                    if st.button(f"📝 View Tasks", key=f"btn_{meeting_id}"):
                        if email_id:
                            st.session_state['selected_meeting_id'] = email_id
                            st.session_state['selected_meeting_name'] = person_name
                            st.rerun()
                
                st.divider()
        
        if 'selected_meeting_id' in st.session_state and 'selected_meeting_name' in st.session_state:
            st.markdown("---")
            st.subheader(f"📋 Recommendations for {st.session_state['selected_meeting_name']}")
            
            recs = get_recommendations_for_meeting(st.session_state['selected_meeting_id'])
            
            if len(recs) > 0:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("### ✅ Tasks to Complete")
                    tasks = recs[recs['type'] == 'task']
                    
                    if len(tasks) > 0:
                        for idx, task in tasks.iterrows():
                            completed = st.checkbox(
                                task['content'],
                                value=task['completed'],
                                key=f"task_{task['id']}"
                            )
                            
                            if completed != task['completed']:
                                update_task_completion(task['id'], completed)
                                st.rerun()
                    else:
                        st.info("No tasks available")
                
                with col2:
                    st.markdown("### 💡 Advices")
                    advices = recs[recs['type'] == 'advice']
                    
                    if len(advices) > 0:
                        for idx, advice in advices.iterrows():
                            st.markdown(f"""
                            <div class="advice-item">
                                💡 {advice['content']}
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.info("No advices available")
            else:
                st.warning("No recommendations found for this meeting")

# ==================== ALL MEETINGS ====================
elif view_option == "📅 All Meetings":
    st.header("📅 All Meetings")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        search_term = st.text_input("🔍 Search by name, topic, or project", "")
    
    with col2:
        sort_by = st.selectbox("Sort by", ["Date", "Name", "Urgency"])
    
    with col3:
        show_urgent_only = st.checkbox("Show urgent only")
    
    filtered_df = df_meetings.copy()
    
    if search_term:
        mask = (
            filtered_df['person_name'].fillna('').str.contains(search_term, case=False) |
            filtered_df['meeting_topic'].fillna('').str.contains(search_term, case=False) |
            filtered_df['project_title'].fillna('').str.contains(search_term, case=False)
        )
        filtered_df = filtered_df[mask]
    
    if show_urgent_only:
        filtered_df = filtered_df[
            (filtered_df['urgent'] == True) | 
            (filtered_df['urgent'] == 't') | 
            (filtered_df['urgent'] == 'true')
        ]
    
    st.write(f"📊 Showing {len(filtered_df)} meeting(s)")
    
    if len(filtered_df) > 0:
        display_df = filtered_df[[
            'person_name', 'meeting_topic', 'project_title', 'meeting_date', 
            'meeting_time', 'duration', 'relation_type', 'confirmation_status', 'urgent'
        ]].copy()
        
        display_df.columns = ['Name', 'Topic', 'Project', 'Date', 'Time', 
                             'Duration', 'Relation', 'Status', 'Urgent']
        
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Urgent": st.column_config.CheckboxColumn("🔥 Urgent"),
                "Status": st.column_config.TextColumn("Status")
            }
        )
    else:
        st.info("No meetings found matching your criteria")

# ==================== RELATIONSHIPS ====================
elif view_option == "👥 Relationships":
    st.header("👥 Relationship Intelligence")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Contacts by Relation Type")
        relation_counts = df_personnes['relation_type'].value_counts().reset_index()
        relation_counts.columns = ['Relation Type', 'Count']
        
        fig = px.bar(relation_counts, x='Relation Type', y='Count',
                     color='Relation Type', 
                     color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("🏢 Top Companies")
        company_counts = df_personnes['company'].value_counts().head(10).reset_index()
        company_counts.columns = ['Company', 'Count']
        
        fig = px.pie(company_counts, values='Count', names='Company', hole=0.4)
        st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    st.subheader("📇 Contact Directory")
    
    selected_relation = st.selectbox(
        "Filter by relation type",
        ["All"] + list(df_personnes['relation_type'].unique())
    )
    
    filtered_personnes = df_personnes if selected_relation == "All" else df_personnes[df_personnes['relation_type'] == selected_relation]
    
    for idx, person in filtered_personnes.iterrows():
        with st.expander(f"👤 {person['name']} - {person['company']}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Email:** {person['email']}")
                st.write(f"**Role:** {person['role']}")
                st.write(f"**Service:** {person['service']}")
            
            with col2:
                st.write(f"**Relation:** {person['relation_type']}")
                st.write(f"**Project:** {person['project_title']}")
                st.write(f"**Latest Decision:** {person['latest_decision']}")

# ==================== RECOMMENDATIONS ====================
elif view_option == "✅ Recommendations":
    st.header("✅ Tasks & Advices Management")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_tasks = len(df_recommendations[df_recommendations['type'] == 'task'])
        st.metric("Total Tasks", total_tasks)
    
    with col2:
        completed_tasks = len(df_recommendations[
            (df_recommendations['type'] == 'task') & 
            (df_recommendations['completed'] == True)
        ])
        st.metric("Completed Tasks", completed_tasks)
    
    with col3:
        completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        st.metric("Completion Rate", f"{completion_rate:.0f}%")
    
    st.divider()
    
    all_projects = df_recommendations['project_title'].dropna().unique()
    selected_project = st.selectbox(
        "🔍 Filter by Project",
        ["All Projects"] + list(all_projects),
        key="project_filter"
    )
    
    if selected_project != "All Projects":
        filtered_recs = df_recommendations[df_recommendations['project_title'] == selected_project]
    else:
        filtered_recs = df_recommendations
    
    st.divider()
    
    projects = filtered_recs['project_title'].dropna().unique()
    
    if len(projects) == 0:
        st.info("No recommendations found")
    else:
        for project in projects:
            project_recs = filtered_recs[filtered_recs['project_title'] == project]
            
            project_tasks = project_recs[project_recs['type'] == 'task']
            project_advices = project_recs[project_recs['type'] == 'advice']
            completed_count = len(project_tasks[project_tasks['completed'] == True])
            total_count = len(project_tasks)
            
            with st.expander(
                f"📁 **{project}** - {completed_count}/{total_count} tasks completed | {len(project_advices)} advices",
                expanded=(selected_project != "All Projects")
            ):
                # Get meeting info from the first recommendation's linked meeting
                meeting_info = project_recs.iloc[0]
                
                # Get proper meeting details - now from the joined data
                meeting_date = meeting_info['meeting_date'] if pd.notna(meeting_info['meeting_date']) else 'Date not set'
                meeting_time = meeting_info['meeting_time'] if pd.notna(meeting_info['meeting_time']) else ''
                meeting_topic = meeting_info['meeting_topic'] if pd.notna(meeting_info['meeting_topic']) else 'No topic'
                person_name = meeting_info['person_name'] if pd.notna(meeting_info['person_name']) else 'Unknown'
                
                st.markdown(f"**Tasks & Advices for meeting about '{meeting_topic}' for project '{project}'**")
                st.markdown(f"**Date:** {meeting_date} {meeting_time} | **Contact:** {person_name}")
                st.divider()
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("### ✅ Tasks")
                    
                    if len(project_tasks) > 0:
                        pending = project_tasks[project_tasks['completed'] == False]
                        if len(pending) > 0:
                            st.markdown("**⏳ Pending:**")
                            for idx, task in pending.iterrows():
                                completed = st.checkbox(
                                    task['content'],
                                    value=False,
                                    key=f"task_{task['id']}_{project}"
                                )
                                
                                if completed:
                                    update_task_completion(task['id'], True)
                                    st.rerun()
                        
                        completed_tasks_list = project_tasks[project_tasks['completed'] == True]
                        if len(completed_tasks_list) > 0:
                            st.markdown("**✅ Completed:**")
                            for idx, task in completed_tasks_list.iterrows():
                                st.markdown(f"~~{task['content']}~~ ✓")
                    else:
                        st.info("No tasks for this project")
                
                with col2:
                    st.markdown("### 💡 Advices")
                    
                    if len(project_advices) > 0:
                        for idx, advice in project_advices.iterrows():
                            st.markdown(f"""
                            <div style="padding: 10px; margin: 5px 0; border-left: 4px solid #2196F3; background: #e3f2fd; border-radius: 4px;">
                                💡 {advice['content']}
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.info("No advices for this project")
                
                st.divider()
                
                if total_count > 0:
                    progress = completed_count / total_count
                    st.progress(progress, text=f"Progress: {completed_count}/{total_count} tasks ({progress*100:.0f}%)")
                else:
                    st.progress(0, text="No tasks to track")

# ==================== ANALYTICS ====================
elif view_option == "📈 Analytics":
    st.header("📈 Advanced Analytics")
    
    st.subheader("🗓️ Meeting Distribution Heatmap")
    
    df_temp = df_meetings.copy()
    df_temp['meeting_date_dt'] = df_temp['meeting_date'].apply(parse_meeting_date)
    df_temp = df_temp[df_temp['meeting_date_dt'].notna()].copy()
    df_temp['day_of_week'] = df_temp['meeting_date_dt'].dt.day_name()
    df_temp['hour'] = pd.to_datetime(df_temp['meeting_time'], format='%H:%M', errors='coerce').dt.hour
    
    heatmap_data = df_temp.groupby(['day_of_week', 'hour']).size().reset_index(name='count')
    heatmap_pivot = heatmap_data.pivot(index='day_of_week', columns='hour', values='count').fillna(0)
    
    fig = px.imshow(heatmap_pivot, 
                    labels=dict(x="Hour of Day", y="Day of Week", color="Meetings"),
                    color_continuous_scale="Blues")
    st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Project Engagement")
        project_data = df_meetings['project_title'].dropna()
        if len(project_data) > 0:
            project_counts = project_data.value_counts().head(10)
            project_df = pd.DataFrame({
                'Project': project_counts.index,
                'Meetings': project_counts.values
            })
            fig = px.bar(project_df, x='Meetings', y='Project', orientation='h',
                         color='Meetings', color_continuous_scale='Teal')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No project data available")
    
    with col2:
        st.subheader("⏱️ Average Meeting Duration by Service")
        df_temp = df_meetings.copy()
        df_temp['duration_num'] = df_temp['duration'].astype(str).str.extract('(\d+)').astype(float)
        avg_duration = df_temp.groupby('service')['duration_num'].mean().sort_values(ascending=False).head(10)
        
        if len(avg_duration) > 0:
            duration_df = pd.DataFrame({
                'Service': avg_duration.index,
                'Avg Duration (min)': avg_duration.values
            })
            fig = px.bar(duration_df, x='Avg Duration (min)', y='Service', orientation='h',
                         color='Avg Duration (min)', color_continuous_scale='Oranges')
            st.plotly_chart(fig, use_container_width=True)
        else:

            st.info("No duration data available")
