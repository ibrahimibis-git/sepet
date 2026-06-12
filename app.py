import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask import Flask, jsonify
import requests

app = Flask(__name__)

# --- YAPILANDIRMA AYARLARI ---
# Render'da "Environment Variables" kýsmýndan bunlarý güvenlice yöneteceðiz
URUN_ID = os.environ.get("URUN_ID", "10123456")
HEDEF_FIYAT = float(os.environ.get("HEDEF_FIYAT", "1500"))

YONETICI_EMAIL = os.environ.get("YONETICI_EMAIL")
YONETICI_SIFRE = os.environ.get("YONETICI_SIFRE")
ALICI_EMAIL = os.environ.get("ALICI_EMAIL")


def mail_gonder(guncel_fiyat):
    if not YONETICI_EMAIL or not YONETICI_SIFRE:
        print("E-posta ayarlarý eksik!")
        return

    try:
        msg = MIMEMultipart()
        msg["From"] = YONETICI_EMAIL
        msg["To"] = ALICI_EMAIL
        msg["Subject"] = "Bershka Indirim Alarmi!"

        urun_link = (
            f"https://www.bershka.com/tr/cift-tarafli-ceket-p{URUN_ID}.html"
        )
        icerik = f"Müjde! Takip ettiðin Bershka ürünü {guncel_fiyat} TL'ye düþtü!\nÜrün Linki: {urun_link}"
        msg.attach(MIMEText(icerik, "plain"))

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(YONETICI_EMAIL, YONETICI_SIFRE)
        server.send_message(msg)
        server.quit()
        print("E-posta baþarýyla gönderildi.")
    except Exception as e:
        print(f"E-posta hatasý: {e}")


# Cron-job.org burayý tetikleyecek
@app.route("/kontrol-et", methods=["GET"])
def fiyat_kontrol_et():
    # Bershka Türkiye API Linki
    api_url = f"https://www.bershka.com/itxrest/2/v1/shop/bershkatr/products/{URUN_ID}/stock"

    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
        "Accept": "application/json",
    }

    try:
        response = requests.get(api_url, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()
            # Bershka kuruþ cinsinden verir, 100'e bölerek TL yapýyoruz
            guncel_fiyat = data.get("price", {}).get("current", 0) / 100

            if guncel_fiyat > 0 and guncel_fiyat <= HEDEF_FIYAT:
                mail_gonder(guncel_fiyat)
                return (
                    jsonify(
                        {
                            "durum": "basarili",
                            "mesaj": "Ýndirim bulundu, mail atýldý!",
                            "fiyat": guncel_fiyat,
                        }
                    ),
                    200,
                )

            return (
                jsonify(
                    {
                        "durum": "basarili",
                        "mesaj": "Fiyat henüz düþmedi.",
                        "fiyat": guncel_fiyat,
                    }
                ),
                200,
            )

        return (
            jsonify(
                {
                    "durum": "hata",
                    "mesaj": f"Bershka API hata kodu: {response.status_code}",
                }
            ),
            400,
        )

    except Exception as e:
        return jsonify({"durum": "hata", "detay": str(e)}), 500


# Ana sayfa (Render'ýn sitenin açýk olduðunu anlamasý için)
@app.route("/")
def home():
    return "Bershka Fiyat Takip Botu Aktif!", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)