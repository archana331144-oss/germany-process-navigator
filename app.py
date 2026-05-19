from flask import Flask, request
import pandas as pd
import requests
import os

app = Flask(__name__)

# ==========================================
# LOAD EXCEL
# ==========================================

EXCEL_FILE = "germany_processes.xlsx"

df = pd.read_excel(EXCEL_FILE)

df.columns = [col.strip() for col in df.columns]

print("Excel loaded successfully")
print(df.columns)

# ==========================================
# WEBEX CONFIG
# ==========================================

WEBEX_BOT_TOKEN = os.getenv("WEBEX_BOT_TOKEN")

WEBEX_API_URL = "https://webexapis.com/v1/messages"

# ==========================================
# SEARCH FUNCTION
# ==========================================

def search_process(user_message):

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

    print(f"Matched Process: {matched_process}")

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
# SEND WEBEX MESSAGE
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

    print("Message sent to Webex")
    print(response.status_code)
    print(response.text)

# ==========================================
# HOME ROUTE
# ==========================================

@app.route('/')
def home():

    return "Germany Process Navigator is LIVE"

# ==========================================
# WEBHOOK ROUTE
# ==========================================

@app.route('/webhook', methods=['POST'])
def webhook():

    try:

        print("Webhook received")

        data = request.json

        print(data)

        room_id = data['data']['roomId']
        message_id = data['data']['id']

        headers = {
            "Authorization": f"Bearer {WEBEX_BOT_TOKEN}"
        }

        # Get full message details
        message_response = requests.get(
            f"https://webexapis.com/v1/messages/{message_id}",
            headers=headers
        )

        message_details = message_response.json()

        print("Message Details:")
        print(message_details)

        # Ignore bot messages
        if message_details.get('personEmail', '').endswith('webex.bot'):

            print("Ignoring bot message")

            return "OK"

        user_message = message_details.get('text', '')

        print(f"User Message: {user_message}")

        # Generate response
        bot_response = search_process(user_message)

        print(f"Bot Response: {bot_response}")

        # Send reply
        send_webex_message(room_id, bot_response)

        return "OK"

    except Exception as e:

        print("ERROR OCCURRED")
        print(str(e))

        return "ERROR"

# ==========================================
# START APP
# ==========================================

if __name__ == '__main__':

    app.run(host='0.0.0.0', port=5000)
