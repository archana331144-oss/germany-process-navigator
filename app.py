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

    # Normalize input
    cleaned_message = user_message.lower().strip()

    # Remove spaces for flexible matching
    compact_message = cleaned_message.replace(" ", "")

    # Keyword variations
    keyword_mapping = {
        "workhours": "Work hours",
        "parttime": "Work hours",
        "fulltime": "Work hours",

        "jobtitle": "Job Title",
        "titlechange": "Job Title",

        "termination": "Termination",
        "resignation": "Termination",

        "worklocation": "Work Location",
        "locationchange": "Work Location",

        "personaldata": "Personal Data",
        "citizenship": "Personal Data",

        "bankdetails": "Bank Details",
        "compensation": "Compensation",
        "promotion": "Promotion",
        "leave": "Leave"
    }

    matched_process = None

    # Flexible keyword matching
    for keyword, process_name in keyword_mapping.items():

        if keyword in compact_message:
            matched_process = process_name
            break

    # Fallback matching using Excel process names
    if not matched_process:

        for index, row in df.iterrows():

            process_name = str(row['Process']).lower()

            process_compact = process_name.replace(" ", "")

            if process_compact in compact_message:
                matched_process = row['Process']
                break

    # No match found
    if not matched_process:

        return """
Germany Process Navigator

I could not identify the process.

Try:
• work hours
• title change
• work location
• termination
• compensation
"""

    # Find matching process in Excel
    for index, row in df.iterrows():

        process = str(row['Process'])

        if matched_process.lower() in process.lower():

            guidance = str(row['German Specific steps']).strip()

            guidance = guidance.replace("•", "\n•")

            return f"""
Germany Process Navigator

Process:
{row['Process']}

Key Guidance:
{guidance[:1200]}
"""

    return """
Germany Process Navigator

No guidance found for this process.
"""

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

        # Ignore bot's own messages
        if data['data'].get('personEmail', '').endswith('webex.bot'):

            print("Ignoring bot message")

            return "OK"

        room_id = data['data']['roomId']

        message_id = data['data']['id']

        headers = {
            "Authorization": f"Bearer {WEBEX_BOT_TOKEN}"
        }

        # Get actual message text
        message_response = requests.get(
            f"https://webexapis.com/v1/messages/{message_id}",
            headers=headers
        )

        message_details = message_response.json()

        user_message = message_details.get('text', '')

        print(f"User Message: {user_message}")

        # Generate response
        bot_response = search_process(user_message)

        # Send reply
        send_webex_message(room_id, bot_response)

        return "OK"

    except Exception as e:

        print(str(e))

        return "ERROR"

# ==========================================
# START APP
# ==========================================

if __name__ == '__main__':

    port = int(os.environ.get("PORT", 5000))

    app.run(host='0.0.0.0', port=port)
