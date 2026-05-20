from flask import Flask, request
import requests
import os
import pandas as pd

app = Flask(__name__)

WEBEX_BOT_TOKEN = os.getenv("WEBEX_BOT_TOKEN")

WEBEX_API_URL = "https://webexapis.com/v1/messages"

EXCEL_FILE = "germany_processes.xlsx"

# ==========================================
# LOAD EXCEL
# ==========================================

def load_excel():

    df = pd.read_excel(EXCEL_FILE)

    df.columns = [col.strip() for col in df.columns]

    return df

# ==========================================
# SEARCH FUNCTION
# ==========================================

def search_process(user_message):

    df = load_excel()

    user_message = user_message.lower()

    keyword_mapping = {
        "work hours": "Work hours",
        "part time": "Work hours",
        "full time": "Work hours",
        "job title": "Job Title",
        "title": "Job Title",
        "termination": "Termination",
        "resignation": "Termination",
        "work location": "Work Location",
        "location": "Work Location",
        "personal data": "Personal Data",
        "citizenship": "Personal Data"
    }

    matched_process = None

    for keyword, process_name in keyword_mapping.items():

        if keyword in user_message:
            matched_process = process_name
            break

    if not matched_process:

        return """
Germany Process Navigator

Sorry, I could not identify the process.

Try asking:
- work hours
- title change
- termination
- work location
"""

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

    return "No matching guidance found."

# ==========================================
# SEND MESSAGE
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

    response = requests.post(
        WEBEX_API_URL,
        headers=headers,
        json=data
    )

    print(response.status_code)

# ==========================================
# HOME
# ==========================================

@app.route('/')
def home():

    return "Germany Process Navigator is LIVE"

# ==========================================
# WEBHOOK
# ==========================================

@app.route('/webhook', methods=['POST'])
def webhook():

    try:

        data = request.json

        print(data)

        # IMPORTANT
        # Ignore bot's own messages
        if data['data'].get('personEmail', '').endswith('webex.bot'):

            print("Ignoring bot message")

            return "OK"

        room_id = data['data']['roomId']

        # Get actual message
        message_id = data['data']['id']

        headers = {
            "Authorization": f"Bearer {WEBEX_BOT_TOKEN}"
        }

        message_response = requests.get(
            f"https://webexapis.com/v1/messages/{message_id}",
            headers=headers
        )

        message_details = message_response.json()

        user_message = message_details.get('text', '')

        print(f"User Message: {user_message}")

        bot_response = search_process(user_message)

        send_webex_message(room_id, bot_response)

        return "OK"

    except Exception as e:

        print(str(e))

        return "ERROR"

# ==========================================
# START
# ==========================================

if __name__ == '__main__':

    port = int(os.environ.get("PORT", 5000))

    app.run(host='0.0.0.0', port=port)
