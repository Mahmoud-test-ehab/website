from flask import Flask, render_template, redirect, url_for, request, session
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import datetime
import os

# Define the scopes required for accessing Calendar and Drive
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly', 'https://www.googleapis.com/auth/drive.readonly']

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Used for session management

# Load credentials from the OAuth client
def authenticate_google_account():
    # Check if we have valid credentials stored
    creds = None
    if 'credentials' in session:
        creds = session['credentials']
    if not creds or not creds.valid:
        # If no valid credentials are available, let the user log in
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
        session['credentials'] = creds
    return creds

# Fetch the next lecture event from Google Calendar
def get_next_lecture(creds):
    try:
        service = build('calendar', 'v3', credentials=creds)
        now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
        events = service.events().list(calendarId='primary', timeMin=now, maxResults=1, singleEvents=True, orderBy='startTime').execute()
        items = events.get('items', [])
        if not items:
            return None
        return items[0]
    except HttpError as error:
        print(f"An error occurred: {error}")
        return None

# Fetch the list of recorded meetings from Google Drive
def get_drive_files(creds):
    try:
        service = build('drive', 'v3', credentials=creds)
        # You need to replace with your Google Drive folder ID
        folder_id = 'your-folder-id'
        query = f"'{folder_id}' in parents"
        results = service.files().list(q=query).execute()
        return results.get('files', [])
    except HttpError as error:
        print(f"An error occurred: {error}")
        return []

# Route for OAuth login
@app.route('/login')
def login():
    flow = InstalledAppFlow.from_client_secrets_file(
        'credentials.json', SCOPES)
    auth_url, _ = flow.authorization_url(prompt='consent')
    return redirect(auth_url)

# Route to handle OAuth2 callback and save credentials
@app.route('/oauth2callback')
def oauth2callback():
    flow = InstalledAppFlow.from_client_secrets_file(
        'credentials.json', SCOPES)
    creds = flow.fetch_token(authorization_response=request.url)
    session['credentials'] = creds
    return redirect(url_for('index'))

# Route to display the main page
@app.route('/')
def index():
    creds = authenticate_google_account()
    next_lecture = get_next_lecture(creds)
    recordings = get_drive_files(creds)

    countdown_time = ""
    if next_lecture:
        # Calculate time remaining for the next lecture
        lecture_time = datetime.datetime.fromisoformat(next_lecture['start']['dateTime'])
        remaining_time = lecture_time - datetime.datetime.utcnow()
        countdown_time = str(remaining_time).split(".")[0]  # Format countdown

    return render_template('index.html', countdown_time=countdown_time, recordings=recordings)

if __name__ == '__main__':
    app.run(debug=True)
