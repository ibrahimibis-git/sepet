import os
import re
from flask import Flask, jsonify
import requests

app = Flask(__name__)

TARGET_URL = "https://www.bershka.com/tr/uzun-kollu-dar-kesim-g%C3%B6mlek-c0p226924398.html?colorId=250"
HEDEF_FIYAT = float(os.environ.get("HEDEF_FIYAT", "1500"))


@app.route("/kontrol-et", methods=["GET"])
def fiyat_kontrol_et():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "tr-TR,tr;q=0.9",
    }

    try:
        response = requests.get(TARGET_URL, headers=headers, timeout=15)

        if response.status_code != 200:
            return (
                jsonify(
                    {
                        "durum": "BERSHKA_BAGLANTI_HATASI",
                        "mesaj": f"Status code: {response.status_code}",
                    }
                ),
                response.status_code,
            )

        html_content = response.text
        match = re.search(r'"price"\s*:\s*"?(\d+[\.,]?\d*)"?', html_content)

        if match:
            fiyat_metni = match.group(1).replace(",", ".")
            guncel_fiyat = float(fiyat_metni)

            if guncel_fiyat > 10000:
                guncel_fiyat = guncel_fiyat / 100

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
                        "guncel_fiyat_tl": guncel_fiyat,
                        "hedef_fiyat_tl": HEDEF_FIYAT,
                        "mesaj": "Fiyat henuz dusmedi.",
                    }
                ),
                200,
            )

        return (
            jsonify(
                {
                    "durum": "AYRISTIRMA_HATASI",
                    "mesaj": "Price data not found in HTML.",
                }
            ),
            500,
        )

    except Exception as e:
        return (
            jsonify({"durum": "SISTEM_HATASI", "detay": str(e)}),
            500,
        )


@app.route("/")
def home():
    return "Bershka Safe Tracker is Active.", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)