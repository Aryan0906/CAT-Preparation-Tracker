import os
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import sqlite3

# Comment out Google Sheets integration for now
# import gspread
# from oauth2client.service_account import ServiceAccountCredentials

from utils import (
    save_lecture_notes,
    save_flashcard,
    save_question,
    save_notes,
    save_study_session,
    save_progress,
    save_settings,
    save_timer_session
)

# Comment out Google Sheets integration for now
# from config import get_sheet_client, setup_google_sheets

# Set page configuration
st.set_page_config(
    page_title="CAT Preparation Tracker",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Comment out Google Sheets integration for now
# def init_gsheets():
#     try:
#         # Check if credentials.json exists
#         if not os.path.exists('credentials.json'):
#             # Create a placeholder credentials file for demonstration
#             st.warning("credentials.json not found. Creating a placeholder file.")
#             with open('credentials.json', 'w') as f:
#                 f.write('{"type": "service_account", "project_id": "placeholder", "private_key_id": "placeholder", "private_key": "placeholder", "client_email": "placeholder@example.com", "client_id": "placeholder", "auth_uri": "https://accounts.google.com/o/oauth2/auth", "token_uri": "https://oauth2.googleapis.com/token", "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs", "client_x509_cert_url": "placeholder"}')
#             st.info("Please configure Google Sheets in the Settings page.")
#             return None
#
#         sheet = get_sheet_client()
#         if sheet is None:
#             st.error("Google Sheets connection not configured. Using local storage instead.")
#             return None
#         return sheet
#     except Exception as e:
#         st.error(f"Error initializing Google Sheets: {str(e)}")
#         return None

# Enhanced Database initialization
def init_db(reset=False):
    conn = sqlite3.connect('cat_prep.db')
    c = conn.cursor()

    # Drop all tables if reset is True
    if reset:
        # Get all table names from the database
        c.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [table[0] for table in c.fetchall()]

        # Drop all tables
        for table in tables:
            c.execute(f"DROP TABLE IF EXISTS {table}")

        conn.commit()
        st.success("All data has been reset to zero!")

    # Progress tracking table
    c.execute('''CREATE TABLE IF NOT EXISTS progress
                 (date TEXT, section TEXT, topic TEXT, subtopic TEXT, score REAL)''')

    # Study log table - Ensure the date column exists
    # First check if the table exists
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='study_log'")
    if c.fetchone() is None:
        # Create the table with the correct schema
        c.execute('''CREATE TABLE IF NOT EXISTS study_log
                     (date TEXT, topic TEXT, subtopic TEXT, time_spent INTEGER, notes TEXT)''')
    else:
        # Check if the date column exists
        c.execute("PRAGMA table_info(study_log)")
        columns = [info[1] for info in c.fetchall()]
        if 'date' not in columns:
            # Add the date column if it doesn't exist
            c.execute("ALTER TABLE study_log ADD COLUMN date TEXT")
        if 'subtopic' not in columns:
            # Add the subtopic column if it doesn't exist
            c.execute("ALTER TABLE study_log ADD COLUMN subtopic TEXT")

    # Flashcards table
    c.execute('''CREATE TABLE IF NOT EXISTS flashcards
                 (word TEXT, definition TEXT, usage TEXT, category TEXT, mastered BOOLEAN, date TEXT)''')

    # Questions table
    c.execute('''CREATE TABLE IF NOT EXISTS questions
                 (date TEXT, question TEXT, answer TEXT, topic TEXT, difficulty TEXT, correct INTEGER DEFAULT 0)''')

    # Notes table
    c.execute('''CREATE TABLE IF NOT EXISTS notes
                 (date TEXT, title TEXT, content TEXT, tags TEXT)''')

    # Productivity settings table
    c.execute('''CREATE TABLE IF NOT EXISTS productivity_settings
                 (user_id TEXT, focus_duration INTEGER DEFAULT 25, break_duration INTEGER DEFAULT 5,
                  reminder_frequency TEXT, notification_enabled BOOLEAN DEFAULT 0,
                  daily_goal INTEGER DEFAULT 120, reminder_time TEXT DEFAULT '09:00')''')

    # Timer logs table
    c.execute('''CREATE TABLE IF NOT EXISTS timer_logs
                 (date TEXT, start_time TEXT, end_time TEXT, duration INTEGER,
                  completed BOOLEAN, topic TEXT)''')

    conn.commit()
    return conn

def show_dashboard():
    # Create a modern header with gradient background and CAT logo
    st.markdown("""
    <style>
    /* Global Color Scheme */
    :root {
        --primary-color: #4F46E5; /* Indigo */
        --primary-light: #818CF8;
        --primary-dark: #3730A3;
        --secondary-color: #06B6D4; /* Cyan */
        --secondary-light: #67E8F9;
        --secondary-dark: #0E7490;
        --accent-color: #F97316; /* Orange */
        --accent-light: #FB923C;
        --accent-dark: #C2410C;
        --success-color: #10B981; /* Emerald */
        --warning-color: #F59E0B; /* Amber */
        --danger-color: #EF4444; /* Red */
        --neutral-50: #F8FAFC;
        --neutral-100: #F1F5F9;
        --neutral-200: #E2E8F0;
        --neutral-300: #CBD5E1;
        --neutral-400: #94A3B8;
        --neutral-500: #64748B;
        --neutral-600: #475569;
        --neutral-700: #334155;
        --neutral-800: #1E293B;
        --neutral-900: #0F172A;
    }

    /* Apply custom fonts */
    body {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
    }

    /* Dashboard header */
    .dashboard-header {
        background: linear-gradient(90deg, var(--primary-dark) 0%, var(--primary-color) 100%);
        padding: 20px;
        border-radius: 12px;
        color: white;
        margin-bottom: 25px;
        display: flex;
        align-items: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .logo-container {
        margin-right: 20px;
        background: white;
        border-radius: 50%;
        width: 70px;
        height: 70px;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    .header-text {
        flex-grow: 1;
    }
    .header-title {
        font-size: 28px;
        font-weight: bold;
        margin: 0;
        padding: 0;
        color: #ffffff;
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
    }
    .header-subtitle {
        font-size: 14px;
        margin-top: 5px;
        color: #E0E7FF;
        text-shadow: 0 1px 1px rgba(0, 0, 0, 0.05);
    }
    </style>

    <div class="dashboard-header">
        <div class="logo-container">
            <img src="https://upload.wikimedia.org/wikipedia/en/thumb/9/95/CAT_logo.png/220px-CAT_logo.png" width="50">
        </div>
        <div class="header-text">
            <h1 class="header-title">CAT Preparation Dashboard</h1>
            <p class="header-subtitle">Your personal companion for CAT exam success</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Add a reset button in the sidebar
    if st.sidebar.button("Reset All Data to Zero"):
        conn = init_db(reset=True)
        c = conn.cursor()
    else:
        # Initialize database connection
        conn = init_db()
        c = conn.cursor()

    # Add custom CSS for modern cards
    st.markdown("""
    <style>
    .metric-section {
        margin-bottom: 30px;
    }
    .section-header {
        display: flex;
        align-items: center;
        margin-bottom: 15px;
        background: var(--neutral-50);
        padding: 10px 15px;
        border-radius: 8px;
        border-left: 4px solid var(--primary-color);
    }
    .section-icon {
        margin-right: 10px;
    }
    .section-title {
        font-size: 18px;
        font-weight: 600;
        color: var(--primary-color);
        margin: 0;
        letter-spacing: -0.3px;
        text-shadow: 0 1px 1px rgba(255, 255, 255, 0.8);
    }
    .metrics-container {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 15px;
    }
    .metric-card {
        background: white;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }
    .metric-title {
        font-size: 14px;
        color: var(--neutral-600);
        margin-bottom: 8px;
        font-weight: 500;
    }
    .metric-value {
        font-size: 24px;
        font-weight: bold;
        margin-bottom: 5px;
        color: var(--neutral-800);
        letter-spacing: -0.5px;
    }
    .metric-subtitle {
        font-size: 12px;
        font-weight: 500;
    }
    .progress-bar {
        height: 6px;
        background: var(--neutral-200);
        border-radius: 3px;
        margin-top: 10px;
        overflow: hidden;
    }
    .progress-value {
        height: 100%;
        border-radius: 3px;
    }
    </style>

    <div class="metric-section" background="lightblue">
        <div class="section-header" >
            <img src="https://cdn-icons-png.flaticon.com/512/3652/3652191.png" width="24" class="section-icon"   >
            <h2 class="section-title" background="lightblue" >Study Progress</h2>
        </div>
        <div class="metrics-container" background="lightblue">
    """, unsafe_allow_html=True)

    # We'll use these columns for the backend calculations, but display using custom HTML
    col1, col2, col3, col4 = st.columns(4)

    # Get actual metrics from database with error handling
    # Count watched lectures
    try:
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='videos'")
        if c.fetchone():
            try:
                c.execute("SELECT COUNT(*) FROM videos WHERE watched = 1")
                watched_lectures = c.fetchone()[0] or 0
                c.execute("SELECT COUNT(*) FROM videos")
                total_lectures = c.fetchone()[0] or 1  # Avoid division by zero
            except sqlite3.OperationalError:
                # If watched column doesn't exist
                c.execute("SELECT COUNT(*) FROM videos")
                total_lectures = c.fetchone()[0] or 0
                watched_lectures = 0
        else:
            total_lectures = 0
            watched_lectures = 0
    except sqlite3.OperationalError:
        total_lectures = 0
        watched_lectures = 0

    lecture_percentage = round((watched_lectures / total_lectures) * 100) if total_lectures > 0 else 0

    # Count mastered flashcards with error handling
    try:
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='flashcards'")
        if c.fetchone():
            c.execute("SELECT COUNT(*) FROM flashcards WHERE mastered = 1")
            mastered_count = c.fetchone()[0] or 0
            c.execute("SELECT COUNT(*) FROM flashcards")
            total_flashcards = c.fetchone()[0] or 1  # Avoid division by zero
        else:
            mastered_count = 0
            total_flashcards = 0
    except sqlite3.OperationalError:
        mastered_count = 0
        total_flashcards = 0

    mastery_percentage = round((mastered_count / total_flashcards) * 100) if total_flashcards > 0 else 0

    # Count practice questions with error handling
    try:
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='questions'")
        if c.fetchone():
            c.execute("SELECT COUNT(*) FROM questions WHERE correct = 1")
            correct_count = c.fetchone()[0] or 0
            c.execute("SELECT COUNT(*) FROM questions")
            total_questions = c.fetchone()[0] or 1  # Avoid division by zero
        else:
            correct_count = 0
            total_questions = 0
    except sqlite3.OperationalError:
        correct_count = 0
        total_questions = 0

    question_percentage = round((correct_count / total_questions) * 100) if total_questions > 0 else 0

    # Calculate study hours with error handling
    try:
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='study_log'")
        if c.fetchone():
            c.execute("SELECT SUM(time_spent) FROM study_log")
            minutes = c.fetchone()[0] or 0

            # Get today's study time
            today = datetime.now().strftime('%Y-%m-%d')
            c.execute("SELECT SUM(time_spent) FROM study_log WHERE date = ?", (today,))
            today_minutes = c.fetchone()[0] or 0
        else:
            minutes = 0
            today_minutes = 0
    except sqlite3.OperationalError:
        minutes = 0
        today_minutes = 0

    study_hours = round(minutes / 60, 1)

    # Get yesterday's study time for delta with error handling
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    try:
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='study_log'")
        if c.fetchone():
            c.execute("SELECT SUM(time_spent) FROM study_log WHERE date = ?", (yesterday,))
            yesterday_minutes = c.fetchone()[0] or 0
        else:
            yesterday_minutes = 0
    except sqlite3.OperationalError:
        yesterday_minutes = 0

    today_delta = today_minutes - yesterday_minutes

    # Display metrics with modern card design
    # Lectures card
    lecture_progress_color = "var(--primary-color)" # Indigo
    lecture_card = f"""
    <div class="metric-card">
        <div class="metric-title">Lectures Completed</div>
        <div class="metric-value">{watched_lectures}/{total_lectures}</div>
        <div class="metric-subtitle" style="color: {lecture_progress_color};">{lecture_percentage}% Complete</div>
        <div class="progress-bar">
            <div class="progress-value" style="width: {lecture_percentage}%; background-color: {lecture_progress_color};"></div>
        </div>
    </div>
    """

    # Flashcards card
    flashcard_progress_color = "var(--warning-color)" # Amber
    flashcard_card = f"""
    <div class="metric-card">
        <div class="metric-title">Flashcards Mastered</div>
        <div class="metric-value">{mastered_count}/{total_flashcards}</div>
        <div class="metric-subtitle" style="color: {flashcard_progress_color};">{mastery_percentage}% Mastered</div>
        <div class="progress-bar">
            <div class="progress-value" style="width: {mastery_percentage}%; background-color: {flashcard_progress_color};"></div>
        </div>
    </div>
    """

    # Questions card
    question_progress_color = "var(--secondary-color)" # Cyan
    question_card = f"""
    <div class="metric-card">
        <div class="metric-title">Questions Practiced</div>
        <div class="metric-value">{correct_count}/{total_questions}</div>
        <div class="metric-subtitle" style="color: {question_progress_color};">{question_percentage}% Correct</div>
        <div class="progress-bar">
            <div class="progress-value" style="width: {question_percentage}%; background-color: {question_progress_color};"></div>
        </div>
    </div>
    """

    # Study time card
    delta_color = "var(--success-color)" if today_delta >= 0 else "var(--danger-color)" # Green or Red
    delta_symbol = "+" if today_delta >= 0 else ""
    study_card = f"""
    <div class="metric-card">
        <div class="metric-title">Today's Study Time</div>
        <div class="metric-value">{today_minutes} min</div>
        <div class="metric-subtitle" style="color: {delta_color};">{delta_symbol}{today_delta} min vs yesterday</div>
        <div class="progress-bar">
            <div class="progress-value" style="width: {min(100, (today_minutes / 120) * 100)}%; background-color: {delta_color};"></div>
        </div>
    </div>
    """

    # Combine all cards and close the container
    st.markdown(f"{lecture_card}{flashcard_card}{question_card}{study_card}</div>", unsafe_allow_html=True)

    # Summary Statistics - Second row
    col1, col2, col3, col4 = st.columns(4)

    # Get study streak
    c.execute("""
        SELECT date FROM study_log
        GROUP BY date
        ORDER BY date DESC
    """)
    dates = [row[0] for row in c.fetchall()]

    current_streak = 0
    if dates:
        current_date = datetime.strptime(dates[0], '%Y-%m-%d').date()
        expected_date = datetime.now().date()

        # Check if the most recent study date is today or yesterday
        if current_date >= expected_date - timedelta(days=1):
            current_streak = 1
            for i in range(1, len(dates)):
                prev_date = datetime.strptime(dates[i], '%Y-%m-%d').date()
                if (current_date - prev_date).days == 1:
                    current_streak += 1
                    current_date = prev_date
                else:
                    break

    # Get total study days
    c.execute("SELECT COUNT(DISTINCT date) FROM study_log")
    study_days = c.fetchone()[0] or 0

    # Get section with highest score
    c.execute("""
        SELECT section, AVG(score) as avg_score
        FROM progress
        GROUP BY section
        ORDER BY avg_score DESC
        LIMIT 1
    """)
    best_section_data = c.fetchone()
    best_section = best_section_data[0] if best_section_data else "N/A"
    best_score = round(best_section_data[1], 1) if best_section_data else 0

    # Get section with lowest score
    c.execute("""
        SELECT section, AVG(score) as avg_score
        FROM progress
        GROUP BY section
        ORDER BY avg_score ASC
        LIMIT 1
    """)
    weakest_section_data = c.fetchone()
    weakest_section = weakest_section_data[0] if weakest_section_data else "N/A"
    weakest_score = round(weakest_section_data[1], 1) if weakest_section_data else 0

    with col1:
        st.metric("Total Study Hours", f"{study_hours}")
    with col2:
        st.metric("Current Streak", f"{current_streak} days")
    with col3:
        st.metric("Strongest Section", best_section, f"{best_score}%")
    with col4:
        st.metric("Focus Area", weakest_section, f"{weakest_score}%")

    # Create a layout with tabs for different analytics
    tab1, tab2, tab3 = st.tabs(["Progress Overview", "Study Patterns", "Recent Activity"])

    with tab1:
        # Progress Overview
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Section-wise Progress")
            # Get progress data
            c.execute("""
                SELECT section, AVG(score) as avg_score
                FROM progress
                GROUP BY section
            """)
            progress_data = c.fetchall()

            if progress_data:
                df_progress = pd.DataFrame(progress_data, columns=['Section', 'Average Score'])
                fig = px.bar(
                    df_progress,
                    x='Section',
                    y='Average Score',
                    color='Section',
                    title='Section-wise Performance',
                    labels={'Average Score': 'Average Score (%)'},
                    color_discrete_map={
                        'VARC': '#1f77b4',
                        'DILR': '#ff7f0e',
                        'Quant': '#2ca02c'
                    }
                )
                fig.update_layout(yaxis_range=[0, 100])
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No progress data available yet. Start tracking your practice to see insights.")

        with col2:
            st.subheader("Flashcard Mastery")
            # Get flashcard mastery by category
            c.execute("""
                SELECT category,
                       COUNT(*) as total,
                       SUM(CASE WHEN mastered = 1 THEN 1 ELSE 0 END) as mastered
                FROM flashcards
                GROUP BY category
            """)
            flashcard_data = c.fetchall()

            if flashcard_data:
                df_flashcards = pd.DataFrame(flashcard_data, columns=['Category', 'Total', 'Mastered'])
                df_flashcards['Mastery Rate'] = (df_flashcards['Mastered'] / df_flashcards['Total'] * 100).round(1)

                # Create a bar chart
                fig = px.bar(
                    df_flashcards,
                    x='Category',
                    y=['Mastered', 'Total'],
                    title='Flashcard Mastery by Category',
                    barmode='group',
                    labels={'value': 'Count', 'variable': 'Status'},
                    color_discrete_map={
                        'Mastered': '#2ca02c',
                        'Total': '#1f77b4'
                    }
                )
                st.plotly_chart(fig, use_container_width=True)

                # Add a table with mastery rates
                st.dataframe(df_flashcards[['Category', 'Total', 'Mastered', 'Mastery Rate']].rename(
                    columns={'Mastery Rate': 'Mastery Rate (%)'}), hide_index=True)
            else:
                st.info("No flashcard data available yet. Add some flashcards to see insights.")

    with tab2:
        # Study Patterns
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Study Time by Day")
            # Get study time by day of week
            c.execute("""
                SELECT date, SUM(time_spent) as daily_time
                FROM study_log
                GROUP BY date
                ORDER BY date
            """)
            daily_data = c.fetchall()

            if daily_data:
                df_daily = pd.DataFrame(daily_data, columns=["Date", "Minutes"])
                df_daily["Date"] = pd.to_datetime(df_daily["Date"])
                df_daily["Day"] = df_daily["Date"].dt.day_name()

                # Group by day of week
                day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                df_weekly = df_daily.groupby("Day")["Minutes"].mean().reset_index()
                df_weekly["Day"] = pd.Categorical(df_weekly["Day"], categories=day_order, ordered=True)
                df_weekly = df_weekly.sort_values("Day")
                df_weekly["Hours"] = (df_weekly["Minutes"] / 60).round(1)

                # Create a bar chart
                fig = px.bar(
                    df_weekly,
                    x="Day",
                    y="Hours",
                    title="Average Study Hours by Day of Week",
                    color="Hours",
                    color_continuous_scale="Viridis"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No study log data available yet. Log your study sessions to see insights.")

        with col2:
            st.subheader("Topic Distribution")
            # Get study time by topic
            c.execute("""
                SELECT topic, SUM(time_spent) as total_time
                FROM study_log
                GROUP BY topic
            """)
            topic_data = c.fetchall()

            if topic_data:
                df_topic = pd.DataFrame(topic_data, columns=["Topic", "Minutes"])
                df_topic["Hours"] = (df_topic["Minutes"] / 60).round(1)

                # Create a pie chart
                fig = px.pie(
                    df_topic,
                    values="Hours",
                    names="Topic",
                    title="Study Time Distribution by Topic",
                    color="Topic",
                    color_discrete_map={
                        "VARC": "#1f77b4",
                        "DILR": "#ff7f0e",
                        "Quant": "#2ca02c",
                        "General": "#d62728"
                    }
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No study log data available yet. Log your study sessions to see insights.")

    with tab3:
        # Recent Activity
        st.subheader("Recent Activities")
        show_recent_activity(conn, c)

        # Motivational Reminder
        st.subheader("🎯 Your CAT Goal")

        # IIM Ahmedabad image and goal reminder
        col1, col2 = st.columns([1, 2])
        with col1:
            st.image("https://upload.wikimedia.org/wikipedia/en/thumb/3/3f/Indian_Institute_of_Management_Ahmedabad_Logo.svg/1200px-Indian_Institute_of_Management_Ahmedabad_Logo.svg.png", width=150)
        with col2:
            # Get dream school from session state if available
            dream_school = st.session_state.get('dream_school', 'IIM Ahmedabad')
            st.markdown(f"### {dream_school} Awaits You!")

            # Get percentile target from session state if available
            percentile = st.session_state.get('cat_percentile', 99.0)
            st.markdown(f"**Target:** {percentile:.1f}%ile in CAT Exam")

            # Days remaining calculation
            import datetime as dt
            # Get CAT date from session state if available, otherwise use default
            if 'cat_date' in st.session_state:
                cat_date = dt.datetime.combine(st.session_state.cat_date, dt.datetime.min.time())
            else:
                # Default CAT exam date
                cat_date = dt.datetime(2023, 11, 26)

            today = dt.datetime.now()
            days_remaining = (cat_date - today).days

            if days_remaining > 0:
                st.markdown(f"**Days Remaining:** {days_remaining} days")
                st.progress(min(1.0, (365 - days_remaining) / 365))
            else:
                st.markdown("**CAT Exam Day has passed. Results awaited!**")

        # Daily Motivation
        st.subheader("💪 Daily Motivation")

        # List of motivational quotes specifically for CAT and IIM aspirants
        motivational_quotes = [
            """*"Success is not final, failure is not fatal: It is the courage to continue that counts."* - Winston Churchill

            Remember: Every hour of study brings you closer to IIM Ahmedabad!""",

            """*"The difference between ordinary and extraordinary is that little extra."* - Jimmy Johnson

            That extra hour of practice could be what gets you into IIM-A!""",

            """*"The expert in anything was once a beginner."* - Helen Hayes

            IIM Ahmedabad students all started exactly where you are now.""",

            """*"It's not about perfect. It's about effort."* - Jillian Michaels

            Your consistent effort will pay off with a 99%ile score!""",

            """*"The only place where success comes before work is in the dictionary."* - Vidal Sassoon

            Your hard work today is preparing you for IIM Ahmedabad tomorrow!""",

            """*"Don't watch the clock; do what it does. Keep going."* - Sam Levenson

            Every minute counts on your journey to 99%ile!""",

            """*"The future belongs to those who believe in the beauty of their dreams."* - Eleanor Roosevelt

            Your dream of IIM Ahmedabad is within reach!""",

            """*"Hard work beats talent when talent doesn't work hard."* - Tim Notke

            Your dedication to CAT prep will outshine natural aptitude!""",

            """*"The best way to predict your future is to create it."* - Abraham Lincoln

            You're creating your future at IIM Ahmedabad with every practice question!""",

            """*"Success is the sum of small efforts, repeated day in and day out."* - Robert Collier

            Consistency in your CAT preparation is the key to 99%ile!""",

            """*"The secret of getting ahead is getting started."* - Mark Twain

            Each study session brings you one step closer to IIM Ahmedabad!""",

            """*"Believe you can and you're halfway there."* - Theodore Roosevelt

            Your belief in achieving 99%ile is a crucial part of your success!""",

            """*"The CAT exam doesn't test your intelligence, it tests your preparation."* - CAT Toppers

            Your systematic preparation will lead you to IIM-A!""",

            """*"The pain of discipline is far less than the pain of regret."* - Jim Rohn

            Today's discipline is tomorrow's celebration at IIM Ahmedabad!"""
        ]

        # Display a random motivational quote
        import random
        st.markdown(motivational_quotes[random.randint(0, len(motivational_quotes)-1)])

        # Achievement Badges
        st.subheader("🎖 Your Achievements")

        # Calculate achievements based on app usage with error handling
        try:
            c.execute("SELECT COUNT(*) FROM study_sessions")
            study_sessions = c.fetchone()[0] or 0
        except sqlite3.OperationalError:
            study_sessions = 0

        try:
            c.execute("SELECT SUM(duration) FROM study_sessions")
            total_study_minutes = c.fetchone()[0] or 0
        except sqlite3.OperationalError:
            total_study_minutes = 0

        try:
            c.execute("SELECT COUNT(*) FROM videos WHERE watched = 1")
            watched_lectures = c.fetchone()[0] or 0
        except sqlite3.OperationalError:
            watched_lectures = 0

        try:
            c.execute("SELECT COUNT(*) FROM flashcards")
            flashcards_count = c.fetchone()[0] or 0
        except sqlite3.OperationalError:
            flashcards_count = 0

        try:
            c.execute("SELECT COUNT(*) FROM questions")
            questions_count = c.fetchone()[0] or 0
        except sqlite3.OperationalError:
            questions_count = 0

        # Define achievement badges
        badges = [
            {
                "name": "Study Starter",
                "description": "Completed your first study session",
                "icon": "🌟",
                "earned": study_sessions >= 1
            },
            {
                "name": "Focus Master",
                "description": "Accumulated over 10 hours of study time",
                "icon": "⏰",
                "earned": total_study_minutes >= 600
            },
            {
                "name": "Knowledge Seeker",
                "description": "Watched at least 10 lectures",
                "icon": "📺",
                "earned": watched_lectures >= 10
            },
            {
                "name": "Vocabulary Builder",
                "description": "Created at least 10 flashcards",
                "icon": "📄",
                "earned": flashcards_count >= 10
            },
            {
                "name": "Question Conqueror",
                "description": "Added at least 10 practice questions",
                "icon": "❓",
                "earned": questions_count >= 10
            },
            {
                "name": "CAT Champion",
                "description": "On track for 99%ile with consistent practice",
                "icon": "🦁",
                "earned": study_sessions >= 20 and total_study_minutes >= 1200 and watched_lectures >= 20
            }
        ]

        # Display badges in a grid
        badge_cols = st.columns(3)
        for i, badge in enumerate(badges):
            with badge_cols[i % 3]:
                if badge["earned"]:
                    st.markdown(f"<div style='text-align: center; background-color: #e6f7ff; padding: 10px; border-radius: 10px; margin-bottom: 10px;'>"
                              f"<div style='font-size: 30px;'>{badge['icon']}</div>"
                              f"<div style='font-weight: bold;'>{badge['name']}</div>"
                              f"<div style='font-size: 12px;'>{badge['description']}</div>"
                              f"</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div style='text-align: center; background-color: #f5f5f5; padding: 10px; border-radius: 10px; margin-bottom: 10px; opacity: 0.7;'>"
                              f"<div style='font-size: 30px;'>❓</div>"
                              f"<div style='font-weight: bold;'>{badge['name']}</div>"
                              f"<div style='font-size: 12px;'>{badge['description']}</div>"
                              f"</div>", unsafe_allow_html=True)

        # Quick Actions
        st.subheader("⚡ Quick Actions")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Start Focus Timer", key="dashboard_timer"):
                st.session_state.page = "Focus Timer"
                st.rerun()
        with col2:
            if st.button("Track Lectures", key="dashboard_lectures"):
                st.session_state.page = "Lecture Tracker"
                st.rerun()
        with col3:
            if st.button("Practice Questions", key="dashboard_questions"):
                st.session_state.page = "Question Bank"
                st.rerun()

    # Close database connection
    conn.close()

def show_recent_activity(conn, c):
    # Get recent activities from different tables
    activities = []

    # Add custom CSS for modern activity feed
    st.markdown("""
    <style>
    .activity-section {
        margin-bottom: 30px;
    }
    .activity-header {
        display: flex;
        align-items: center;
        margin-bottom: 15px;
        background: var(--neutral-50);
        padding: 10px 15px;
        border-radius: 8px;
        border-left: 4px solid var(--success-color);
    }
    .activity-icon {
        margin-right: 10px;
    }
    .activity-title {
        font-size: 18px;
        font-weight: 600;
        color: var(--success-color);
        margin: 0;
        letter-spacing: -0.3px;
        text-shadow: 0 1px 1px rgba(255, 255, 255, 0.8);
    }
    .activity-feed {
        background: white;
        border-radius: 10px;
        padding: 5px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    .activity-item {
        display: flex;
        align-items: center;
        padding: 12px 15px;
        border-bottom: 1px solid var(--neutral-100);
        transition: background-color 0.2s;
    }
    .activity-item:hover {
        background-color: var(--neutral-50);
    }
    .activity-item:last-child {
        border-bottom: none;
    }
    .activity-badge {
        width: 36px;
        height: 36px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-right: 15px;
        font-size: 18px;
    }
    .activity-content {
        flex-grow: 1;
    }
    .activity-date {
        font-size: 12px;
        color: var(--neutral-500);
        margin-bottom: 3px;
        font-weight: 500;
    }
    .activity-text {
        font-size: 14px;
        color: var(--neutral-700);
        line-height: 1.4;
    }
    .activity-highlight {
        font-weight: 600;
        color: var(--neutral-900);
    }
    .activity-empty {
        padding: 30px;
        text-align: center;
        color: var(--neutral-500);
        font-style: italic;
    }
    </style>

    <div class="activity-section">
        <div class="activity-header">
            <img src="https://cdn-icons-png.flaticon.com/512/2838/2838779.png" width="24" class="activity-icon">
            <h2 class="activity-title">Recent Activities</h2>
        </div>
        <div class="activity-feed">
    """, unsafe_allow_html=True)

    # Try to get study sessions
    try:
        # Check if study_log table exists and has date column
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='study_log'")
        if c.fetchone():
            c.execute("PRAGMA table_info(study_log)")
            study_log_columns = [info[1] for info in c.fetchall()]

            # Get recent study logs if date column exists
            if 'date' in study_log_columns:
                c.execute("""
                    SELECT date, topic, time_spent, 'Study Session' as activity_type
                    FROM study_log
                    ORDER BY date DESC
                    LIMIT 5
                """)
                activities.extend(c.fetchall())
    except sqlite3.OperationalError:
        pass  # Table doesn't exist or other issue

    # Try to get flashcard activities
    try:
        # Check if flashcards table exists
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='flashcards'")
        if c.fetchone():
            c.execute("PRAGMA table_info(flashcards)")
            flashcard_columns = [info[1] for info in c.fetchall()]

            # Get recent flashcard activity if required columns exist
            if 'date' in flashcard_columns and 'word' in flashcard_columns:
                c.execute("""
                    SELECT date, word, category, 'Flashcard Added' as activity_type
                    FROM flashcards
                    ORDER BY date DESC
                    LIMIT 5
                """)
                activities.extend(c.fetchall())
    except sqlite3.OperationalError:
        pass  # Table doesn't exist or other issue

    # Try to get question activities
    try:
        # Check if questions table exists
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='questions'")
        if c.fetchone():
            c.execute("""
                SELECT date, topic, difficulty, 'Question Practiced' as activity_type
                FROM questions
                ORDER BY date DESC
                LIMIT 5
            """)
            activities.extend(c.fetchall())
    except sqlite3.OperationalError:
        pass  # Table doesn't exist or other issue

    # Try to get notes activities
    try:
        # Check if notes table exists
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='notes'")
        if c.fetchone():
            c.execute("""
                SELECT date, title, tags, 'Note Added' as activity_type
                FROM notes
                ORDER BY date DESC
                LIMIT 5
            """)
            activities.extend(c.fetchall())
    except sqlite3.OperationalError:
        pass  # Table doesn't exist or other issue

    # Try to get lecture watching activities
    try:
        # Check if videos table exists and has watched column
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='videos'")
        if c.fetchone():
            c.execute("PRAGMA table_info(videos)")
            video_columns = [info[1] for info in c.fetchall()]

            if 'watched' in video_columns and 'date' in video_columns:
                c.execute("""
                    SELECT date, title, category, 'Lecture Watched' as activity_type
                    FROM videos
                    WHERE watched = 1
                    ORDER BY date DESC
                    LIMIT 5
                """)
                activities.extend(c.fetchall())
    except sqlite3.OperationalError:
        pass  # Table doesn't exist or other issue

    # Sort activities by date (most recent first)
    try:
        activities.sort(key=lambda x: x[0], reverse=True)
    except Exception:
        # If sorting fails, just use the order we have
        pass

    # Display activities with modern design
    if activities:
        for activity in activities[:7]:  # Show top 7 most recent activities
            try:
                date = datetime.strptime(activity[0], '%Y-%m-%d').strftime('%b %d, %Y')

                if activity[3] == 'Study Session':
                    badge_color = "#EEF2FF"  # Light indigo (primary color)
                    icon = "📚"  # Book emoji
                    activity_html = f"""
                    <div class="activity-item">
                        <div class="activity-badge" style="background-color: {badge_color};">{icon}</div>
                        <div class="activity-content">
                            <div class="activity-date">{date}</div>
                            <div class="activity-text">Studied <span class="activity-highlight">{activity[1]}</span> for <span class="activity-highlight">{activity[2]} minutes</span></div>
                        </div>
                    </div>
                    """

                elif activity[3] == 'Flashcard Added':
                    badge_color = "#FFFBEB"  # Light amber (warning color)
                    icon = "🃄"  # Card emoji
                    activity_html = f"""
                    <div class="activity-item">
                        <div class="activity-badge" style="background-color: {badge_color};">{icon}</div>
                        <div class="activity-content">
                            <div class="activity-date">{date}</div>
                            <div class="activity-text">Added flashcard <span class="activity-highlight">'{activity[1]}'</span> in <span class="activity-highlight">{activity[2]}</span></div>
                        </div>
                    </div>
                    """

                elif activity[3] == 'Question Practiced':
                    badge_color = "#ECFEFF"  # Light cyan (secondary color)
                    icon = "❓"  # Question mark emoji
                    activity_html = f"""
                    <div class="activity-item">
                        <div class="activity-badge" style="background-color: {badge_color};">{icon}</div>
                        <div class="activity-content">
                            <div class="activity-date">{date}</div>
                            <div class="activity-text">Practiced <span class="activity-highlight">{activity[2]}</span> level question in <span class="activity-highlight">{activity[1]}</span></div>
                        </div>
                    </div>
                    """

                elif activity[3] == 'Note Added':
                    badge_color = "#ECFDF5"  # Light green (success color)
                    icon = "📝"  # Note emoji
                    activity_html = f"""
                    <div class="activity-item">
                        <div class="activity-badge" style="background-color: {badge_color};">{icon}</div>
                        <div class="activity-content">
                            <div class="activity-date">{date}</div>
                            <div class="activity-text">Added note: <span class="activity-highlight">'{activity[1]}'</span> [Tags: <span class="activity-highlight">{activity[2]}</span>]</div>
                        </div>
                    </div>
                    """

                elif activity[3] == 'Lecture Watched':
                    badge_color = "#FFF1F2"  # Light red (accent color)
                    icon = "📺"  # TV emoji
                    activity_html = f"""
                    <div class="activity-item">
                        <div class="activity-badge" style="background-color: {badge_color};">{icon}</div>
                        <div class="activity-content">
                            <div class="activity-date">{date}</div>
                            <div class="activity-text">Watched lecture <span class="activity-highlight">'{activity[1]}'</span> in <span class="activity-highlight">{activity[2]}</span></div>
                        </div>
                    </div>
                    """
                else:
                    continue  # Skip unknown activity types

                st.markdown(activity_html, unsafe_allow_html=True)

            except Exception as e:
                pass  # Skip activities that can't be displayed properly

        # Close the activity feed container
        st.markdown("</div></div>", unsafe_allow_html=True)
    else:
        # Empty state
        st.markdown("""
        <div class="activity-feed">
            <div class="activity-empty">
                <p>No recent activities found. Start using the app to track your progress!</p>
            </div>
        </div></div>
        """, unsafe_allow_html=True)

def show_flashcards():
    st.title("Flashcards")

    # Initialize database connection
    conn = init_db()
    c = conn.cursor()

    # Create tabs for Add and Review
    tab1, tab2 = st.tabs(["Add Flashcard", "Review Flashcards"])

    with tab1:
        st.header("Add New Flashcard")

        # Form for adding new flashcard
        with st.form("flashcard_form"):
            word = st.text_input("Word/Concept")
            definition = st.text_area("Definition")
            usage = st.text_area("Usage/Example")
            category = st.selectbox("Category", ["VARC", "DILR", "Quant"])

            submitted = st.form_submit_button("Add Flashcard")
            if submitted and word and definition:
                save_flashcard(word, definition, usage, category)
                st.success(f"Added flashcard for '{word}'")

    with tab2:
        st.header("Review Flashcards")
        show_flashcard_review(conn, c)

    # Close database connection
    conn.close()

def show_flashcard_review(conn, c):
    # Filter options
    col1, col2 = st.columns(2)
    with col1:
        category_filter = st.selectbox(
            "Filter by Category",
            ["All", "VARC", "DILR", "Quant"]
        )
    with col2:
        mastery_filter = st.selectbox(
            "Filter by Mastery",
            ["All", "Mastered", "Not Mastered"]
        )

    # Check if the flashcards table has the necessary columns
    c.execute("PRAGMA table_info(flashcards)")
    columns = [info[1] for info in c.fetchall()]

    # If the table doesn't have the required columns, create some sample flashcards
    if 'word' not in columns or 'definition' not in columns or 'usage' not in columns or 'category' not in columns or 'mastered' not in columns:
        st.warning("Flashcards table doesn't have the required columns. Creating sample flashcards.")

        # Drop the existing table if it exists but has wrong schema
        c.execute("DROP TABLE IF EXISTS flashcards")
        conn.commit()

        # Create the table with the correct schema
        c.execute('''CREATE TABLE IF NOT EXISTS flashcards
                     (word TEXT, definition TEXT, usage TEXT, category TEXT, mastered BOOLEAN, date TEXT DEFAULT CURRENT_DATE)''')
        conn.commit()

        # Add some sample flashcards
        sample_flashcards = [
            ("Amalgamate", "To combine or unite to form one organization or structure", "The two companies decided to amalgamate to increase their market share.", "VARC", False, datetime.now().strftime('%Y-%m-%d')),
            ("Ephemeral", "Lasting for a very short time", "The beauty of cherry blossoms is ephemeral, lasting only a few days each year.", "VARC", False, datetime.now().strftime('%Y-%m-%d')),
            ("Permutation", "Each of several possible ways in which a set or number of things can be ordered or arranged", "There are 6 permutations of the 3 letters A, B, and C.", "DILR", True, datetime.now().strftime('%Y-%m-%d')),
            ("Quadratic", "Involving the square (and no higher power) of an unknown quantity or variable", "The quadratic equation ax² + bx + c = 0 has two solutions.", "Quant", True, datetime.now().strftime('%Y-%m-%d'))
        ]

        c.executemany("INSERT INTO flashcards (word, definition, usage, category, mastered, date) VALUES (?, ?, ?, ?, ?, ?)", sample_flashcards)
        conn.commit()

    # Build query based on filters
    query = "SELECT word, definition, usage, category, mastered FROM flashcards"
    conditions = []

    if category_filter != "All":
        conditions.append(f"category = '{category_filter}'")
    if mastery_filter != "All":
        conditions.append(f"mastered = {1 if mastery_filter == 'Mastered' else 0}")

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    try:
        c.execute(query)
        flashcards = c.fetchall()
    except sqlite3.OperationalError as e:
        st.error(f"Database error: {e}")
        st.info("Creating sample flashcards for demonstration.")

        # Create sample flashcards for display
        flashcards = [
            ("Amalgamate", "To combine or unite to form one organization or structure", "The two companies decided to amalgamate to increase their market share.", "VARC", False),
            ("Ephemeral", "Lasting for a very short time", "The beauty of cherry blossoms is ephemeral, lasting only a few days each year.", "VARC", False),
            ("Permutation", "Each of several possible ways in which a set or number of things can be ordered or arranged", "There are 6 permutations of the 3 letters A, B, and C.", "DILR", True),
            ("Quadratic", "Involving the square (and no higher power) of an unknown quantity or variable", "The quadratic equation ax² + bx + c = 0 has two solutions.", "Quant", True)
        ]

    # Display flashcards
    if flashcards:
        for i, (word, definition, usage, category, mastered) in enumerate(flashcards):
            with st.expander(f"{word} ({category})", expanded=False):
                st.markdown(f"**Definition:** {definition}")
                if usage:
                    st.markdown(f"**Usage:** {usage}")

                col1, col2 = st.columns([4, 1])
                with col2:
                    # Toggle mastery status
                    current_status = "Mastered" if mastered else "Not Mastered"
                    new_status = "Not Mastered" if mastered else "Mastered"
                    if st.button(f"Mark as {new_status}", key=f"toggle_{i}"):
                        c.execute(
                            "UPDATE flashcards SET mastered = ? WHERE word = ?",
                            (not mastered, word)
                        )
                        conn.commit()
                        st.rerun()
    else:
        st.info("No flashcards found. Add some flashcards to get started!")

    # Statistics
    st.subheader("Review Statistics")
    stats_col1, stats_col2, stats_col3 = st.columns([1, 1, 1])

    with stats_col1:
        c.execute("SELECT COUNT(*) FROM flashcards")
        total = c.fetchone()[0] or 0
        st.metric("Total Flashcards", total)

    with stats_col2:
        c.execute("SELECT COUNT(*) FROM flashcards WHERE mastered = 1")
        mastered = c.fetchone()[0] or 0
        st.metric("Mastered", mastered)

    with stats_col3:
        if total > 0:
            mastery_rate = round((mastered / total) * 100, 1)
        else:
            mastery_rate = 0
        st.metric("Mastery Rate", f"{mastery_rate}%")

def show_question_bank():
    st.title("Question Bank")

    # Initialize database connection
    conn = init_db()
    c = conn.cursor()

    # Create tabs for Add and Practice
    tab1, tab2 = st.tabs(["Add Question", "Practice Questions"])

    with tab1:
        st.header("Add New Question")

        # Form for adding new question
        with st.form("question_form"):
            question = st.text_area("Question")
            answer = st.text_area("Answer/Solution")
            topic = st.selectbox("Topic", ["VARC", "DILR", "Quant"])
            difficulty = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"])

            submitted = st.form_submit_button("Add Question")
            if submitted and question and answer:
                save_question(question, answer, topic, difficulty)
                st.success("Question added successfully!")

    with tab2:
        st.header("Practice Questions")
        show_practice_questions(conn, c)

    # Close database connection
    conn.close()

def show_practice_questions(conn, c):
    # Filter options
    col1, col2 = st.columns(2)
    with col1:
        topic_filter = st.selectbox(
            "Filter by Topic",
            ["All", "VARC", "DILR", "Quant"]
        )
    with col2:
        difficulty_filter = st.selectbox(
            "Filter by Difficulty",
            ["All", "Easy", "Medium", "Hard"]
        )

    # Check if questions table exists and has the correct schema
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='questions'")
    if c.fetchone() is None:
        # Create questions table if it doesn't exist
        c.execute('''CREATE TABLE IF NOT EXISTS questions
                     (date TEXT, question TEXT, answer TEXT, topic TEXT, difficulty TEXT, correct INTEGER DEFAULT 0)''')
        conn.commit()

        # Add sample questions
        sample_questions = [
            (datetime.now().strftime('%Y-%m-%d'), 'What is the value of x in the equation 2x + 5 = 15?', 'x = 5', 'Quant', 'Easy', 1),
            (datetime.now().strftime('%Y-%m-%d'), 'If a train travels at 60 km/h, how long will it take to cover 150 km?', '2.5 hours', 'Quant', 'Medium', 0),
            (datetime.now().strftime('%Y-%m-%d'), 'Identify the logical fallacy in the following argument...', 'This is an example of a straw man fallacy...', 'VARC', 'Hard', 0),
            (datetime.now().strftime('%Y-%m-%d'), 'Analyze the given data set and find the trend...', 'The trend shows an increasing pattern...', 'DILR', 'Medium', 1)
        ]
        c.executemany("INSERT INTO questions (date, question, answer, topic, difficulty, correct) VALUES (?, ?, ?, ?, ?, ?)", sample_questions)
        conn.commit()
    else:
        # Check if the correct column exists
        c.execute("PRAGMA table_info(questions)")
        columns = [info[1] for info in c.fetchall()]
        if 'correct' not in columns:
            # Add the correct column if it doesn't exist
            c.execute("ALTER TABLE questions ADD COLUMN correct INTEGER DEFAULT 0")
            conn.commit()

    # Build query based on filters
    query = "SELECT date, question, answer, topic, difficulty, correct FROM questions"
    conditions = []

    if topic_filter != "All":
        conditions.append(f"topic = '{topic_filter}'")
    if difficulty_filter != "All":
        conditions.append(f"difficulty = '{difficulty_filter}'")

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    try:
        c.execute(query)
        questions = c.fetchall()
    except sqlite3.OperationalError as e:
        st.error(f"Database error: {e}")
        st.info("Creating sample questions for demonstration.")

        # Create sample questions for display
        questions = [
            (datetime.now().strftime('%Y-%m-%d'), 'What is the value of x in the equation 2x + 5 = 15?', 'x = 5', 'Quant', 'Easy', 1),
            (datetime.now().strftime('%Y-%m-%d'), 'If a train travels at 60 km/h, how long will it take to cover 150 km?', '2.5 hours', 'Quant', 'Medium', 0),
            (datetime.now().strftime('%Y-%m-%d'), 'Identify the logical fallacy in the following argument...', 'This is an example of a straw man fallacy...', 'VARC', 'Hard', 0),
            (datetime.now().strftime('%Y-%m-%d'), 'Analyze the given data set and find the trend...', 'The trend shows an increasing pattern...', 'DILR', 'Medium', 1)
        ]

    # Display questions
    if questions:
        for i, (date, question, answer, topic, difficulty, correct) in enumerate(questions):
            with st.expander(f"{topic} - {difficulty} - {date}", expanded=False):
                st.markdown(f"**Question:** {question}")

                # Show/hide answer with a button
                if st.button("Show Answer", key=f"show_answer_{i}"):
                    st.markdown(f"**Answer:** {answer}")

                # Question metadata
                col1, col2, col3 = st.columns([1, 1, 1])
                with col1:
                    st.write(f"Topic: {topic}")
                with col2:
                    st.write(f"Difficulty: {difficulty}")
                with col3:
                    status = "Correct" if correct else "Incorrect"
                    st.write(f"Status: {status}")

                # Mark as correct/incorrect
                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button("Mark as Correct", key=f"correct_{i}"):
                        c.execute(
                            "UPDATE questions SET correct = 1 WHERE question = ?",
                            (question,)
                        )
                        conn.commit()
                        st.rerun()
                with col2:
                    if st.button("Mark as Incorrect", key=f"incorrect_{i}"):
                        c.execute(
                            "UPDATE questions SET correct = 0 WHERE question = ?",
                            (question,)
                        )
                        conn.commit()
                        st.rerun()
    else:
        st.info("No questions found. Add some questions to get started!")

    # Practice Statistics
    st.subheader("Practice Statistics")
    stats_col1, stats_col2, stats_col3 = st.columns([1, 1, 1])

    with stats_col1:
        c.execute("SELECT COUNT(*) FROM questions")
        total = c.fetchone()[0] or 0
        st.metric("Total Questions", total)

    with stats_col2:
        c.execute("SELECT COUNT(*) FROM questions WHERE correct = 1")
        correct = c.fetchone()[0] or 0
        st.metric("Correct Answers", correct)

    with stats_col3:
        if total > 0:
            success_rate = round((correct / total) * 100, 1)
        else:
            success_rate = 0
        st.metric("Success Rate", f"{success_rate}%")

def show_study_notes():
    st.title("Study Notes")

    # Initialize database connection
    conn = init_db()
    c = conn.cursor()

    # Create tabs for Add and View
    tab1, tab2 = st.tabs(["Add Notes", "View Notes"])

    with tab1:
        st.header("Add New Notes")

        # Form for adding new notes
        with st.form("notes_form"):
            title = st.text_input("Title")
            content = st.text_area("Content", height=300)
            tags = st.multiselect(
                "Tags",
                ["VARC", "DILR", "Quant", "Formulas", "Concepts", "Tips", "Important"]
            )

            submitted = st.form_submit_button("Save Notes")
            if submitted and title and content:
                tags_str = ", ".join(tags) if tags else ""
                save_notes(title, content, tags_str)
                st.success(f"Notes '{title}' saved successfully!")

    with tab2:
        st.header("View Notes")
        show_notes_list(conn, c)

    # Close database connection
    conn.close()

def show_notes_list(conn, c):
    # Check if notes table exists and has the correct schema
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='notes'")
    if c.fetchone() is None:
        # Create notes table if it doesn't exist
        c.execute('''CREATE TABLE IF NOT EXISTS notes
                     (date TEXT, title TEXT, content TEXT, tags TEXT)''')
        conn.commit()

        # Add sample notes
        sample_notes = [
            (datetime.now().strftime('%Y-%m-%d'), 'Reading Comprehension Strategies', 'Here are some effective strategies for RC passages:\n\n1. Skim the passage first\n2. Read the questions before detailed reading\n3. Look for transition words\n4. Pay attention to the first and last sentences of each paragraph\n5. Practice active reading by asking questions', 'VARC, Tips'),
            (datetime.now().strftime('%Y-%m-%d'), 'Important Quant Formulas', 'Key formulas to remember:\n\n1. Quadratic equation: ax² + bx + c = 0\n2. Compound interest: A = P(1 + r/n)^(nt)\n3. Permutation: nPr = n!/(n-r)!\n4. Combination: nCr = n!/[r!(n-r)!]\n5. Area of triangle: (1/2) × base × height', 'Quant, Formulas, Important'),
            (datetime.now().strftime('%Y-%m-%d'), 'Data Interpretation Tips', 'When approaching DI sets:\n\n1. Understand what each graph/table represents\n2. Identify the units of measurement\n3. Look for patterns and trends\n4. Calculate key values before starting questions\n5. Double-check calculations', 'DILR, Tips')
        ]
        c.executemany("INSERT INTO notes (date, title, content, tags) VALUES (?, ?, ?, ?)", sample_notes)
        conn.commit()

    # Search and filter options
    col1, col2 = st.columns(2)

    with col1:
        search_term = st.text_input("Search notes", "")

    with col2:
        tag_filter = st.multiselect(
            "Filter by tags",
            ["VARC", "DILR", "Quant", "Formulas", "Concepts", "Tips", "Important"],
            []
        )

    # Build query based on search and filters
    query = "SELECT date, title, content, tags FROM notes"
    conditions = []

    if search_term:
        conditions.append(f"(title LIKE '%{search_term}%' OR content LIKE '%{search_term}%')")

    if tag_filter:
        tag_conditions = [f"tags LIKE '%{tag}%'" for tag in tag_filter]
        conditions.append("(" + " OR ".join(tag_conditions) + ")")

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY date DESC"

    try:
        c.execute(query)
        notes = c.fetchall()
    except sqlite3.OperationalError as e:
        st.error(f"Database error: {e}")
        st.info("Creating sample notes for demonstration.")

        # Create sample notes for display
        notes = [
            (datetime.now().strftime('%Y-%m-%d'), 'Reading Comprehension Strategies', 'Here are some effective strategies for RC passages:\n\n1. Skim the passage first\n2. Read the questions before detailed reading\n3. Look for transition words\n4. Pay attention to the first and last sentences of each paragraph\n5. Practice active reading by asking questions', 'VARC, Tips'),
            (datetime.now().strftime('%Y-%m-%d'), 'Important Quant Formulas', 'Key formulas to remember:\n\n1. Quadratic equation: ax² + bx + c = 0\n2. Compound interest: A = P(1 + r/n)^(nt)\n3. Permutation: nPr = n!/(n-r)!\n4. Combination: nCr = n!/[r!(n-r)!]\n5. Area of triangle: (1/2) × base × height', 'Quant, Formulas, Important'),
            (datetime.now().strftime('%Y-%m-%d'), 'Data Interpretation Tips', 'When approaching DI sets:\n\n1. Understand what each graph/table represents\n2. Identify the units of measurement\n3. Look for patterns and trends\n4. Calculate key values before starting questions\n5. Double-check calculations', 'DILR, Tips')
        ]

    # Display notes
    if notes:
        for i, (date, title, content, tags) in enumerate(notes):
            with st.expander(f"{title} - {date}", expanded=False):
                st.markdown(content)
                st.markdown(f"**Tags:** {tags}")

                # Edit and Delete buttons (placeholder for future functionality)
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Edit", key=f"edit_note_{i}"):
                        st.info("Edit functionality will be added in a future update.")
                with col2:
                    if st.button("Delete", key=f"delete_note_{i}"):
                        st.info("Delete functionality will be added in a future update.")
    else:
        st.info("No notes found. Add some notes to get started!")

    # Notes Statistics
    st.subheader("Notes Statistics")

    # Get tag counts
    c.execute("""
        SELECT COUNT(*) FROM notes
    """)
    total_notes = c.fetchone()[0] or 0

    # Display statistics
    st.metric("Total Notes", total_notes)

def show_progress_trends():
    st.title("Progress Trends")

    # Initialize database connection
    conn = init_db()
    c = conn.cursor()

    # Check if progress table exists and has the correct schema
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='progress'")
    if c.fetchone() is None:
        # Create progress table with sample data
        c.execute('''CREATE TABLE IF NOT EXISTS progress
                     (date TEXT, section TEXT, topic TEXT, subtopic TEXT, score REAL)''')
        conn.commit()

        # Add sample data spanning multiple dates
        today = datetime.now()
        sample_data = []

        # Generate data for the past 30 days
        for i in range(30, 0, -5):  # Every 5 days for the past 30 days
            date = (today - timedelta(days=i)).strftime('%Y-%m-%d')

            # VARC progress (gradually improving)
            sample_data.append((date, 'VARC', 'VARC', 'Reading Comprehension', 60 + i/2))
            sample_data.append((date, 'VARC', 'VARC', 'Vocabulary', 70 + i/3))

            # DILR progress (fluctuating)
            sample_data.append((date, 'DILR', 'DILR', 'Data Interpretation', 65 + (i % 10)))
            sample_data.append((date, 'DILR', 'DILR', 'Logical Reasoning', 70 + (i % 8)))

            # Quant progress (steady improvement)
            sample_data.append((date, 'Quant', 'Quant', 'Algebra', 75 + i/4))
            sample_data.append((date, 'Quant', 'Quant', 'Geometry', 60 + i/3))

        c.executemany("INSERT INTO progress (date, section, topic, subtopic, score) VALUES (?, ?, ?, ?, ?)", sample_data)
        conn.commit()

    # Get date range for filtering
    c.execute("SELECT MIN(date), MAX(date) FROM progress")
    date_range = c.fetchone()

    if date_range and date_range[0] and date_range[1]:
        start_date = datetime.strptime(date_range[0], '%Y-%m-%d')
        end_date = datetime.strptime(date_range[1], '%Y-%m-%d')
    else:
        # Default to last 30 days if no data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)

    # Date range selector
    col1, col2 = st.columns(2)
    with col1:
        selected_start_date = st.date_input("From", start_date)
    with col2:
        selected_end_date = st.date_input("To", end_date)

    # Convert to string format for SQL query
    start_date_str = selected_start_date.strftime('%Y-%m-%d')
    end_date_str = selected_end_date.strftime('%Y-%m-%d')

    # Get progress data within selected date range
    c.execute("""
        SELECT date, section, AVG(score) as avg_score
        FROM progress
        WHERE date BETWEEN ? AND ?
        GROUP BY date, section
        ORDER BY date
    """, (start_date_str, end_date_str))

    progress_data = c.fetchall()

    if progress_data:
        # Convert to DataFrame for easier manipulation
        df_progress = pd.DataFrame(progress_data, columns=['Date', 'Section', 'Average Score'])
        df_progress['Date'] = pd.to_datetime(df_progress['Date'])

        # Create line chart showing progress over time by section
        st.subheader("Performance Trends by Section")
        fig = px.line(
            df_progress,
            x='Date',
            y='Average Score',
            color='Section',
            title='Section-wise Performance Over Time',
            labels={'Average Score': 'Average Score (%)', 'Date': 'Date'},
            color_discrete_map={
                'VARC': '#1f77b4',
                'DILR': '#ff7f0e',
                'Quant': '#2ca02c'
            }
        )
        st.plotly_chart(fig, use_container_width=True)

        # Section-wise progress
        st.subheader("Section-wise Progress")

        # Calculate improvement rates
        section_improvements = {}
        for section in df_progress['Section'].unique():
            section_data = df_progress[df_progress['Section'] == section]
            if len(section_data) >= 2:
                initial_score = section_data.iloc[0]['Average Score']
                final_score = section_data.iloc[-1]['Average Score']
                improvement = final_score - initial_score
                section_improvements[section] = improvement

        # Display improvement metrics
        if section_improvements:
            cols = st.columns([1] * len(section_improvements))
            for i, (section, improvement) in enumerate(section_improvements.items()):
                with cols[i]:
                    delta = f"+{improvement:.1f}" if improvement > 0 else f"{improvement:.1f}"
                    st.metric(f"{section} Improvement", f"{improvement:.1f}%", delta)
        else:
            st.info("No improvement data available yet.")

        # Get most recent scores by section
        recent_scores = {}
        for section in df_progress['Section'].unique():
            section_data = df_progress[df_progress['Section'] == section]
            if not section_data.empty:
                recent_scores[section] = section_data.iloc[-1]['Average Score']

        # Create radar chart for current proficiency
        st.subheader("Current Proficiency")

        if recent_scores:
            # Prepare data for radar chart
            categories = list(recent_scores.keys())
            values = list(recent_scores.values())

            # Create radar chart using plotly
            fig = go.Figure()

            fig.add_trace(go.Scatterpolar(
                r=values,
                theta=categories,
                fill='toself',
                name='Current Proficiency'
            ))

            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 100]
                    )),
                showlegend=False
            )

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No recent score data available.")
    else:
        st.info("No progress data available for the selected date range. Add some progress data to see trends.")

    # Study consistency
    st.subheader("Study Consistency")

    # Get study log data
    c.execute("""
        SELECT date, SUM(time_spent) as daily_time
        FROM study_log
        WHERE date BETWEEN ? AND ?
        GROUP BY date
        ORDER BY date
    """, (start_date_str, end_date_str))

    study_data = c.fetchall()

    if study_data:
        # Convert to DataFrame
        df_study = pd.DataFrame(study_data, columns=['Date', 'Minutes'])
        df_study['Date'] = pd.to_datetime(df_study['Date'])
        df_study['Hours'] = df_study['Minutes'] / 60

        # Create bar chart for study hours by day
        fig = px.bar(
            df_study,
            x='Date',
            y='Hours',
            title='Daily Study Hours',
            labels={'Hours': 'Study Hours', 'Date': 'Date'}
        )
        st.plotly_chart(fig, use_container_width=True)

        # Study consistency metrics
        total_days = (selected_end_date - selected_start_date).days + 1
        study_days = len(df_study)
        consistency = (study_days / total_days) * 100 if total_days > 0 else 0

        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            st.metric("Study Days", f"{study_days}/{total_days}")
        with col2:
            st.metric("Consistency Rate", f"{consistency:.1f}%")
        with col3:
            avg_hours = df_study['Hours'].mean() if not df_study.empty else 0
            st.metric("Average Daily Hours", f"{avg_hours:.1f}")
    else:
        st.info("No study log data available for the selected date range. Log your study sessions to track consistency.")

    # Close database connection
    conn.close()

