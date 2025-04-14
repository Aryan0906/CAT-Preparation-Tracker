import streamlit as st
from datetime import datetime
import sqlite3
from utils import save_study_session, save_timer_session

def init_db():
    """Initialize database connection"""
    conn = sqlite3.connect('cat_prep.db')
    c = conn.cursor()
    
    # Ensure productivity_settings table exists
    c.execute('''CREATE TABLE IF NOT EXISTS productivity_settings
                 (user_id TEXT, focus_duration INTEGER DEFAULT 25, break_duration INTEGER DEFAULT 5,
                  reminder_frequency TEXT, notification_enabled BOOLEAN DEFAULT 1,
                  daily_goal INTEGER DEFAULT 120, reminder_time TEXT DEFAULT '09:00')''')
    
    # Ensure timer_logs table exists
    c.execute('''CREATE TABLE IF NOT EXISTS timer_logs
                 (date TEXT, start_time TEXT, end_time TEXT, duration INTEGER,
                  completed BOOLEAN, topic TEXT)''')
    
    # Ensure study_log table exists
    c.execute('''CREATE TABLE IF NOT EXISTS study_log
                 (date TEXT, topic TEXT, subtopic TEXT, time_spent INTEGER, notes TEXT)''')
    
    conn.commit()
    return conn

def show_focus_timer():
    """Display a focus timer using the external Pomofocus.io service"""
    st.title("Focus Timer")
    
    # Initialize database connection
    conn = init_db()
    c = conn.cursor()
    
    # Get user settings
    c.execute("SELECT * FROM productivity_settings WHERE user_id = 'default'")
    settings = c.fetchone()
    
    if not settings:
        # Insert default settings if none exist
        c.execute("""
            INSERT INTO productivity_settings
            (user_id, focus_duration, break_duration, reminder_frequency, notification_enabled, daily_goal, reminder_time)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ("default", 25, 5, "daily", True, 120, "09:00"))
        conn.commit()
    
    # Create layout
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Topic selector for focus sessions
        topic = st.selectbox(
            "What are you working on?",
            ["VARC", "DILR", "Quant", "General Preparation", "Mock Test", "Other"]
        )
        subtopic = st.text_input("Subtopic (optional)")
        
        # Embed Pomofocus.io in an iframe
        st.markdown("""
        <div style="border: 1px solid #ddd; border-radius: 5px; padding: 10px; margin-bottom: 20px;">
            <iframe src="https://pomofocus.io/" width="100%" height="600" frameborder="0"></iframe>
        </div>
        """, unsafe_allow_html=True)
        
        # Add a form to record completed sessions
        with st.form("record_session"):
            st.subheader("Record Completed Session")
            minutes_spent = st.number_input("Minutes spent", min_value=1, max_value=180, value=25)
            record_button = st.form_submit_button("Record Session")
            
            if record_button:
                try:
                    # Save to database
                    save_study_session(topic, subtopic, minutes_spent)
                    save_timer_session(
                        datetime.now(),
                        datetime.now(),
                        minutes_spent * 60,
                        True,
                        topic
                    )
                    st.success(f"Saved {minutes_spent} minutes of study on {topic}")
                except Exception as e:
                    st.error(f"Error saving session: {str(e)}")
    
    with col2:
        # Display study session history
        st.subheader("Recent Sessions")
        
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
                st.write(f"{date} - {topic}: {time_spent} min")
        else:
            st.info("No sessions recorded yet")
        
        # Display daily goal progress
        st.subheader("Daily Progress")
        
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
        daily_goal = c.fetchone()[0] or 120
        
        # Display progress
        progress = min(1.0, today_minutes / daily_goal)
        st.progress(progress)
        st.write(f"{today_minutes} / {daily_goal} min ({int(progress * 100)}%)")
    
    # Close database connection
    conn.close()
