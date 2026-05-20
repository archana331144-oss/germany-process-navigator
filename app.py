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

    df.columns = [col.strip() for col in df.columns]

    return df

# ==========================================
# NORMALIZE TEXT
# ==========================================

def normalize_text(text):

    return re.sub(
        r'[^a-zA-Z0-9]',
        '',
        str(text).lower()
    )

# ==========================================
# FORMAT GUIDANCE
# ==========================================

def format_guidance(guidance_text):

    guidance_text = str(guidance_text).strip()

    # Remove unnecessary labels
    unwanted_labels = [
        "Process:",
        "process:",
        "Guidance:",
        "guidance:"
    ]

    for label in unwanted_labels:

        guidance_text = guidance_text.replace(
            label,
            ""
        )

    lines = guidance_text.split('\n')

    formatted_lines = []

    for line in lines:

        line = line.strip()

        if not line:
            continue

        # Remove existing bullets
        line = line.lstrip('•').strip()

        # Keep numbered steps clean
        if re.match(r'^\d+\)', line):

            formatted_lines.append(line)

        else:

            formatted_lines.append(f"• {line}")

    return "\n\n".join(formatted_lines)

# ==========================================
# SPLIT SPECIAL CONSIDERATIONS
# ==========================================

def split_special_considerations(text):

    text = str(text)

    special_patterns = [
        "special considerations:",
        "special consideration:",
        "important:",
        "note:"
    ]

    lower_text = text.lower()

    for pattern in special_patterns:

        if pattern in lower_text:

            split_index = lower_text.index(pattern)

            main_text = text[:split_index].strip()

            special_text = text[split_index:].strip()

            # Clean heading text
            special_text = re.sub(
                r'(?i)special considerations?:',
                '',
                special_text
            )

            special_text = re.sub(
                r'(?i)important:',
                '',
                special_text
            )

            special_text = re.sub(
                r'(?i)note:',
                '',
                special_text
            )

            return main_text, special_text.strip()

    return text, None

# ==========================================
# SEARCH PROCESS
# ==========================================

def search_process(user_message):

    df = load_excel()

    normalized_message = normalize_text(
        user_message
    )

    matched_row = None

    # ======================================
    # MATCH USING KEYWORDS
    # ======================================

    for index, row in df.iterrows():

        keywords = str(
            row['Keywords']
        ).split(',')

        for keyword in keywords:

            normalized_keyword = normalize_text(
                keyword
            )

            if (
                normalized_keyword in normalized_message
                or normalized_message in normalized_keyword
            ):

                matched_row = row
                break

        if matched_row is not None:
            break

    # ======================================
    # FALLBACK MATCH USING PROCESS NAME
    # ======================================

    if matched_row is None:

        for index, row in df.iterrows():

            process_name = str(
                row['Process']
            )

            normalized_process = normalize_text(
                process_name
            )

            if (
                normalized_process in normalized_message
                or normalized_message in normalized_process
            ):

                matched_row = row
                break

    # ======================================
    # NO MATCH FOUND
    # ======================================

    if matched_row is None:

        return """
I could not identify the process.

Try examples like:
• work hours
• work location
• job title
• termination
• compensation
"""

    # ======================================
    # FORMAT RESPONSE
    # ======================================

    raw_guidance = str(
        matched_row['German Specific steps']
    )

    process_text, special_text = split_special_considerations(
        raw_guidance
    )

    formatted_process = format_guidance(
        process_text
    )

    response = f"""
━━━━━━━━━━━━━━━━━━
PROCESS
━━━━━━━━━━━━━━━━━━

{formatted_process}
"""

    # ======================================
    # SPECIAL CONSIDERATIONS
    # ======================================

    if special_text:

        formatted_special = format_guidance(
            special_text
        )

        response += f"""


━━━━━━━━━━━━━━━━━━
SPECIAL CONSIDERATIONS
━━━━━━━━━━━━━━━━━━

{formatted_special}
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

        # Get actual user message
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
        bot_response = search_process(
            user_message
        )

        # Send response
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