def show_topic_analysis():
    st.title("Topic Analysis")

    # Initialize database connection
    conn = init_db()
    c = conn.cursor()

    # Topic selector
    selected_topic = st.selectbox(
        "Select Topic",
        ["VARC", "DILR", "Quant"]
    )

    # Check if progress table exists and has the required columns
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='progress'")
    if c.fetchone() is None:
        # Create progress table with sample data
        c.execute('''CREATE TABLE IF NOT EXISTS progress
                     (date TEXT, section TEXT, topic TEXT, subtopic TEXT, score REAL)''')
        conn.commit()

        # Add sample data
        sample_data = [
            (datetime.now().strftime('%Y-%m-%d'), 'VARC', 'VARC', 'Reading Comprehension', 75.0),
            (datetime.now().strftime('%Y-%m-%d'), 'VARC', 'VARC', 'Vocabulary', 85.0),
            (datetime.now().strftime('%Y-%m-%d'), 'VARC', 'VARC', 'Grammar', 70.0),
            (datetime.now().strftime('%Y-%m-%d'), 'VARC', 'VARC', 'Critical Reasoning', 65.0),
            (datetime.now().strftime('%Y-%m-%d'), 'DILR', 'DILR', 'Data Interpretation', 70.0),
            (datetime.now().strftime('%Y-%m-%d'), 'DILR', 'DILR', 'Logical Reasoning', 80.0),
            (datetime.now().strftime('%Y-%m-%d'), 'DILR', 'DILR', 'Data Sufficiency', 60.0),
            (datetime.now().strftime('%Y-%m-%d'), 'DILR', 'DILR', 'Puzzles', 75.0),
            (datetime.now().strftime('%Y-%m-%d'), 'Quant', 'Quant', 'Algebra', 90.0),
            (datetime.now().strftime('%Y-%m-%d'), 'Quant', 'Quant', 'Geometry', 65.0),
            (datetime.now().strftime('%Y-%m-%d'), 'Quant', 'Quant', 'Number Systems', 80.0),
            (datetime.now().strftime('%Y-%m-%d'), 'Quant', 'Quant', 'Arithmetic', 85.0)
        ]
        c.executemany("INSERT INTO progress (date, section, topic, subtopic, score) VALUES (?, ?, ?, ?, ?)", sample_data)
        conn.commit()
    else:
        # Check if the subtopic column exists
        c.execute("PRAGMA table_info(progress)")
        columns = [info[1] for info in c.fetchall()]
        if 'subtopic' not in columns:
            # Add the subtopic column if it doesn't exist
            c.execute("ALTER TABLE progress ADD COLUMN subtopic TEXT")
            conn.commit()

    # Get topic performance data
    try:
        c.execute("""
            SELECT subtopic, AVG(score) as avg_score, COUNT(*) as attempts
            FROM progress
            WHERE topic = ?
            GROUP BY subtopic
            ORDER BY avg_score DESC
        """, (selected_topic,))
        topic_data = c.fetchall()
    except sqlite3.OperationalError as e:
        st.error(f"Database error: {e}")
        st.info("Creating sample data for demonstration.")

        # Create sample data for display
        if selected_topic == "VARC":
            topic_data = [("Reading Comprehension", 75.0, 5), ("Vocabulary", 85.0, 3), ("Grammar", 70.0, 4), ("Critical Reasoning", 65.0, 2)]
        elif selected_topic == "DILR":
            topic_data = [("Data Interpretation", 70.0, 4), ("Logical Reasoning", 80.0, 6), ("Data Sufficiency", 60.0, 3), ("Puzzles", 75.0, 5)]
        else:  # Quant
            topic_data = [("Algebra", 90.0, 7), ("Geometry", 65.0, 4), ("Number Systems", 80.0, 5), ("Arithmetic", 85.0, 6)]

    if topic_data:
        # Convert to DataFrame
        df_topic = pd.DataFrame(topic_data, columns=['Subtopic', 'Average Score', 'Attempts'])

        # Create two columns for charts
        col1, col2 = st.columns(2)

        with col1:
            # Performance by subtopic
            fig_perf = px.bar(
                df_topic,
                x='Subtopic',
                y='Average Score',
                title=f'{selected_topic} Performance by Subtopic',
                labels={'Average Score': 'Average Score (%)'},
                color='Average Score',
                color_continuous_scale='RdYlGn',  # Red to Yellow to Green scale
                range_color=[50, 100]  # Set color scale range
            )
            st.plotly_chart(fig_perf, use_container_width=True)

        with col2:
            # Attempts by subtopic
            fig_attempts = px.bar(
                df_topic,
                x='Subtopic',
                y='Attempts',
                title=f'{selected_topic} Practice Attempts by Subtopic',
                labels={'Attempts': 'Number of Attempts'}
            )
            st.plotly_chart(fig_attempts, use_container_width=True)

        # Strength and weakness analysis
        st.subheader("Strength and Weakness Analysis")

        # Identify strengths and weaknesses
        strengths = df_topic[df_topic['Average Score'] >= 80].sort_values('Average Score', ascending=False)
        weaknesses = df_topic[df_topic['Average Score'] < 70].sort_values('Average Score')

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### Strengths")
            if not strengths.empty:
                for _, row in strengths.iterrows():
                    st.markdown(f"- **{row['Subtopic']}** ({row['Average Score']:.1f}%)")
            else:
                st.info("No clear strengths identified yet. Keep practicing!")

        with col2:
            st.markdown("### Areas for Improvement")
            if not weaknesses.empty:
                for _, row in weaknesses.iterrows():
                    st.markdown(f"- **{row['Subtopic']}** ({row['Average Score']:.1f}%)")
            else:
                st.success("Great job! No significant weaknesses identified.")

        # Question analysis
        st.subheader("Question Analysis")

        # Check if questions table exists and has the correct schema
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='questions'")
        if c.fetchone() is None:
            # Create questions table if it doesn't exist
            c.execute('''CREATE TABLE IF NOT EXISTS questions
                         (date TEXT, question TEXT, answer TEXT, topic TEXT, difficulty TEXT, correct INTEGER DEFAULT 0)''')
            conn.commit()

            # Add sample questions
            sample_questions = [
                (datetime.now().strftime('%Y-%m-%d'), 'What is the value of x in the equation 2x + 5 = 15?', 'x = 5', 'Quant', 'Easy', 1),
                (datetime.now().strftime('%Y-%m-%d'), 'If a train travels at 60 km/h, how long will it take to cover 150 km?', '2.5 hours', 'Quant', 'Medium', 0),
                (datetime.now().strftime('%Y-%m-%d'), 'Identify the logical fallacy in the following argument...', 'This is an example of a straw man fallacy...', 'VARC', 'Hard', 0),
                (datetime.now().strftime('%Y-%m-%d'), 'Analyze the given data set and find the trend...', 'The trend shows an increasing pattern...', 'DILR', 'Medium', 1)
            ]
            c.executemany("INSERT INTO questions (date, question, answer, topic, difficulty, correct) VALUES (?, ?, ?, ?, ?, ?)", sample_questions)
            conn.commit()
        else:
            # Check if the correct column exists
            c.execute("PRAGMA table_info(questions)")
            columns = [info[1] for info in c.fetchall()]
            if 'correct' not in columns:
                # Add the correct column if it doesn't exist
                c.execute("ALTER TABLE questions ADD COLUMN correct INTEGER DEFAULT 0")
                conn.commit()

        try:
            c.execute("""
                SELECT difficulty, COUNT(*) as count, AVG(CASE WHEN correct = 1 THEN 100 ELSE 0 END) as success_rate
                FROM questions
                WHERE topic = ?
                GROUP BY difficulty
            """, (selected_topic,))
            question_data = c.fetchall()
        except sqlite3.OperationalError as e:
            st.error(f"Database error: {e}")
            st.info("Creating sample data for demonstration.")

            # Create sample data for display
            if selected_topic == "VARC":
                question_data = [("Easy", 5, 80.0), ("Medium", 8, 62.5), ("Hard", 3, 33.3)]
            elif selected_topic == "DILR":
                question_data = [("Easy", 4, 75.0), ("Medium", 6, 50.0), ("Hard", 5, 40.0)]
            else:  # Quant
                question_data = [("Easy", 6, 83.3), ("Medium", 7, 57.1), ("Hard", 4, 25.0)]

        if question_data:
            # Convert to DataFrame
            df_questions = pd.DataFrame(question_data, columns=['Difficulty', 'Count', 'Success Rate'])

            # Create two columns for charts
            col1, col2 = st.columns(2)

            with col1:
                # Question count by difficulty
                fig_count = px.bar(
                    df_questions,
                    x='Difficulty',
                    y='Count',
                    title=f'{selected_topic} Questions by Difficulty',
                    labels={'Count': 'Number of Questions'}
                )
                st.plotly_chart(fig_count, use_container_width=True)

            with col2:
                # Success rate by difficulty
                fig_success = px.bar(
                    df_questions,
                    x='Difficulty',
                    y='Success Rate',
                    title='Success Rate by Difficulty',
                    labels={'Success Rate': 'Success Rate (%)'}
                )
                st.plotly_chart(fig_success, use_container_width=True)
        else:
            st.info(f"No question data available for {selected_topic}. Add some questions to see analysis.")

        # Time analysis
        st.subheader("Time Analysis")

        # Check if study_log table exists and has the required columns
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='study_log'")
        if c.fetchone() is None:
            # Create study_log table with sample data
            c.execute('''CREATE TABLE IF NOT EXISTS study_log
                         (date TEXT, topic TEXT, subtopic TEXT, time_spent INTEGER, notes TEXT)''')
            conn.commit()

            # Add sample data
            sample_data = [
                (datetime.now().strftime('%Y-%m-%d'), 'VARC', 'Reading Comprehension', 60, 'Practiced RC passages'),
                (datetime.now().strftime('%Y-%m-%d'), 'VARC', 'Vocabulary', 45, 'Learned new words'),
                (datetime.now().strftime('%Y-%m-%d'), 'VARC', 'Grammar', 30, 'Reviewed grammar rules'),
                (datetime.now().strftime('%Y-%m-%d'), 'VARC', 'Critical Reasoning', 50, 'Practiced CR questions'),
                (datetime.now().strftime('%Y-%m-%d'), 'DILR', 'Data Interpretation', 75, 'Solved DI sets'),
                (datetime.now().strftime('%Y-%m-%d'), 'DILR', 'Logical Reasoning', 90, 'Practiced LR puzzles'),
                (datetime.now().strftime('%Y-%m-%d'), 'DILR', 'Data Sufficiency', 45, 'Worked on DS problems'),
                (datetime.now().strftime('%Y-%m-%d'), 'DILR', 'Puzzles', 60, 'Solved puzzle sets'),
                (datetime.now().strftime('%Y-%m-%d'), 'Quant', 'Algebra', 60, 'Solved equations'),
                (datetime.now().strftime('%Y-%m-%d'), 'Quant', 'Geometry', 45, 'Practiced theorems'),
                (datetime.now().strftime('%Y-%m-%d'), 'Quant', 'Number Systems', 50, 'Worked on number properties'),
                (datetime.now().strftime('%Y-%m-%d'), 'Quant', 'Arithmetic', 55, 'Practiced arithmetic problems')
            ]
            c.executemany("INSERT INTO study_log (date, topic, subtopic, time_spent, notes) VALUES (?, ?, ?, ?, ?)", sample_data)
            conn.commit()
        else:
            # Check if the subtopic column exists
            c.execute("PRAGMA table_info(study_log)")
            columns = [info[1] for info in c.fetchall()]
            if 'subtopic' not in columns:
                # Add the subtopic column if it doesn't exist
                c.execute("ALTER TABLE study_log ADD COLUMN subtopic TEXT")
                conn.commit()

                # Update existing records with sample subtopics
                c.execute("SELECT DISTINCT topic FROM study_log")
                topics = c.fetchall()
                for topic in topics:
                    if topic[0] == 'VARC':
                        c.execute("UPDATE study_log SET subtopic = 'Reading Comprehension' WHERE topic = ? AND subtopic IS NULL", (topic[0],))
                    elif topic[0] == 'DILR':
                        c.execute("UPDATE study_log SET subtopic = 'Data Interpretation' WHERE topic = ? AND subtopic IS NULL", (topic[0],))
                    elif topic[0] == 'Quant':
                        c.execute("UPDATE study_log SET subtopic = 'Algebra' WHERE topic = ? AND subtopic IS NULL", (topic[0],))
                conn.commit()

        try:
            c.execute("""
                SELECT subtopic, AVG(time_spent) as avg_time
                FROM study_log
                WHERE topic = ?
                GROUP BY subtopic
            """, (selected_topic,))
            time_data = c.fetchall()
        except sqlite3.OperationalError as e:
            st.error(f"Database error: {e}")
            st.info("Creating sample data for demonstration.")

            # Create sample data for display
            if selected_topic == "VARC":
                time_data = [("Reading Comprehension", 60), ("Vocabulary", 45), ("Grammar", 30), ("Critical Reasoning", 50)]
            elif selected_topic == "DILR":
                time_data = [("Data Interpretation", 75), ("Logical Reasoning", 90), ("Data Sufficiency", 45), ("Puzzles", 60)]
            else:  # Quant
                time_data = [("Algebra", 60), ("Geometry", 45), ("Number Systems", 50), ("Arithmetic", 55)]

        if time_data:
            df_time = pd.DataFrame(time_data, columns=['Subtopic', 'Average Time'])
            fig_time = px.bar(
                df_time,
                x='Subtopic',
                y='Average Time',
                title='Average Time Spent per Subtopic',
                labels={'Average Time': 'Minutes'}
            )
            st.plotly_chart(fig_time, use_container_width=True)

            # Calculate total time spent on this topic
            c.execute("""
                SELECT SUM(time_spent) as total_time
                FROM study_log
                WHERE topic = ?
            """, (selected_topic,))
            total_time = c.fetchone()[0] or 0

            # Display total time spent
            st.metric(f"Total Time Spent on {selected_topic}", f"{total_time} minutes ({total_time/60:.1f} hours)")
        else:
            st.info(f"No time data available for {selected_topic}. Log your study sessions to see time analysis.")
    else:
        st.info(f"No data available for {selected_topic}. Add some progress data to see topic analysis.")

    # Recommendations
    st.subheader("Recommendations")

    # Generate recommendations based on available data
    if topic_data:
        # Find weakest subtopic
        df_topic = pd.DataFrame(topic_data, columns=['Subtopic', 'Average Score', 'Attempts'])
        weakest_subtopic = df_topic.loc[df_topic['Average Score'].idxmin()]['Subtopic']
        weakest_score = df_topic['Average Score'].min()

        # Find least practiced subtopic
        least_practiced = df_topic.loc[df_topic['Attempts'].idxmin()]['Subtopic']
        least_attempts = df_topic['Attempts'].min()

        st.markdown(f"### Based on your performance in {selected_topic}:")
        st.markdown(f"1. **Focus on improving {weakest_subtopic}** (Current score: {weakest_score:.1f}%)")
        st.markdown(f"2. **Increase practice for {least_practiced}** (Only {least_attempts} attempts so far)")

        # Additional recommendations based on topic
        if selected_topic == "VARC":
            st.markdown("3. **Reading Comprehension Strategy**: Practice active reading by summarizing each paragraph")
            st.markdown("4. **Vocabulary Building**: Learn 5 new words daily and use them in sentences")
        elif selected_topic == "DILR":
            st.markdown("3. **Data Interpretation**: Practice different types of charts and graphs daily")
            st.markdown("4. **Logical Reasoning**: Focus on identifying patterns and rules quickly")
        else:  # Quant
            st.markdown("3. **Formula Revision**: Create a formula sheet and review it regularly")
            st.markdown("4. **Practice Speed**: Work on mental math to improve calculation speed")
    else:
        st.info("Add some progress data to get personalized recommendations.")

    # Close database connection
    conn.close()

