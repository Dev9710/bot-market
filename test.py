import requests

TOKEN = "8451477317:AAFlppZm7GHGeV2Uv_gR7qfpDkDwONPktVM"
CHAT = "5636697170"

resp = requests.post(
    f"https://api.telegram.org/bot{TOKEN}/sendMessage",
    data={"chat_id": CHAT, "text": "🔥 Test Telegram OK – bon bot !"},
)

print(resp.text)
