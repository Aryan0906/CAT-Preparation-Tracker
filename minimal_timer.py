import streamlit as st
from datetime import datetime
import sqlite3
from utils import save_study_session, save_timer_session

def init_db():
    """Initialize database connection"""
    conn = sqlite3.connect('cat_prep.db')
    c = conn.cursor()
    
    # Ensure study_log table exists
    c.execute('''CREATE TABLE IF NOT EXISTS study_log
                 (date TEXT, topic TEXT, subtopic TEXT, time_spent INTEGER, notes TEXT)''')
    
    conn.commit()
    return conn

def show_focus_timer():
    """Display a minimal focus timer using the external Pomofocus.io service"""
    st.title("Focus Timer")
    
    # Initialize database connection
    conn = init_db()
    c = conn.cursor()
    
    # Topic selector for focus sessions
    topic = st.selectbox(
        "What are you working on?",
        ["VARC", "DILR", "Quant", "General Preparation", "Mock Test", "Other"]
    )
    
    # Embed only the timer part of Pomofocus.io in an iframe with custom CSS
    st.markdown("""
    <style>
    iframe {
        border: none;
        width: 100%;
        height: 500px;
        overflow: hidden;
    }
    </style>
    
    <div style="margin-bottom: 20px;">
        <iframe src="https://pomofocus.io/" scrolling="no"></iframe>
    </div>
    """, unsafe_allow_html=True)
    
    # Simple form to record completed sessions
    with st.form("record_session"):
        col1, col2 = st.columns([3, 1])
        
        with col1:
            minutes_spent = st.number_input("Minutes completed", min_value=1, max_value=180, value=25)
        
        with col2:
            record_button = st.form_submit_button("Save Session")
        
        if record_button:
            try:
                # Save to database
                save_study_session(topic, "", minutes_spent)
                st.success(f"Saved {minutes_spent} minutes of study on {topic}")
            except Exception as e:
                st.error(f"Error saving session: {str(e)}")
    
    # Close database connection
    conn.close()