def show_focus_timer():
    st.title("Focus Timer")

    # Initialize database connection
    conn = init_db()
    c = conn.cursor()

    # Get user settings
    c.execute("SELECT * FROM productivity_settings WHERE user_id = 'default'")
    settings = c.fetchone()

    if settings:
        focus_duration = settings[1]  # focus_duration
        break_duration = settings[2]  # break_duration
    else:
        # Default settings
        focus_duration = 25
        break_duration = 5

        # Insert default settings
        c.execute("""
            INSERT INTO productivity_settings
            (user_id, focus_duration, break_duration, reminder_frequency, notification_enabled, daily_goal, reminder_time)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ("default", focus_duration, break_duration, "daily", False, 120, "09:00"))
        conn.commit()

    # Create two columns for timer and settings
    col1, col2 = st.columns([2, 1])

    with col1:
        st.header("Pomodoro Timer")

        # Timer settings
        timer_options = {
            "Focus": focus_duration,
            "Short Break": break_duration,
            "Long Break": break_duration * 3
        }

        # Timer type selector
        timer_type = st.radio("Timer Type", list(timer_options.keys()))
        selected_duration = timer_options[timer_type]

        # Topic selector for focus sessions
        if timer_type == "Focus":
            topic = st.selectbox(
                "What are you working on?",
                ["VARC", "DILR", "Quant", "General Preparation", "Mock Test", "Other"]
            )
            subtopic = st.text_input("Subtopic (optional)")

        # Timer display
        if 'timer_running' not in st.session_state:
            st.session_state.timer_running = False
            st.session_state.start_time = None
            st.session_state.remaining_time = selected_duration * 60
            st.session_state.elapsed_time = 0

        # Timer controls
        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            if st.button("Start" if not st.session_state.timer_running else "Pause"):
                if not st.session_state.timer_running:
                    st.session_state.timer_running = True
                    st.session_state.start_time = datetime.now()
                else:
                    st.session_state.timer_running = False
                    st.session_state.elapsed_time += (datetime.now() - st.session_state.start_time).total_seconds()
                st.rerun()

        with col2:
            if st.button("Reset"):
                st.session_state.timer_running = False
                st.session_state.start_time = None
                st.session_state.remaining_time = selected_duration * 60
                st.session_state.elapsed_time = 0
                st.rerun()

        with col3:
            if timer_type == "Focus" and st.button("Complete"):
                if 'start_time' in st.session_state and st.session_state.start_time:
                    # Calculate time spent
                    if st.session_state.timer_running:
                        elapsed = st.session_state.elapsed_time + (datetime.now() - st.session_state.start_time).total_seconds()
                    else:
                        elapsed = st.session_state.elapsed_time

                    # Convert to minutes
                    minutes_spent = int(elapsed / 60)

                    # Save to database
                    if minutes_spent > 0:
                        save_study_session(topic, subtopic, minutes_spent)
                        st.success(f"Saved {minutes_spent} minutes of study on {topic}")

                    # Reset timer
                    st.session_state.timer_running = False
                    st.session_state.start_time = None
                    st.session_state.remaining_time = selected_duration * 60
                    st.session_state.elapsed_time = 0
                    st.rerun()

        # Display timer
        if st.session_state.timer_running:
            current_elapsed = st.session_state.elapsed_time + (datetime.now() - st.session_state.start_time).total_seconds()
            remaining = max(0, selected_duration * 60 - current_elapsed)
        else:
            remaining = max(0, selected_duration * 60 - st.session_state.elapsed_time)

        # Format time as mm:ss
        mins, secs = divmod(int(remaining), 60)
        timer_display = f"{mins:02d}:{secs:02d}"

        # Display large timer
        st.markdown(f"<h1 style='text-align: center; font-size: 6em;'>{timer_display}</h1>", unsafe_allow_html=True)

        # Progress bar
        progress = 1 - (remaining / (selected_duration * 60))
        st.progress(min(1.0, max(0.0, progress)))

        # Display message based on timer type
        if timer_type == "Focus":
            st.info(f"Focus on your {topic} studies. Stay concentrated!")
        elif timer_type == "Short Break":
            st.success("Take a short break. Stretch, hydrate, and relax your eyes.")
        else:  # Long Break
            st.success("Take a longer break. Get up, move around, and refresh your mind.")

    with col2:
        st.header("Timer Settings")

        # Form for updating timer settings
        with st.form("timer_settings"):
            new_focus = st.number_input("Focus Duration (minutes)", min_value=1, max_value=60, value=focus_duration)
            new_break = st.number_input("Break Duration (minutes)", min_value=1, max_value=30, value=break_duration)

            submitted = st.form_submit_button("Update Settings")
            if submitted:
                # Update settings in database
                c.execute("""
                    UPDATE productivity_settings
                    SET focus_duration = ?, break_duration = ?
                    WHERE user_id = ?
                """, (new_focus, new_break, "default"))
                conn.commit()
                st.success("Settings updated!")
                st.rerun()

        # Display study session history
        st.subheader("Recent Study Sessions")

        # Get recent study sessions
        c.execute("""
            SELECT date, topic, time_spent
            FROM study_log
            ORDER BY date DESC, rowid DESC
            LIMIT 5
        """)
        sessions = c.fetchall()

        if sessions:
            for date, topic, time_spent in sessions:
                st.write(f"{date} - {topic}: {time_spent} minutes")
        else:
            st.info("No study sessions recorded yet.")

        # Display daily goal progress
        st.subheader("Daily Goal Progress")

        # Get today's study time
        today = datetime.now().strftime('%Y-%m-%d')
        c.execute("""
            SELECT SUM(time_spent)
            FROM study_log
            WHERE date = ?
        """, (today,))
        today_minutes = c.fetchone()[0] or 0

        # Get daily goal from settings
        c.execute("SELECT daily_goal FROM productivity_settings WHERE user_id = 'default'")
        daily_goal = c.fetchone()
        if daily_goal:
            daily_goal = daily_goal[0]
        else:
            daily_goal = 120  # Default 2 hours

        # Display progress
        progress = min(1.0, today_minutes / daily_goal)
        st.progress(progress)
        st.write(f"{today_minutes} / {daily_goal} minutes ({int(progress * 100)}%)")

    # Close database connection
    conn.close()

def show_settings():
    st.title("Settings")

    # Import datetime module for date handling
    import datetime as dt

    # Initialize database connection
    conn = init_db()
    c = conn.cursor()

    # Create tabs for different settings
    tab1, tab2, tab3 = st.tabs(["General Settings", "Data Management", "Integrations"])

    with tab1:
        st.header("General Settings")

        # Get current settings
        c.execute("SELECT * FROM productivity_settings WHERE user_id = 'default'")
        settings = c.fetchone()

        if settings:
            focus_duration = settings[1]  # focus_duration
            break_duration = settings[2]  # break_duration
            reminder_frequency = settings[3]  # reminder_frequency
            notification_enabled = settings[4]  # notification_enabled
            daily_goal = settings[5]  # daily_goal
            reminder_time = settings[6]  # reminder_time
        else:
            # Default settings
            focus_duration = 25
            break_duration = 5
            reminder_frequency = "daily"
            notification_enabled = False
            daily_goal = 120
            reminder_time = "09:00"

            # Insert default settings
            c.execute("""
                INSERT INTO productivity_settings
                (user_id, focus_duration, break_duration, reminder_frequency, notification_enabled, daily_goal, reminder_time)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, ("default", focus_duration, break_duration, reminder_frequency, notification_enabled, daily_goal, reminder_time))
            conn.commit()

        # Form for updating general settings
        with st.form("general_settings"):
            st.subheader("CAT Exam Goals")

            # CAT percentile goal
            cat_percentile = st.slider("CAT Percentile Target", min_value=80.0, max_value=100.0, value=99.0, step=0.1, format="%.1f%%")
            st.markdown(f"**Target:** {cat_percentile:.1f}%ile")

            # Dream B-school selection
            b_schools = ["IIM Ahmedabad", "IIM Bangalore", "IIM Calcutta", "IIM Lucknow", "IIM Indore", "IIM Kozhikode", "FMS Delhi", "XLRI Jamshedpur", "SP Jain Mumbai", "MDI Gurgaon", "Other"]
            dream_school = st.selectbox("Dream B-School", b_schools, index=0)

            # CAT exam date
            cat_date = st.date_input("CAT Exam Date", value=dt.datetime(2023, 11, 26))
            today = dt.datetime.now().date()
            days_remaining = (cat_date - today).days

            if days_remaining > 0:
                st.info(f"{days_remaining} days remaining until CAT exam")
                # Calculate required daily study hours
                recommended_hours = round(min(12, max(4, 1200 / days_remaining)), 1)
                st.markdown(f"**Recommended daily study:** {recommended_hours} hours")
            else:
                st.warning("Please set a future date for your CAT exam")

            st.subheader("Daily Study Goals")
            new_daily_goal = st.number_input("Daily Study Goal (minutes)", min_value=15, max_value=720, value=daily_goal)

            st.subheader("Timer Settings")
            new_focus = st.number_input("Focus Duration (minutes)", min_value=1, max_value=60, value=focus_duration)
            new_break = st.number_input("Break Duration (minutes)", min_value=1, max_value=30, value=break_duration)

            st.subheader("Reminders")
            new_reminder_enabled = st.checkbox("Enable Reminders", value=notification_enabled)
            new_reminder_frequency = st.selectbox(
                "Reminder Frequency",
                ["daily", "weekdays", "weekends", "custom"],
                index=["daily", "weekdays", "weekends", "custom"].index(reminder_frequency) if reminder_frequency in ["daily", "weekdays", "weekends", "custom"] else 0
            )
            new_reminder_time = st.time_input("Reminder Time", datetime.strptime(reminder_time, "%H:%M") if reminder_time else datetime.strptime("09:00", "%H:%M"))

            # Make the submit button more prominent
            st.markdown("")
            submitted = st.form_submit_button("💾 Save Settings", use_container_width=True)
            if submitted:
                try:
                    # Update settings in database
                    c.execute("""
                        UPDATE productivity_settings
                        SET focus_duration = ?, break_duration = ?, reminder_frequency = ?,
                            notification_enabled = ?, daily_goal = ?, reminder_time = ?
                        WHERE user_id = ?
                    """, (new_focus, new_break, new_reminder_frequency, new_reminder_enabled,
                          new_daily_goal, new_reminder_time.strftime("%H:%M"), "default"))
                    conn.commit()
                    st.success("Settings updated successfully!")

                    # Also save CAT goals in session state for use elsewhere
                    if 'cat_percentile' not in st.session_state:
                        st.session_state.cat_percentile = cat_percentile
                    else:
                        st.session_state.cat_percentile = cat_percentile

                    if 'dream_school' not in st.session_state:
                        st.session_state.dream_school = dream_school
                    else:
                        st.session_state.dream_school = dream_school

                    if 'cat_date' not in st.session_state:
                        st.session_state.cat_date = cat_date
                    else:
                        st.session_state.cat_date = cat_date
                except Exception as e:
                    st.error(f"Error saving settings: {e}")

    with tab2:
        st.header("Data Management")

        # Export data
        st.subheader("Export Data")
        if st.button("Export All Data"):
            # Create a ZIP file with all data
            st.info("This feature will export all your data to a downloadable ZIP file.")
            st.info("Feature coming soon!")

        # Import data
        st.subheader("Import Data")
        uploaded_file = st.file_uploader("Upload Data File", type=["zip"])
        if uploaded_file is not None:
            st.info("This feature will import data from a previously exported ZIP file.")
            st.info("Feature coming soon!")

        # Reset data
        st.subheader("Reset Data")
        st.warning("⚠️ Warning: This will delete all your data and cannot be undone!")

        # Two-step confirmation for data reset
        if 'reset_confirmation' not in st.session_state:
            st.session_state.reset_confirmation = False

        if not st.session_state.reset_confirmation:
            if st.button("Reset All Data"):
                st.session_state.reset_confirmation = True
                st.rerun()
        else:
            st.error("Are you absolutely sure? All your data will be permanently deleted.")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Yes, Reset Everything"):
                    # Reset the database
                    conn.close()  # Close the current connection
                    conn = init_db(reset=True)  # Reinitialize with reset=True
                    st.session_state.reset_confirmation = False
                    st.success("All data has been reset to zero!")
                    st.rerun()
            with col2:
                if st.button("No, Cancel"):
                    st.session_state.reset_confirmation = False
                    st.rerun()

    with tab3:
        st.header("Integrations")

        # Google Sheets integration
        st.subheader("Google Sheets Integration")
        st.info("Google Sheets integration is currently disabled in this version.")

        # Placeholder for future integrations
        st.subheader("Other Integrations")
        st.info("Additional integrations will be available in future updates.")

        # About section
        st.subheader("About CAT Preparation Tracker")
        st.markdown("""
        **Version:** 1.0.0

        **Description:** A comprehensive study tracking application for CAT (Common Admission Test) preparation.

        **Features:**
        - Dashboard with progress metrics
        - Flashcards for vocabulary review
        - Question bank with difficulty tracking
        - Study notes with tagging system
        - Section-wise performance analytics
        - Topic analysis and recommendations
        - Focus timer for productivity

        **Created by:** Your Name

        **GitHub:** [CAT-Preparation-Tracker](https://github.com/yourusername/CAT-Preparation-Tracker)
        """)

    # Close database connection
    conn.close()

