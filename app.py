import os
from flask import Flask, jsonify
import requests

app = Flask(__name__)

URUN_ID = "226924398"
HEDEF_FIYAT = float(os.environ.get("HEDEF_FIYAT", "1500"))


@app.route("/kontrol-et", methods=["GET"])
def fiyat_kontrol_et():
    api_url = f"https://www.bershka.com/itxrest/2/v1/shop/bershkatr/products/{URUN_ID}/stock"

    headers = {
        "User-Agent": "BershkaApp/10.4.0 (iPhone; iOS 16.6; Scale/3.00)",
        "Accept": "application/json",
        "Accept-Language": "tr-TR",
    }

    try:
        response = requests.get(api_url, headers=headers, timeout=15)

        if response.status_code == 200:
            data = response.json()

            price_info = data.get("price", {})
            guncel_fiyat = price_info.get("current", 0) / 100

            if guncel_fiyat == 0:
                guncel_fiyat = price_info.get("regular", 0) / 100

            if guncel_fiyat > 0 and guncel_fiyat <= HEDEF_FIYAT:
                return (
                    jsonify(
                        {
                            "durum": "INDIRIM_YAKALANDI",
                            "guncel_fiyat_tl": guncel_fiyat,
                            "hedef_fiyat_tl": HEDEF_FIYAT,
                            "mesaj": "Urun hedef fiyatin altina dustu!",
                        }
                    ),
                    200,
                )

            return (
                jsonify(
                    {
                        "durum": "BEKLEMEDE",
                        "guncel_fiyat_tl": guncel_fiyat,
                        "hedef_fiyat_tl": HEDEF_FIYAT,
                        "mesaj": "Fiyat henuz dusmedi. Takibe devam.",
                    }
                ),
                200,
            )

        return (
            jsonify(
                {
                    "durum": "BERSHKA_API_HATASI",
                    "mesaj": f"Bershka Mobil API hata kodu dondu: {response.status_code}",
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
    return "Bershka Mobile API Tracker is Active.", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)