import os
from flask import Flask, jsonify
import requests

app = Flask(__name__)

URUN_ID = os.environ.get("URUN_ID", "226924398")
HEDEF_FIYAT = float(os.environ.get("HEDEF_FIYAT", "1500"))


@app.route("/kontrol-et", methods=["GET"])
def fiyat_kontrol_et():
    # Bershka'nin web uzerinden dogrudan sorgulama yapabilecegimiz alternatif api url yapisi
    api_url = f"https://www.bershka.com/itxrest/2/v1/shop/bershkatr/products/{URUN_ID}/stock"

    # Akamai ve Cloudflare engellerini asmak icin tarayici kimlik taklidi (Header Yapisi)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "tr-TR,tr;q=0.0,en-US;q=0.8,en;q=0.7",
        "Referer": f"https://www.bershka.com/tr/",
        "Origin": "https://www.bershka.com",
        "Sec-Ch-Ua": '"Not-A.Brand";v="99", "Chromium";v="124", "Google Chrome";v="124"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    }

    try:
        # Bir oturum (session) baslatarak cookieleri otomatik yonetmesini sagliyoruz
        session = requests.Session()
        response = session.get(api_url, headers=headers, timeout=15)

        if response.status_code == 200:
            data = response.json()
            guncel_fiyat = data.get("price", {}).get("current", 0) / 100

            if guncel_fiyat > 0 and guncel_fiyat <= HEDEF_FIYAT:
                return (
                    jsonify(
                        {
                            "durum": "INDIRIM_YAKALANDI",
                            "guncel_fiyat_tl": guncel_fiyat,
                            "hedef_fiyat_tl": HEDEF_FIYAT,
                        }
                    ),
                    200,
                )

            return (
                jsonify(
                    {
                        "durum": "BEKLEMEDE",
                        "mesaj": "Fiyat henuz dusmedi.",
                        "guncel_fiyat_tl": guncel_fiyat,
                        "hedef_fiyat_tl": HEDEF_FIYAT,
                    }
                ),
                200,
            )

        # Hata devam ederse durum kodunu ekrana bas
        return (
            jsonify(
                {
                    "durum": "BERSHKA_HATASI",
                    "mesaj": f"Bershka sunucusu hata kodu dondu: {response.status_code}",
                }
            ),
            response.status_code,
        )

    except Exception as e:
        return (
            jsonify({"durum": "SISTEM_HATASI", "detay": str(e)}),
            500,
        )


@app.route("/")
def home():
    return "Bershka Bot Sistemi Aktif.", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)