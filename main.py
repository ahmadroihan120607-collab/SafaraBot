import requests
from flask import Flask, request

app = Flask(__name__)

# --- ISI 3 DATA UTAMA ANDA LAGI (JANGAN SALAH) ---
# 1. Token WhatsApp
WA_TOKEN = "EAANGQvirNc4BQZCACaZAETHu8eZC3wlS4vXvuTEBl0mfzY7L7VW5IFAjrYkscH2NAKcJTJSCLKPtKUkOChhrr2VOZCmYEQ5YgikDs7xZA6hx8VWHh2mRYKZA0Cli5PPOjqGsWJL0ZC4kXcUZBzfpr9KDtd5QHnDZA9qUgDg5BR9LZCz1sLzL7lGADzVwgFzOD0ipqKHAZDZD"

# 2. ID Nomor Telepon
PHONE_ID = "938565982682894"

# 3. Gemini API Key
GEMINI_KEY = "AIzaSyBbTn4l_pG-w2-__zzflY8pIXZgbXOtVBg"

# 4. Password (Biarkan)
VERIFY_TOKEN = "safarapassword"
# -------------------------------------------------

@app.route("/")
def home():
    return "Bot Safara 2.0 (Super Cepat) Sudah Aktif!", 200

@app.route("/webhook", methods=["GET"])
def verify_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    else:
        return "Gagal", 403

@app.route("/webhook", methods=["POST"])
def receive_message():
    data = request.json
    try:
        if data.get("entry") and data["entry"][0].get("changes") and \
           data["entry"][0]["changes"][0].get("value") and \
           data["entry"][0]["changes"][0]["value"].get("messages"):

            message_data = data["entry"][0]["changes"][0]["value"]["messages"][0]
            sender_id = message_data["from"]
            text_body = message_data["text"]["body"]

            print(f"User: {text_body}")

            # 1. PANGGIL GEMINI 2.0 FLASH (SESUAI HASIL SCAN)
            jawaban_ai = tanya_gemini(text_body)

            # 2. KIRIM KE WA
            send_whatsapp_message(sender_id, jawaban_ai)

        return "OK", 200
    except Exception as e:
        print(f"Error: {e}")
        return "OK", 200

def tanya_gemini(pertanyaan):
    try:
        # PERHATIKAN: Kita pakai 'gemini-2.0-flash' sesuai scan Anda
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_KEY}"
        headers = {"Content-Type": "application/json"}
        # --- OTAK SALES (VERSI HEMAT) ---
        prompt_sales = f"""
        PERAN: Kamu adalah Sales dari 'Royhan AI Agency'. Jawab to the point & ramah.

        DAFTAR HARGA:
        1. PAKET BASIC (Rp 500rb): Bot penjawab otomatis sederhana. Pengerjaan 1 hari.
        2. PAKET PRO (Rp 1 Juta): Bot AI Pintar (Gemini). Pengerjaan 3 hari.

        ATURAN:
        - Kalau ditanya harga, SEBUTKAN nominal di atas.
        - Kalau ditanya cara beli, jawab: "Transfer ke BCA Royhan".
        - JAWAB SINGKAT (Max 3 kalimat).

        User: {pertanyaan}
        """

        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt_sales
                }]
            }]
        }
        # ----------------------------------
        response = requests.post(url, headers=headers, json=payload)

        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"Error Google: {response.text}"
    except Exception:
        return "Maaf, saya sedang pusing."

def send_whatsapp_message(to, message):
    url = f"https://graph.facebook.com/v17.0/{PHONE_ID}/messages"
    headers = {"Authorization": f"Bearer {WA_TOKEN}", "Content-Type": "application/json"}
    data = {"messaging_product": "whatsapp", "to": to, "text": {"body": message}}
    requests.post(url, headers=headers, json=data)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)