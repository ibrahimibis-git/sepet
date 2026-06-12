import os
from flask import Flask, jsonify
import requests

app = Flask(__name__)

URUN_ID = os.environ.get("URUN_ID", "226924398")
HEDEF_FIYAT = float(os.environ.get("HEDEF_FIYAT", "1500"))
SCRAPER_API_KEY = os.environ.get("SCRAPER_API_KEY")


@app.route("/kontrol-et", methods=["GET"])
def fiyat_kontrol_et():
    if not SCRAPER_API_KEY:
        return (
            jsonify(
                {
                    "durum": "SISTEM_HATASI",
                    "mesaj": "SCRAPER_API_KEY Render ortam degiskenlerine eklenmemis!",
                }
            ),
            500,
        )

    # Hedef Bershka Linki
    target_url = f"https://www.bershka.com/itxrest/2/v1/shop/bershkatr/products/{URUN_ID}/stock"

    # Istegi ScraperAPI uzerinden geciriyoruz. Onlar arka planda proxy ve header yonetimini yapiyor.
    scraper_url = "https://api.scraperapi.com/"
    payload = {"api_key": SCRAPER_API_KEY, "url": target_url}

    try:
        # ScraperAPI bazen proxy dondugu icin istek 10-15 saniye surebilir, timeout'u uzun tutuyoruz
        response = requests.get(scraper_url, params=payload, timeout=30)

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
                            "urun_kodu": URUN_ID,
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

        return (
            jsonify(
                {
                    "durum": "PROXY_HATASI",
                    "mesaj": f"ScraperAPI baglanti sorunu. Kod: {response.status_code}",
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
    return "Bershka Proxy Bot Sistemi Aktif.", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)