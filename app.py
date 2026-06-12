import os
from flask import Flask, jsonify
import requests

app = Flask(__name__)

# Config
URUN_ID = os.environ.get("URUN_ID", "226924398")
HEDEF_FIYAT = float(os.environ.get("HEDEF_FIYAT", "1500"))


@app.route("/kontrol-et", methods=["GET"])
def fiyat_kontrol_et():
    api_url = f"https://www.bershka.com/itxrest/2/v1/shop/bershkatr/products/{URUN_ID}/stock"

    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
        "Accept": "application/json",
    }

    try:
        response = requests.get(api_url, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()
            guncel_fiyat = data.get("price", {}).get("current", 0) / 100

            # 1. DURUM: INDIRIM VAR
            if guncel_fiyat > 0 and guncel_fiyat <= HEDEF_FIYAT:
                print(
                    f"ALARM: INDIRIM YAKALANDI! Fiyat: {guncel_fiyat} TL, Hedef: {HEDEF_FIYAT} TL"
                )
                return (
                    jsonify(
                        {
                            "durum": "INDIRIM_YAKALANDI",
                            "mesaj": "Urun hedef fiyatin altina dustu!",
                            "guncel_fiyat_tl": guncel_fiyat,
                            "hedef_fiyat_tl": HEDEF_FIYAT,
                            "urun_kodu": URUN_ID,
                        }
                    ),
                    200,
                )

            # 2. DURUM: BEKLEMEDE
            print(
                f"Fiyat kontrol edildi: {guncel_fiyat} TL. Beklemede..."
            )
            return (
                jsonify(
                    {
                        "durum": "BEKLEMEDE",
                        "mesaj": "Fiyat henuz dusmedi. Takibe devam...",
                        "guncel_fiyat_tl": guncel_fiyat,
                        "hedef_fiyat_tl": HEDEF_FIYAT,
                    }
                ),
                200,
            )

        print(f"Bershka API Hata Kodu: {response.status_code}")
        return (
            jsonify(
                {
                    "durum": "BERSHKA_HATASI",
                    "mesaj": f"Bershka sunucusu hata kodu dondu: {response.status_code}",
                }
            ),
            400,
        )

    except Exception as e:
        print(f"Sistem Hatasi: {str(e)}")
        return (
            jsonify(
                {
                    "durum": "SISTEM_HATASI",
                    "mesaj": "Kod calisirken bir hata olustu.",
                    "detay": str(e),
                }
            ),
            500,
        )


@app.route("/")
def home():
    return (
        "Bershka Fiyat Takip Sistemi Aktif! Kontrol icin /kontrol-et sayfasina gidin.",
        200,
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)