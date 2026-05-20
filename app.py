from flask import Flask, request
import requests
import os

app = Flask(__name__)

WEBEX_BOT_TOKEN = os.getenv("NjZlZWNjODItOTJlZC00ZDYyLWEwMmItNmY2YjdiMDdiNGI2ZDA5MzM2NGUtN2Zl_PF84_1eb65fdf-9643-417f-9974-ad72cae0e10f")

WEBEX_API_URL = "https://webexapis.com/v1/messages"

# ==========================================
# HOME
# ==========================================

@app.route('/')
def home():
    return "Germany Process Navigator is LIVE"

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
    print(response.text)

# ==========================================
# WEBHOOK
# ==========================================

@app.route('/webhook', methods=['POST'])
def webhook():

    try:

        print("WEBHOOK HIT")

        data = request.json

        print(data)

        room_id = data['data']['roomId']

        send_webex_message(
            room_id,
            "Germany Process Navigator is connected successfully!"
        )

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
