import os
import json
import streamlit as st

# Comment out Google Sheets integration for now
# import gspread
# from oauth2client.service_account import ServiceAccountCredentials

# Application settings
APP_NAME = "CAT Preparation Tracker"
APP_VERSION = "1.0.0"
APP_AUTHOR = "Your Name"
APP_GITHUB = "https://github.com/yourusername/CAT-Preparation-Tracker"

# Database settings
DB_NAME = "cat_prep.db"

# Default user settings
DEFAULT_FOCUS_DURATION = 25  # minutes
DEFAULT_BREAK_DURATION = 5   # minutes
DEFAULT_DAILY_GOAL = 120     # minutes
DEFAULT_REMINDER_TIME = "09:00"

# CAT exam sections
CAT_SECTIONS = ["VARC", "DILR", "Quant"]

# Topic subtopics
TOPIC_SUBTOPICS = {
    "VARC": ["Reading Comprehension", "Vocabulary", "Grammar", "Critical Reasoning", "Para Jumbles", "Para Summary"],
    "DILR": ["Data Interpretation", "Logical Reasoning", "Data Sufficiency", "Puzzles", "Arrangements", "Games and Tournaments"],
    "Quant": ["Algebra", "Geometry", "Number Systems", "Arithmetic", "Modern Math", "Mensuration"]
}

# Color schemes
SECTION_COLORS = {
    "VARC": "#1f77b4",
    "DILR": "#ff7f0e",
    "Quant": "#2ca02c",
    "General": "#d62728"
}

def create_credentials_template():
    """Create a template credentials.json file"""
    credentials_template = {
        "type": "service_account",
        "project_id": "your-project-id",
        "private_key_id": "your-private-key-id",
        "private_key": "your-private-key",
        "client_email": "your-service-account-email",
        "client_id": "your-client-id",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "your-cert-url"
    }

    with open('credentials_template.json', 'w') as f:
        json.dump(credentials_template, f, indent=4)

def setup_google_sheets():
    """Setup Google Sheets configuration (currently disabled)"""
    st.title("Google Sheets Integration")
    st.info("Google Sheets integration is currently disabled in this version.")

    # Display placeholder form
    with st.form("google_sheets_form"):
        st.text_input("Google Sheets ID (disabled)", disabled=True)
        st.text_input("Credentials File Path (disabled)", disabled=True)
        st.form_submit_button("Save Settings (disabled)", disabled=True)

    # Information about enabling Google Sheets integration
    with st.expander("How to enable Google Sheets integration"):
        st.markdown("""
        To enable Google Sheets integration in a future version:

        1. Uncomment the Google Sheets imports in config.py
        2. Create a credentials.json file with your Google API credentials
        3. Share your Google Sheet with the service account email

        For more information, refer to the documentation.
        """)

    return False

def get_sheet_client():
    """Get an authorized Google Sheets client (currently disabled)"""
    # This function is a placeholder for Google Sheets integration
    # Currently disabled in this version
    return None

if __name__ == "__main__":
    setup_google_sheets()
