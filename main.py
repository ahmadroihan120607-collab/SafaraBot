import os
import requests
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
from flask import Flask, request

app = Flask(__name__)

# --- ISI 3 DATA UTAMA ANDA ---
WA_TOKEN = os.environ.get('WA_TOKEN')
PHONE_ID = "938565982682894"
GEMINI_KEY = os.environ.get('GEMINI_API_KEY')
VERIFY_TOKEN = "safarapassword"

# --- 5. KONEKSI GOOGLE SHEETS ---
try:
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    kredensial_json = json.loads(os.environ.get('GOOGLE_CREDENTIALS'))
    creds = ServiceAccountCredentials.from_json_keyfile_dict(kredensial_json, scope)
    gclient = gspread.authorize(creds)
    database = gclient.open("Database SafaraBot").sheet1
    print("Berhasil terhubung ke Google Sheets!")
except Exception as e:
    print("Gagal konek Sheets:", e)
# --------------------------------

@app.route("/")
def home():
    return "Mesin AI Chatbot Sudah Aktif!", 200

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

            # 1. PANGGIL GEMINI
            jawaban_ai = tanya_gemini(text_body)

            # 2. CEK KODE RAHASIA DARI GEMINI
            if "[SIMPAN_DATA]" in jawaban_ai:
                jawaban_bersih = jawaban_ai.replace("[SIMPAN_DATA]", "").strip()

                # Catat ke Sheets
                # --- Set Waktu ke WIB (Waktu Indonesia Barat) ---
                waktu_server = datetime.now()
                waktu_indonesia = waktu_server + timedelta(hours=7)
                waktu = waktu_indonesia.strftime("%Y-%m-%d %H:%M:%S")
                # ------------------------------------------------
                try:
                    database.append_row([waktu, sender_id, "Prospek Fix", text_body])
                    print("Data LENGKAP berhasil dicatat ke Sheets!")
                except Exception as e:
                    print("Gagal catat data:", e)

                send_whatsapp_message(sender_id, jawaban_bersih)

            else:
                send_whatsapp_message(sender_id, jawaban_ai)
                print("Chat biasa, tidak dicatat ke Sheets.")

        return "OK", 200
    except Exception as e:
        print(f"Error: {e}")
        return "OK", 200

def tanya_gemini(pertanyaan):
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_KEY}"
        headers = {"Content-Type": "application/json"}
        # --- OTAK SALES (VERSI PINTAR) ---
        prompt_sales = f"""
        PERAN: Kamu adalah Sales dari 'Royhan AI Agency'. Jawab ramah dan to the point.

        DAFTAR HARGA:
        1. PAKET BASIC (Rp 500rb)
        2. PAKET PRO (Rp 1 Juta)

        ATURAN WAJIB:
        1. Jika pelanggan menunjukkan ketertarikan untuk pesan, WAJIB langsung tanyakan 3 DATA INI SEKALIGUS dalam satu balasan: NAMA, ALAMAT, dan PILIHAN PAKET.
        2. Jangan pernah berikan nomor rekening jika ketiga data tersebut belum dijawab lengkap oleh pelanggan.
        3. JIKA dan HANYA JIKA pelanggan SUDAH membalas dengan Nama, Alamat, dan Paket, berikan ringkasan pesanannya, arahkan transfer ke BCA Royhan, dan WAJIB tambahkan kode rahasia ini di paling akhir kalimatmu: [SIMPAN_DATA]

        User: {pertanyaan}
        """
        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt_sales
                }]
            }]
        }

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