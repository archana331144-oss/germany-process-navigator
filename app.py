from flask import Flask, request
import requests
import os
import pandas as pd
import re

app = Flask(__name__)

# ==========================================
# CONFIG
# ==========================================

WEBEX_BOT_TOKEN = os.getenv("WEBEX_BOT_TOKEN")

WEBEX_API_URL = "https://webexapis.com/v1/messages"

EXCEL_FILE = "germany_processes.xlsx"

# ==========================================
# LOAD EXCEL
# ==========================================

def load_excel():

    df = pd.read_excel(EXCEL_FILE)

    # Clean column names
    df.columns = [col.strip() for col in df.columns]

    return df

# ==========================================
# NORMALIZE TEXT
# ==========================================

def normalize_text(text):

    return re.sub(
        r'[^a-zA-Z0-9]',
        '',
        text.lower()
    )

# ==========================================
# FORMAT GUIDANCE
# ==========================================

def format_guidance(guidance_text):

    guidance_text = str(guidance_text).strip()

    # Split into lines
    lines = guidance_text.split('\n')

    cleaned_lines = []

    for line in lines:

        line = line.strip()

        if line:

            cleaned_lines.append(f"• {line}")

    return "\n".join(cleaned_lines)

# ==========================================
# SEARCH PROCESS
# ==========================================

def search_process(user_message):

    df = load_excel()

    normalized_message = normalize_text(user_message)

    matched_row = None

    # Flexible matching against all process names
    for index, row in df.iterrows():

        process_name = str(row['Process'])

        normalized_process = normalize_text(process_name)

        if (
            normalized_process in normalized_message
            or normalized_message in normalized_process
        ):

            matched_row = row
            break

    # No process found
    if matched_row is None:

        return """
Germany Process Navigator

I could not identify the process.

Try examples like:
• work hours
• work location
• job title
• termination
• compensation
"""

    # Extract guidance
    guidance = format_guidance(
        matched_row['German Specific steps']
    )

    # Structured response
    response = f"""
Germany Process Navigator

━━━━━━━━━━━━━━━
GUIDANCE
━━━━━━━━━━━━━━━

{guidance[:1500]}

━━━━━━━━━━━━━━━
IMPORTANT CHECKS
━━━━━━━━━━━━━━━

• Validate approvals if required
• Ensure Germany-specific compliance checks
• Review supporting documentation before processing
"""

    return response

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
        if data['data'].get(
            'personEmail',
            ''
        ).endswith('webex.bot'):

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

        user_message = message_details.get(
            'text',
            ''
        )

        print(f"User Message: {user_message}")

        # Generate response
        bot_response = search_process(user_message)

        # Send reply
        send_webex_message(
            room_id,
            bot_response
        )

        return "OK"

    except Exception as e:

        print(str(e))

        return "ERROR"

# ==========================================
# START APP
# ==========================================

if __name__ == '__main__':

    port = int(
        os.environ.get("PORT", 5000)
    )

    app.run(
        host='0.0.0.0',
        port=port
    )
