from flask import Flask, request
import pandas as pd
import requests
import os

app = Flask(__name__)

# ==========================================
# GERMANY PROCESS NAVIGATOR
# ==========================================

EXCEL_FILE = "germany_processes.xlsx"

# Load Excel
df = pd.read_excel(EXCEL_FILE)

# Clean column names
df.columns = [col.strip() for col in df.columns]

# ==========================================
# WEBEX BOT TOKEN
# ==========================================

WEBEX_BOT_TOKEN = os.getenv("WEBEX_BOT_TOKEN")

WEBEX_API_URL = "https://webexapis.com/v1/messages"

# ==========================================
# SEARCH FUNCTION
# ==========================================

def search_process(user_message):

    user_message = user_message.lower()

    # Keyword mapping
    keyword_mapping = {
        "work hours": "Work hours",
        "part time": "Work hours",
        "full time": "Work hours",
        "job title": "Job Title",
        "title change": "Job Title",
        "termination": "Termination",
        "resignation": "Termination",
        "work location": "Work Location",
        "location": "Work Location",
        "personal data": "Personal Data",
        "citizenship": "Personal Data"
    }

    matched_process = None

    # Identify matching process
    for keyword, process_name in keyword_mapping.items():

        if keyword in user_message:
            matched_process = process_name
            break

    # No match found
    if not matched_process:

        return """
Germany Process Navigator

Sorry, I could not identify the process.

Try asking:
- work hours
- part time
- title change
- termination
- work location
"""

    # Search Excel
    for index, row in df.iterrows():

        process = str(row['Process'])

        if matched_process.lower() in process.lower():

            return f"""
Germany Process Navigator

Process Identified:
{row['Process']}

Germany Guidance:
{row['German Specific steps']}
"""

    return """
Germany Process Navigator

Process found but no guidance available.
"""

# ==========================================
# SEND MESSAGE TO WEBEX
# ==========================================

def send_webex_message(room_id, message):

    headers = {
        "Authorization": f"Bearer {WEBEX_BOT_TOKEN}",
        "Content-Type": "application/json"
    }

    data = {
        "roomId": room_id,
        "text": message
    }

    requests.post(
        WEBEX_API_URL,
        headers=headers,
        json=data
    )

# ==========================================
# WEBHOOK
# ==========================================

@app.route('/webhook', methods=['POST'])
def webhook():

    data = request.json

    try:

        room_id = data['data']['roomId']
        message_id = data['data']['id']

        headers = {
            "Authorization": f"Bearer {WEBEX_BOT_TOKEN}"
        }

        # Get message details
        message_details = requests.get(
            f"https://webexapis.com/v1/messages/{message_id}",
            headers=headers
        ).json()

        user_message = message_details['text']

        print(f"User message: {user_message}")

        # Ignore bot's own messages
        if message_details.get('personEmail', '').endswith('webex.bot'):
            return "OK"

        # Search process
        response = search_process(user_message)

        print(f"Bot response: {response}")

        # Send reply
        send_webex_message(room_id, response)

        return "OK"

    except Exception as e:

        print(f"ERROR: {e}")

        return "ERROR"

# ==========================================
# HOME ROUTE
# ==========================================

@app.route('/')
def home():

    return "Germany Process Navigator is live!"

# ==========================================
# RUN APP
# ==========================================

if __name__ == '__main__':

    print("Germany Process Navigator is running...")

    app.run(host='0.0.0.0', port=5000)
