from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import os
import json
from google.oauth2.credentials import Credentials

SCOPES = ['https://www.googleapis.com/auth/drive.file']
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.json'

def authenticate_google_drive():
    creds = None
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'r') as token_file:
            creds = Credentials.from_authorized_user_info(json.load(token_file), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, 'w') as token_file:
            token_file.write(creds.to_json())
    return build('drive', 'v3', credentials=creds)

def upload_to_google_drive(filename):
    service = authenticate_google_drive()
    file_metadata = {'name': filename, 'mimeType': 'application/json'}
    media = MediaFileUpload(filename, mimetype='application/json')
    try:
        file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        print(f"Backup successful: {filename} - File ID: {file.get('id')}")
    except Exception as e:
        print(f"Error uploading to Google Drive: {e}")
