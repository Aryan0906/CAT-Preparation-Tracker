import os
import json
import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials

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
    """Setup Google Sheets configuration"""
    st.title("Google Sheets Configuration")
    
    if not os.path.exists('credentials.json'):
        st.warning("credentials.json not found!")
        st.write("Please follow these steps to set up Google Sheets integration:")
        st.markdown("""
        1. Go to [Google Cloud Console](https://console.cloud.google.com/)
        2. Create a new project
        3. Enable Google Sheets API and Google Drive API
        4. Create a service account:
            - Go to "APIs & Services" > "Credentials"
            - Click "Create Credentials" > "Service Account"
            - Fill in the details and click "Create"
        5. Create a key for the service account:
            - Click on the service account
            - Go to "Keys" tab
            - Click "Add Key" > "Create New Key"
            - Choose JSON format
            - Download the JSON file
        6. Rename the downloaded file to `credentials.json`
        7. Place it in this directory
        """)
        
        if st.button("Create credentials template"):
            create_credentials_template()
            st.success("Created credentials_template.json. Use this as a reference for the required format.")
            
            # Create a placeholder credentials file for demonstration
            with open('credentials.json', 'w') as f:
                f.write('{"type": "service_account", "project_id": "placeholder", "private_key_id": "placeholder", "private_key": "placeholder", "client_email": "placeholder@example.com", "client_id": "placeholder", "auth_uri": "https://accounts.google.com/o/oauth2/auth", "token_uri": "https://oauth2.googleapis.com/token", "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs", "client_x509_cert_url": "placeholder"}')
            st.info("Created a placeholder credentials.json file for demonstration purposes.")
        
        return False
    
    try:
        scope = ['https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
        client = gspread.authorize(creds)
        
        st.success("Successfully connected to Google Sheets!")
        
        # Display service account email
        with open('credentials.json', 'r') as f:
            creds_data = json.load(f)
            service_account_email = creds_data.get('client_email', '')
            
        st.info(f"Service Account Email: {service_account_email}")
        st.write("Share your Google Sheet with this email address to enable access.")
        
        # Google Sheet URL input
        sheet_url = st.text_input(
            "Enter your Google Sheet URL",
            value=st.session_state.get('sheet_url', ''),
            help="Example: https://docs.google.com/spreadsheets/d/your-sheet-id/edit"
        )
        
        if sheet_url:
            try:
                sheet = client.open_by_url(sheet_url)
                st.session_state.sheet_url = sheet_url
                st.success(f"Successfully connected to sheet: {sheet.title}")
                
                # Save configuration
                config = {
                    'sheet_url': sheet_url,
                    'service_account_email': service_account_email
                }
                with open('sheets_config.json', 'w') as f:
                    json.dump(config, f)
                
                return True
                
            except Exception as e:
                st.error(f"Error accessing sheet: {str(e)}")
                st.write("Make sure you've shared the sheet with the service account email above.")
                return False
                
    except Exception as e:
        st.error(f"Error with credentials: {str(e)}")
        return False

def get_sheet_client():
    """Get an authorized Google Sheets client"""
    try:
        if not os.path.exists('credentials.json'):
            # Create a placeholder credentials file for demonstration
            with open('credentials.json', 'w') as f:
                f.write('{"type": "service_account", "project_id": "placeholder", "private_key_id": "placeholder", "private_key": "placeholder", "client_email": "placeholder@example.com", "client_id": "placeholder", "auth_uri": "https://accounts.google.com/o/oauth2/auth", "token_uri": "https://oauth2.googleapis.com/token", "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs", "client_x509_cert_url": "placeholder"}')
            
        scope = ['https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
        client = gspread.authorize(creds)
        
        # Load saved sheet URL
        if os.path.exists('sheets_config.json'):
            with open('sheets_config.json', 'r') as f:
                config = json.load(f)
                sheet_url = config.get('sheet_url')
                if sheet_url:
                    return client.open_by_url(sheet_url)
        
        return None
        
    except Exception:
        return None

if __name__ == "__main__":
    setup_google_sheets()