def show_lecture_tracker():
    st.title("Lecture Tracker")

    # Initialize database connection
    conn = init_db()
    c = conn.cursor()

    # Create tabs for Add and View
    tab1, tab2 = st.tabs(["Add Lecture", "View Lectures"])

    with tab1:
        st.header("Add New Lecture")

        # Form for adding new lecture
        with st.form("lecture_form"):
            title = st.text_input("Lecture Title")
            date = st.date_input("Date", datetime.now())
            instructor = st.text_input("Instructor (optional)")
            topic = st.selectbox("Topic", ["VARC", "DILR", "Quant", "General"])
            subtopic = st.text_input("Subtopic (optional)")
            notes = st.text_area("Lecture Notes", height=200)
            resources = st.text_area("Additional Resources (optional)")

            submitted = st.form_submit_button("Save Lecture")
            if submitted and title and notes:
                # Combine notes and resources
                full_notes = f"{notes}\n\n**Additional Resources:**\n{resources}" if resources else notes

                # Save as a note with lecture tag
                tags = f"{topic}, lecture, {subtopic}" if subtopic else f"{topic}, lecture"
                save_lecture_notes(title, full_notes, date)
                st.success(f"Lecture '{title}' saved successfully!")

    with tab2:
        st.header("View Lectures")

        # Filter options
        col1, col2 = st.columns(2)
        with col1:
            topic_filter = st.selectbox(
                "Filter by Topic",
                ["All", "VARC", "DILR", "Quant", "General"]
            )
        with col2:
            sort_order = st.selectbox(
                "Sort By",
                ["Date (Newest First)", "Date (Oldest First)", "Title (A-Z)"]
            )

        # Build query based on filters
        query = "SELECT date, title, content, tags FROM notes WHERE tags LIKE '%lecture%'"

        if topic_filter != "All":
            query += f" AND tags LIKE '%{topic_filter}%'"

        if sort_order == "Date (Newest First)":
            query += " ORDER BY date DESC"
        elif sort_order == "Date (Oldest First)":
            query += " ORDER BY date ASC"
        else:  # Title (A-Z)
            query += " ORDER BY title ASC"

        try:
            c.execute(query)
            lectures = c.fetchall()
        except sqlite3.OperationalError as e:
            st.error(f"Database error: {e}")
            lectures = []

        if lectures:
            # Display lectures
            for i, (date, title, content, tags) in enumerate(lectures):
                with st.expander(f"{title} - {date}", expanded=False):
                    # Display lecture content
                    st.markdown(content)

                    # Display tags
                    st.markdown(f"**Tags:** {tags}")

                    # Actions
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button("Mark as Completed", key=f"complete_lecture_{i}"):
                            st.success("Lecture marked as completed!")
                    with col2:
                        if st.button("Edit", key=f"edit_lecture_{i}"):
                            st.info("Edit functionality will be added in a future update.")
                    with col3:
                        if st.button("Delete", key=f"delete_lecture_{i}"):
                            st.info("Delete functionality will be added in a future update.")
        else:
            st.info("No lectures found. Add some lectures to get started!")

        # Lecture statistics
        st.subheader("Lecture Statistics")

        # Count lectures by topic
        topic_counts = {}
        for _, _, _, tags in lectures:
            for topic in ["VARC", "DILR", "Quant", "General"]:
                if topic.lower() in tags.lower():
                    topic_counts[topic] = topic_counts.get(topic, 0) + 1

        # Display statistics
        if topic_counts:
            # Create a DataFrame for the chart
            df_topics = pd.DataFrame({
                'Topic': list(topic_counts.keys()),
                'Count': list(topic_counts.values())
            })

            # Create a bar chart
            fig = px.bar(
                df_topics,
                x='Topic',
                y='Count',
                title='Lectures by Topic',
                color='Topic',
                color_discrete_map={
                    'VARC': '#1f77b4',
                    'DILR': '#ff7f0e',
                    'Quant': '#2ca02c',
                    'General': '#d62728'
                }
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No lecture data available for statistics.")

    # Close database connection
    conn.close()

def show_study_patterns():
    st.title("Study Patterns Analysis")

    # Initialize database connection
    conn = init_db()
    c = conn.cursor()

    # Get date range for filtering
    c.execute("SELECT MIN(date), MAX(date) FROM study_log")
    date_range = c.fetchone()

    if date_range and date_range[0] and date_range[1]:
        start_date = datetime.strptime(date_range[0], '%Y-%m-%d')
        end_date = datetime.strptime(date_range[1], '%Y-%m-%d')
    else:
        # Default to last 30 days if no data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)

    # Date range selector
    col1, col2 = st.columns(2)
    with col1:
        selected_start_date = st.date_input("From", start_date)
    with col2:
        selected_end_date = st.date_input("To", end_date)

    # Convert to string format for SQL query
    start_date_str = selected_start_date.strftime('%Y-%m-%d')
    end_date_str = selected_end_date.strftime('%Y-%m-%d')

    # Check if study_log table exists and has data
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='study_log'")
    if c.fetchone() is None:
        # Create study_log table with sample data
        c.execute('''CREATE TABLE IF NOT EXISTS study_log
                     (date TEXT, topic TEXT, subtopic TEXT, time_spent INTEGER, notes TEXT)''')
        conn.commit()

        # Add sample data spanning multiple dates
        today = datetime.now()
        sample_data = []

        # Generate data for the past 30 days
        for i in range(30, 0, -1):  # Every day for the past 30 days
            date = (today - timedelta(days=i)).strftime('%Y-%m-%d')

            # Skip some days to create a realistic pattern
            if i % 4 == 0:  # Skip every 4th day
                continue

            # Vary the topics and time spent
            if i % 3 == 0:
                topic = "VARC"
                subtopic = "Reading Comprehension" if i % 2 == 0 else "Vocabulary"
                time_spent = 45 + (i % 30)  # Between 45-75 minutes
            elif i % 3 == 1:
                topic = "DILR"
                subtopic = "Data Interpretation" if i % 2 == 0 else "Logical Reasoning"
                time_spent = 60 + (i % 20)  # Between 60-80 minutes
            else:
                topic = "Quant"
                subtopic = "Algebra" if i % 2 == 0 else "Geometry"
                time_spent = 50 + (i % 25)  # Between 50-75 minutes

            # Add more time on weekends
            if (today - timedelta(days=i)).weekday() >= 5:  # Weekend (5=Saturday, 6=Sunday)
                time_spent += 30

            sample_data.append((date, topic, subtopic, time_spent, f"Study session on {subtopic}"))

        c.executemany("INSERT INTO study_log (date, topic, subtopic, time_spent, notes) VALUES (?, ?, ?, ?, ?)", sample_data)
        conn.commit()

    # Get study log data within selected date range
    c.execute("""
        SELECT date, topic, subtopic, time_spent
        FROM study_log
        WHERE date BETWEEN ? AND ?
        ORDER BY date
    """, (start_date_str, end_date_str))

    study_data = c.fetchall()

    if study_data:
        # Convert to DataFrame for easier manipulation
        df_study = pd.DataFrame(study_data, columns=['Date', 'Topic', 'Subtopic', 'Minutes'])
        df_study['Date'] = pd.to_datetime(df_study['Date'])
        df_study['Hours'] = df_study['Minutes'] / 60

        # 1. Weekly study pattern
        st.subheader("Weekly Study Pattern")

        # Add day of week
        df_study['Day'] = df_study['Date'].dt.day_name()

        # Group by day of week and calculate average study time
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        df_weekly = df_study.groupby('Day')['Hours'].mean().reset_index()
        df_weekly['Day'] = pd.Categorical(df_weekly['Day'], categories=day_order, ordered=True)
        df_weekly = df_weekly.sort_values('Day')

        # Create bar chart for weekly pattern
        fig_weekly = px.bar(
            df_weekly,
            x='Day',
            y='Hours',
            title='Average Study Hours by Day of Week',
            labels={'Hours': 'Average Hours', 'Day': 'Day of Week'},
            color='Hours',
            color_continuous_scale='Viridis'
        )
        st.plotly_chart(fig_weekly, use_container_width=True)

        # 2. Daily study time distribution
        st.subheader("Daily Study Time Distribution")

        # Create calendar heatmap
        # First, group by date and sum hours
        df_daily = df_study.groupby(df_study['Date'].dt.date)['Hours'].sum().reset_index()
        df_daily.columns = ['Date', 'Hours']

        # Create a date range for all days in the selected period
        all_dates = pd.date_range(start=selected_start_date, end=selected_end_date, freq='D')
        all_dates_df = pd.DataFrame({'Date': all_dates})
        all_dates_df['Date'] = all_dates_df['Date'].dt.date

        # Merge to include days with no study time
        df_daily = pd.merge(all_dates_df, df_daily, on='Date', how='left').fillna(0)

        # Add year, month, day, and weekday columns for the heatmap
        df_daily['Year'] = pd.to_datetime(df_daily['Date']).dt.year
        df_daily['Month'] = pd.to_datetime(df_daily['Date']).dt.month
        df_daily['MonthName'] = pd.to_datetime(df_daily['Date']).dt.month_name()
        df_daily['Day'] = pd.to_datetime(df_daily['Date']).dt.day
        df_daily['Weekday'] = pd.to_datetime(df_daily['Date']).dt.day_name()

        # Create heatmap
        fig_heatmap = px.imshow(
            df_daily.pivot_table(index='Day', columns='MonthName', values='Hours', aggfunc='sum'),
            labels=dict(x="Month", y="Day of Month", color="Hours"),
            title="Study Hours Heatmap",
            color_continuous_scale='Viridis'
        )
        st.plotly_chart(fig_heatmap, use_container_width=True)

        # 3. Topic distribution
        st.subheader("Topic Distribution")

        # Group by topic and calculate total hours
        df_topic = df_study.groupby('Topic')['Hours'].sum().reset_index()

        # Create pie chart for topic distribution
        fig_topic = px.pie(
            df_topic,
            values='Hours',
            names='Topic',
            title='Study Time Distribution by Topic',
            color='Topic',
            color_discrete_map={
                'VARC': '#1f77b4',
                'DILR': '#ff7f0e',
                'Quant': '#2ca02c'
            }
        )
        st.plotly_chart(fig_topic, use_container_width=True)

        # 4. Study consistency
        st.subheader("Study Consistency")

        # Calculate consistency metrics
        total_days = (selected_end_date - selected_start_date).days + 1
        study_days = df_daily[df_daily['Hours'] > 0].shape[0]
        consistency = (study_days / total_days) * 100 if total_days > 0 else 0

        # Calculate streak information
        df_daily['HasStudied'] = df_daily['Hours'] > 0
        df_daily['StreakGroup'] = (df_daily['HasStudied'] != df_daily['HasStudied'].shift()).cumsum()
        streak_groups = df_daily.groupby(['StreakGroup', 'HasStudied']).size().reset_index(name='Count')

        # Find the longest streak of study days
        if not streak_groups.empty and True in streak_groups['HasStudied'].values:
            longest_streak = streak_groups[streak_groups['HasStudied'] == True]['Count'].max()
        else:
            longest_streak = 0

        # Find current streak
        current_streak = 0
        for i in range(len(df_daily) - 1, -1, -1):
            if df_daily.iloc[i]['HasStudied']:
                current_streak += 1
            else:
                break

        # Display consistency metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Study Days", f"{study_days}/{total_days}")
        with col2:
            st.metric("Consistency Rate", f"{consistency:.1f}%")
        with col3:
            st.metric("Longest Streak", f"{longest_streak} days")

        # Display current streak
        st.metric("Current Streak", f"{current_streak} days")

        # 5. Study efficiency
        st.subheader("Study Efficiency")

        # Calculate average study time per day of week
        df_efficiency = df_study.groupby(['Day', 'Topic'])['Hours'].mean().reset_index()
        df_efficiency['Day'] = pd.Categorical(df_efficiency['Day'], categories=day_order, ordered=True)
        df_efficiency = df_efficiency.sort_values('Day')

        # Create grouped bar chart for efficiency by day and topic
        fig_efficiency = px.bar(
            df_efficiency,
            x='Day',
            y='Hours',
            color='Topic',
            barmode='group',
            title='Average Study Hours by Day and Topic',
            labels={'Hours': 'Average Hours', 'Day': 'Day of Week'},
            color_discrete_map={
                'VARC': '#1f77b4',
                'DILR': '#ff7f0e',
                'Quant': '#2ca02c'
            }
        )
        st.plotly_chart(fig_efficiency, use_container_width=True)

        # 6. Recommendations based on patterns
        st.subheader("Recommendations")

        # Find the day with the least study time
        least_productive_day = df_weekly.loc[df_weekly['Hours'].idxmin()]['Day']
        least_productive_hours = df_weekly['Hours'].min()

        # Find the most productive day
        most_productive_day = df_weekly.loc[df_weekly['Hours'].idxmax()]['Day']
        most_productive_hours = df_weekly['Hours'].max()

        # Find the least studied topic
        least_studied_topic = df_topic.loc[df_topic['Hours'].idxmin()]['Topic']
        least_studied_hours = df_topic['Hours'].min()

        # Generate recommendations
        st.markdown("### Based on your study patterns:")
        st.markdown(f"1. **Increase study time on {least_productive_day}s** (Currently averaging only {least_productive_hours:.1f} hours)")
        st.markdown(f"2. **Maintain your momentum on {most_productive_day}s** (Great job averaging {most_productive_hours:.1f} hours!)")
        st.markdown(f"3. **Focus more on {least_studied_topic}** (Only {least_studied_hours:.1f} total hours in the selected period)")

        if consistency < 70:
            st.markdown("4. **Improve study consistency** by establishing a regular study routine")
        else:
            st.markdown("4. **Great consistency!** Keep up the regular study routine")

        if current_streak > 0:
            st.markdown(f"5. **Maintain your current streak** of {current_streak} days")
        else:
            st.markdown("5. **Start a new study streak today** to build momentum")
    else:
        st.info("No study log data available for the selected date range. Log your study sessions to see patterns.")

    # Close database connection
    conn.close()

def show_video_resources():
    # Add a more visually appealing header
    col1, col2 = st.columns([1, 5])
    with col1:
        st.image("https://cdn-icons-png.flaticon.com/512/2641/2641409.png", width=80)
    with col2:
        st.title("Lecture Tracker")
        st.markdown("<p style='color: #6c757d; margin-top: -15px;'>Track your progress through CAT preparation lectures</p>", unsafe_allow_html=True)

    # Add a horizontal rule for visual separation
    st.markdown("<hr style='margin-top: -10px; margin-bottom: 20px;'>", unsafe_allow_html=True)

    # Initialize database connection
    conn = init_db()
    c = conn.cursor()

    # Create tabs for different lecture categories
    tab1, tab2, tab3, tab4 = st.tabs(["Spreadsheet View", "VARC", "DILR", "Quant"])

    # Check if videos table exists
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='videos'")
    if c.fetchone() is None:
        # Create lectures table
        c.execute('''CREATE TABLE IF NOT EXISTS videos
                     (date TEXT, title TEXT, url TEXT, category TEXT, notes TEXT, rating INTEGER, watched BOOLEAN DEFAULT 0)''')
        conn.commit()
    else:
        # Check if watched column exists
        c.execute("PRAGMA table_info(videos)")
        columns = [info[1] for info in c.fetchall()]
        if 'watched' not in columns:
            # Add watched column if it doesn't exist
            try:
                c.execute("ALTER TABLE videos ADD COLUMN watched BOOLEAN DEFAULT 0")
                conn.commit()
                st.success("Updated database schema to include watched status.")
            except sqlite3.OperationalError as e:
                st.error(f"Error updating database schema: {e}")

        # Add sample lectures from Rodha YouTube channel
        sample_videos = [
            # Quants - Arithmetic
            (datetime.now().strftime('%Y-%m-%d'), 'Speed Math (SM 1)', 'https://www.youtube.com/watch?v=7Ojn_hVm9Xw', 'Quant', 'Speed math techniques for CAT', 5, 0),
            (datetime.now().strftime('%Y-%m-%d'), 'Averages (AVG 1)', 'https://www.youtube.com/watch?v=Suw0WDHMba0', 'Quant', 'Concepts of averages for CAT', 5, 1),
            (datetime.now().strftime('%Y-%m-%d'), 'Alligation & Mixtures (AM 1)', 'https://www.youtube.com/watch?v=Rl5LpyvMh-c', 'Quant', 'Alligation and mixtures concepts', 4, 0),

            # DILR
            (datetime.now().strftime('%Y-%m-%d'), 'Linear & Circular Arrangement (LCA 1)', 'https://www.youtube.com/watch?v=Rl5LpyvMh-c', 'DILR', 'Solving arrangement problems', 5, 1),
            (datetime.now().strftime('%Y-%m-%d'), 'Venn Diagrams (VD 1)', 'https://www.youtube.com/watch?v=Rl5LpyvMh-c', 'DILR', 'Venn diagram approach', 4, 0),

            # VARC
            (datetime.now().strftime('%Y-%m-%d'), 'Reading Comprehension (RC 1)', 'https://www.youtube.com/watch?v=Rl5LpyvMh-c', 'VARC', 'RC strategies', 5, 1),
            (datetime.now().strftime('%Y-%m-%d'), 'Para Jumbles (PJ 1)', 'https://www.youtube.com/watch?v=Rl5LpyvMh-c', 'VARC', 'Para jumbles solving techniques', 4, 0)
        ]
        c.executemany("INSERT INTO videos (date, title, url, category, notes, rating, watched) VALUES (?, ?, ?, ?, ?, ?, ?)", sample_videos)
        conn.commit()

    # Function to display lectures for a category
    def show_category_videos(category):
        try:
            c.execute("""
                SELECT title, url, notes, rating, rowid, watched
                FROM videos
                WHERE category = ?
                ORDER BY title ASC
            """, (category,))
            videos = c.fetchall()
        except sqlite3.OperationalError:
            # If watched column doesn't exist yet
            c.execute("""
                SELECT title, url, notes, rating, rowid
                FROM videos
                WHERE category = ?
                ORDER BY title ASC
            """, (category,))
            # Add a default watched value of 0 (False)
            videos = [(title, url, notes, rating, rowid, 0) for title, url, notes, rating, rowid in c.fetchall()]

        if videos:
            # Create a table to display all lectures
            st.write(f"### {category} Lectures")

            # Create columns for the table header
            cols = st.columns([0.1, 0.5, 0.2, 0.2])
            cols[0].write("**Status**")
            cols[1].write("**Lecture**")
            cols[2].write("**Watch**")
            cols[3].write("**Mark**")

            st.markdown("---")

            # Display each lecture as a row in the table
            for title, url, notes, rating, rowid, watched in videos:
                cols = st.columns([0.1, 0.5, 0.2, 0.2])

                # Status column (watched/unwatched)
                with cols[0]:
                    if watched:
                        st.markdown("✅")
                    else:
                        st.markdown("⬜")

                # Title column
                with cols[1]:
                    st.write(title)

                # Watch column (link to video)
                with cols[2]:
                    st.markdown(f"[Watch]({url})")

                # Mark as watched/unwatched column
                with cols[3]:
                    if watched:
                        if st.button("Mark Unwatched", key=f"unwatch_{rowid}"):
                            c.execute("UPDATE videos SET watched = 0 WHERE rowid = ?", (rowid,))
                            conn.commit()
                            st.success(f"Marked '{title}' as unwatched")
                            st.rerun()
                    else:
                        if st.button("Mark Watched", key=f"watch_{rowid}"):
                            c.execute("UPDATE videos SET watched = 1 WHERE rowid = ?", (rowid,))
                            conn.commit()
                            st.success(f"Marked '{title}' as watched")
                            st.rerun()
        else:
            st.info(f"No {category} lectures found. Import lectures from the spreadsheet to get started!")

    # Display spreadsheet view
    with tab1:
        st.header("Spreadsheet View")

        # Display the Google Sheet URL
        sheet_url = "https://docs.google.com/spreadsheets/d/121TJowkkWLeaPSAYp5Cokg0If9iwBtFDF6CZ5JWIYO0/edit?pli=1&gid=0#gid=0"
        st.markdown(f"[Open Google Spreadsheet]({sheet_url})")

        # Create a dataframe with all the lecture data from the spreadsheet
        spreadsheet_data = [
            # Quants - Arithmetic
            ["Quant", "Arithmetic", "Speed Math", "SM 1", "https://www.youtube.com/watch?v=7Ojn_hVm9Xw"],
            ["Quant", "Arithmetic", "Speed Math", "SM 2", "https://www.youtube.com/watch?v=7Ojn_hVm9Xw"],
            ["Quant", "Arithmetic", "Speed Math", "SM 3", "https://www.youtube.com/watch?v=7Ojn_hVm9Xw"],
            ["Quant", "Arithmetic", "Speed Math", "SM 4", "https://www.youtube.com/watch?v=7Ojn_hVm9Xw"],
            ["Quant", "Arithmetic", "Speed Math", "SM 5", "https://www.youtube.com/watch?v=7Ojn_hVm9Xw"],
            ["Quant", "Arithmetic", "Speed Math", "SM 6", "https://www.youtube.com/watch?v=7Ojn_hVm9Xw"],
            ["Quant", "Arithmetic", "Averages", "AVG 1", "https://www.youtube.com/watch?v=Suw0WDHMba0"],
            ["Quant", "Arithmetic", "Averages", "AVG 2", "https://www.youtube.com/watch?v=Suw0WDHMba0"],
            ["Quant", "Arithmetic", "Averages", "AVG 3", "https://www.youtube.com/watch?v=Suw0WDHMba0"],
            ["Quant", "Arithmetic", "Averages", "AVG 4", "https://www.youtube.com/watch?v=Suw0WDHMba0"],
            ["Quant", "Arithmetic", "Alligation & Mixtures", "AM 1", "https://www.youtube.com/watch?v=Rl5LpyvMh-c"],
            ["Quant", "Arithmetic", "Alligation & Mixtures", "AM 2", "https://www.youtube.com/watch?v=Rl5LpyvMh-c"],
            ["Quant", "Arithmetic", "Alligation & Mixtures", "AM 3", "https://www.youtube.com/watch?v=Rl5LpyvMh-c"],
            ["Quant", "Arithmetic", "Alligation & Mixtures", "AM 4", "https://www.youtube.com/watch?v=Rl5LpyvMh-c"],
            ["Quant", "Arithmetic", "Alligation & Mixtures", "AM 5", "https://www.youtube.com/watch?v=Rl5LpyvMh-c"],
            ["Quant", "Arithmetic", "Alligation & Mixtures", "AM 6", "https://www.youtube.com/watch?v=Rl5LpyvMh-c"],

            # DILR
            ["DILR", "Arrangement", "Linear & Circular Arrangement", "LCA 1", "https://www.youtube.com/watch?v=Rl5LpyvMh-c"],
            ["DILR", "Arrangement", "Linear & Circular Arrangement", "LCA 2", "https://www.youtube.com/watch?v=Rl5LpyvMh-c"],
            ["DILR", "Arrangement", "Linear & Circular Arrangement", "LCA 3", "https://www.youtube.com/watch?v=Rl5LpyvMh-c"],
            ["DILR", "Arrangement", "Linear & Circular Arrangement", "LCA 4", "https://www.youtube.com/watch?v=Rl5LpyvMh-c"],
            ["DILR", "Arrangement", "Linear & Circular Arrangement", "LCA 5", "https://www.youtube.com/watch?v=Rl5LpyvMh-c"],
            ["DILR", "Sets", "Venn Diagrams", "VD 1", "https://www.youtube.com/watch?v=Rl5LpyvMh-c"],
            ["DILR", "Sets", "Venn Diagrams", "VD 2", "https://www.youtube.com/watch?v=Rl5LpyvMh-c"],
            ["DILR", "Sets", "Venn Diagrams", "VD 3", "https://www.youtube.com/watch?v=Rl5LpyvMh-c"],
            ["DILR", "Sets", "Venn Diagrams", "VD 4", "https://www.youtube.com/watch?v=Rl5LpyvMh-c"],
            ["DILR", "Sets", "Venn Diagrams", "VD 5", "https://www.youtube.com/watch?v=Rl5LpyvMh-c"],
            ["DILR", "Sets", "Venn Diagrams", "VD 6", "https://www.youtube.com/watch?v=Rl5LpyvMh-c"],

            # VARC
            ["VARC", "Reading", "Reading Comprehension", "RC 1", "https://www.youtube.com/watch?v=Rl5LpyvMh-c"],
            ["VARC", "Reading", "Reading Comprehension", "RC 2", "https://www.youtube.com/watch?v=Rl5LpyvMh-c"],
            ["VARC", "Reading", "Reading Comprehension", "RC 3", "https://www.youtube.com/watch?v=Rl5LpyvMh-c"],
            ["VARC", "Reading", "Reading Comprehension", "RC 4", "https://www.youtube.com/watch?v=Rl5LpyvMh-c"],
            ["VARC", "Reading", "Reading Comprehension", "RC 5", "https://www.youtube.com/watch?v=Rl5LpyvMh-c"],
            ["VARC", "Reading", "Reading Comprehension", "RC 6", "https://www.youtube.com/watch?v=Rl5LpyvMh-c"],
            ["VARC", "Reading", "Reading Comprehension", "RC 7", "https://www.youtube.com/watch?v=Rl5LpyvMh-c"],
            ["VARC", "Reading", "Reading Comprehension", "RC 8", "https://www.youtube.com/watch?v=Rl5LpyvMh-c"],
            ["VARC", "Reading", "Reading Comprehension", "RC 9", "https://www.youtube.com/watch?v=Rl5LpyvMh-c"],
            ["VARC", "Verbal", "Para Jumbles", "PJ 1", "https://www.youtube.com/watch?v=Rl5LpyvMh-c"],
            ["VARC", "Verbal", "Para Jumbles", "PJ 2", "https://www.youtube.com/watch?v=Rl5LpyvMh-c"]
        ]

        # Create a DataFrame
        df = pd.DataFrame(spreadsheet_data, columns=["Section", "Topic", "Subtopic", "Code", "URL"])

        # Add a full title column
        df["Title"] = df["Subtopic"] + " (" + df["Code"] + ")"

        # Get watched status for each lecture
        for i, row in df.iterrows():
            title = row["Title"]
            try:
                c.execute("SELECT watched FROM videos WHERE title = ?", (title,))
                result = c.fetchone()
                if result:
                    df.at[i, "Watched"] = "✅" if result[0] else "⬜"
                else:
                    # If not in database, add it
                    try:
                        c.execute("""
                            INSERT INTO videos (date, title, url, category, notes, rating, watched)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (datetime.now().strftime('%Y-%m-%d'), title, row["URL"], row["Section"], "", 5, 0))
                        conn.commit()
                        df.at[i, "Watched"] = "⬜"
                    except sqlite3.OperationalError:
                        # If watched column doesn't exist yet
                        c.execute("""
                            INSERT INTO videos (date, title, url, category, notes, rating)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (datetime.now().strftime('%Y-%m-%d'), title, row["URL"], row["Section"], "", 5))
                        conn.commit()
                        df.at[i, "Watched"] = "⬜"
            except sqlite3.OperationalError:
                # If watched column doesn't exist yet
                c.execute("SELECT rowid FROM videos WHERE title = ?", (title,))
                result = c.fetchone()
                if result:
                    df.at[i, "Watched"] = "⬜"  # Default to unwatched
                else:
                    # Add without watched column
                    c.execute("""
                        INSERT INTO videos (date, title, url, category, notes, rating)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (datetime.now().strftime('%Y-%m-%d'), title, row["URL"], row["Section"], "", 5))
                    conn.commit()
                    df.at[i, "Watched"] = "⬜"

        # Create filters
        col1, col2, col3 = st.columns(3)
        with col1:
            section_filter = st.multiselect("Filter by Section", df["Section"].unique(), default=df["Section"].unique())
        with col2:
            topic_filter = st.multiselect("Filter by Topic", df["Topic"].unique(), default=[])
        with col3:
            watched_filter = st.radio("Show", ["All", "Watched", "Unwatched"], horizontal=True)

        # Apply filters
        filtered_df = df[df["Section"].isin(section_filter)]
        if topic_filter:
            filtered_df = filtered_df[filtered_df["Topic"].isin(topic_filter)]
        if watched_filter == "Watched":
            filtered_df = filtered_df[filtered_df["Watched"] == "✅"]
        elif watched_filter == "Unwatched":
            filtered_df = filtered_df[filtered_df["Watched"] == "⬜"]

        # Display the filtered dataframe
        st.dataframe(
            filtered_df[["Watched", "Section", "Topic", "Subtopic", "Code", "Title"]],
            column_config={
                "Watched": st.column_config.TextColumn("Status"),
                "Section": st.column_config.TextColumn("Section"),
                "Topic": st.column_config.TextColumn("Topic"),
                "Subtopic": st.column_config.TextColumn("Subtopic"),
                "Code": st.column_config.TextColumn("Code"),
                "Title": st.column_config.TextColumn("Title")
            },
            hide_index=True
        )

        # Display statistics
        st.subheader("Progress Statistics")
        total_lectures = len(df)
        watched_lectures = len(df[df["Watched"] == "✅"])
        progress_percentage = round((watched_lectures / total_lectures) * 100, 1) if total_lectures > 0 else 0

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Lectures", total_lectures)
        with col2:
            st.metric("Completed", watched_lectures)
        with col3:
            st.metric("Progress", f"{progress_percentage}%")

        # Progress bar
        st.progress(progress_percentage / 100)

        # Section-wise progress
        st.subheader("Section-wise Progress")
        section_progress = {}
        for section in df["Section"].unique():
            section_df = df[df["Section"] == section]
            section_total = len(section_df)
            section_watched = len(section_df[section_df["Watched"] == "✅"])
            section_progress[section] = round((section_watched / section_total) * 100, 1) if section_total > 0 else 0

        # Create a DataFrame for the chart
        progress_df = pd.DataFrame({
            "Section": list(section_progress.keys()),
            "Progress": list(section_progress.values())
        })

        # Create a bar chart
        fig = px.bar(
            progress_df,
            x="Section",
            y="Progress",
            title="Progress by Section",
            labels={"Progress": "Completion %"},
            color="Section",
            color_discrete_map={
                "VARC": "#1f77b4",
                "DILR": "#ff7f0e",
                "Quant": "#2ca02c"
            }
        )
        st.plotly_chart(fig, use_container_width=True)

        # Add a button to mark selected lectures as watched/unwatched
        st.subheader("Bulk Actions")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Mark All Filtered as Watched"):
                for _, row in filtered_df.iterrows():
                    c.execute("UPDATE videos SET watched = 1 WHERE title = ?", (row["Title"],))
                conn.commit()
                st.success(f"Marked {len(filtered_df)} lectures as watched")
                st.rerun()
        with col2:
            if st.button("Mark All Filtered as Unwatched"):
                for _, row in filtered_df.iterrows():
                    c.execute("UPDATE videos SET watched = 0 WHERE title = ?", (row["Title"],))
                conn.commit()
                st.success(f"Marked {len(filtered_df)} lectures as unwatched")
                st.rerun()

    # Display videos by category
    with tab2:
        show_category_videos("VARC")

    with tab3:
        show_category_videos("DILR")

    with tab4:
        show_category_videos("Quant")

    # Lecture completion statistics
    st.subheader("Lecture Completion Summary")
    col1, col2, col3 = st.columns(3)

    with col1:
        c.execute("SELECT COUNT(*) FROM videos")
        total_lectures = c.fetchone()[0] or 0
        st.metric("Total Lectures", total_lectures)

    with col2:
        try:
            c.execute("SELECT COUNT(*) FROM videos WHERE watched = 1")
            watched_lectures = c.fetchone()[0] or 0
        except sqlite3.OperationalError:
            watched_lectures = 0
        st.metric("Completed Lectures", watched_lectures)

    with col3:
        completion_rate = round((watched_lectures / total_lectures) * 100, 1) if total_lectures > 0 else 0
        st.metric("Completion Rate", f"{completion_rate}%")

    # Category breakdown
    try:
        c.execute("""
            SELECT category, COUNT(*) as total, SUM(watched) as watched
            FROM videos
            GROUP BY category
        """)
        category_data = c.fetchall()
    except sqlite3.OperationalError:
        # If watched column doesn't exist
        c.execute("""
            SELECT category, COUNT(*) as total
            FROM videos
            GROUP BY category
        """)
        # Add a default watched value of 0
        category_data = [(category, total, 0) for category, total in c.fetchall()]

    if category_data:
        df_categories = pd.DataFrame(category_data, columns=["Category", "Total", "Watched"])
        df_categories["Completion"] = (df_categories["Watched"] / df_categories["Total"] * 100).round(1)

        # Create a bar chart for category completion
        fig = px.bar(
            df_categories,
            x="Category",
            y="Completion",
            title="Completion Rate by Category",
            labels={"Completion": "Completion %"},
            color="Category",
            color_discrete_map={
                "VARC": "#1f77b4",
                "DILR": "#ff7f0e",
                "Quant": "#2ca02c"
            }
        )
        st.plotly_chart(fig, use_container_width=True)

    # Close database connection
    conn.close()

# Main function to run the app
if __name__ == "__main__":
    # Initialize session state for navigation
    if 'page' not in st.session_state:
        st.session_state.page = "Dashboard"

    # Create a sidebar for navigation with enhanced styling
    st.sidebar.title("CAT Prep Tracker")
    st.sidebar.markdown("---")

    # Group pages by category with icons
    st.sidebar.markdown("### 🏠 Main")
    if st.sidebar.button("Dashboard", key="nav_dashboard", use_container_width=True):
        st.session_state.page = "Dashboard"

    st.sidebar.markdown("### 📚 Study Tools")
    study_tools = {
        "Lecture Tracker": "📝",
        "Flashcards": "🔤",
        "Question Bank": "❓",
        "Study Notes": "📒",
        "Video Resources": "🎬",
        "Focus Timer": "⏱️"
    }

    for tool, icon in study_tools.items():
        if st.sidebar.button(f"{icon} {tool}", key=f"nav_{tool.lower().replace(' ', '_')}", use_container_width=True):
            st.session_state.page = tool

    st.sidebar.markdown("### 📊 Analytics")
    analytics = {
        "Progress Trends": "📈",
        "Topic Analysis": "🔍",
        "Study Patterns": "📆"
    }

    for tool, icon in analytics.items():
        if st.sidebar.button(f"{icon} {tool}", key=f"nav_{tool.lower().replace(' ', '_')}", use_container_width=True):
            st.session_state.page = tool

    st.sidebar.markdown("### ⚙️ System")
    if st.sidebar.button("Settings", key="nav_settings", use_container_width=True):
        st.session_state.page = "Settings"

    # Get the current page from session state
    page = st.session_state.page

    # Display user info and app version
    st.sidebar.markdown("---")
    st.sidebar.markdown("### User Info")
    st.sidebar.markdown("**Status:** Active User")

    # Get study statistics for sidebar
    conn = init_db()
    c = conn.cursor()

    # Get total study hours
    c.execute("SELECT SUM(time_spent) FROM study_log")
    total_minutes = c.fetchone()[0] or 0
    total_hours = round(total_minutes / 60, 1)

    # Get today's study time
    today = datetime.now().strftime('%Y-%m-%d')
    c.execute("SELECT SUM(time_spent) FROM study_log WHERE date = ?", (today,))
    today_minutes = c.fetchone()[0] or 0

    # Get flashcard count
    c.execute("SELECT COUNT(*) FROM flashcards")
    flashcard_count = c.fetchone()[0] or 0

    # Get question count
    c.execute("SELECT COUNT(*) FROM questions")
    question_count = c.fetchone()[0] or 0

    # Close connection
    conn.close()

    # Display statistics
    st.sidebar.markdown(f"**Total Study:** {total_hours} hours")
    st.sidebar.markdown(f"**Today:** {today_minutes} minutes")
    st.sidebar.markdown(f"**Flashcards:** {flashcard_count}")
    st.sidebar.markdown(f"**Questions:** {question_count}")

    # App info
    st.sidebar.markdown("---")
    st.sidebar.markdown("### App Info")
    st.sidebar.markdown("**Version:** 1.0.0")
    st.sidebar.markdown("**Last Updated:** " + datetime.now().strftime('%Y-%m-%d'))
    st.sidebar.markdown("[GitHub Repository](https://github.com/yourusername/CAT-Preparation-Tracker)")

    # Display the selected page
    if page == "Dashboard":
        show_dashboard()
    elif page == "Lecture Tracker":
        show_lecture_tracker()
    elif page == "Flashcards":
        show_flashcards()
    elif page == "Question Bank":
        show_question_bank()
    elif page == "Study Notes":
        show_study_notes()
    elif page == "Video Resources":
        show_video_resources()
    elif page == "Progress Trends":
        show_progress_trends()
    elif page == "Topic Analysis":
        show_topic_analysis()
    elif page == "Study Patterns":
        show_study_patterns()
    elif page == "Focus Timer":
        show_focus_timer()
    elif page == "Settings":
        show_settings()
