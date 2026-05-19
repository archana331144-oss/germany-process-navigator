from flask import Flask, request
import pandas as pd
import requests

app = Flask(__name__)

# ==========================================
# GERMANY PROCESS NAVIGATOR
# ==========================================

EXCEL_FILE = "germany_processes.xlsx"

# Load Excel
df = pd.read_excel(EXCEL_FILE)

# ==========================================
# WEBEX BOT TOKEN
# ==========================================

WEBEX_BOT_TOKEN = "NDhmZWNkNDUtMzI3NS00Yjc5LTkwNjQtNjI1M2ZiNGZiYWU1NTljNzU4YWMtMjM3_PF84_1eb65fdf-9643-417f-9974-ad72cae0e10f"

WEBEX_API_URL = "https://webexapis.com/v1/messages"

# ==========================================
# SEARCH FUNCTION
# ==========================================

def search_process(user_message):

    user_message = user_message.lower()

    for index, row in df.iterrows():

        process = str(row['Process']).lower()
        steps = str(row['German Specific steps'])

        # Match process names in user question
        if process in user_message:

            return f"""
Germany Process Navigator

Process Identified:
{row['Process']}

Germany Guidance:
{steps}
"""

    return """
Germany Process Navigator

Sorry, I could not identify the process.

Try asking:
- Work hours change
- Job title change
- Work location
- Termination
- Personal data
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

        # Get message text
        message_details = requests.get(
            f"https://webexapis.com/v1/messages/{message_id}",
            headers=headers
        ).json()

        user_message = message_details['text']

        # Ignore bot's own messages
        if message_details.get('personEmail', '').endswith('webex.bot'):
            return "OK"

        # Search Excel
        response = search_process(user_message)

        # Send response
        send_webex_message(room_id, response)

        return "OK"

    except Exception as e:
        print(e)
        return "ERROR"

# ==========================================
# RUN APP
# ==========================================

if __name__ == '__main__':

    print("Germany Process Navigator is running...")

    app.run(host='0.0.0.0', port=5000)
