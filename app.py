import os
from bs4 import BeautifulSoup
from flask import Flask, jsonify
import requests

app = Flask(__name__)

# Config - No Turkish characters allowed here
TARGET_URL = "https://www.bershka.com/tr/uzun-kollu-dar-kesim-g%C3%B6mlek-c0p226924398.html?colorId=250"
HEDEF_FIYAT = float(os.environ.get("HEDEF_FIYAT", "1500"))
SCRAPER_API_KEY = os.environ.get("SCRAPER_API_KEY")


@app.route("/kontrol-et", methods=["GET"])
def fiyat_kontrol_et():
    if not SCRAPER_API_KEY:
        return (
            jsonify(
                {
                    "durum": "SISTEM_HATASI",
                    "mesaj": "SCRAPER_API_KEY is missing in Render environment variables!",
                }
            ),
            500,
        )

    scraper_url = "https://api.scraperapi.com/"
    payload = {"api_key": SCRAPER_API_KEY, "url": TARGET_URL}

    try:
        response = requests.get(scraper_url, params=payload, timeout=30)

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")

            # Look for standard SEO meta price tags
            meta_price = soup.find(
                "meta", property="product:price:amount"
            ) or soup.find("meta", attrs={"name": "twitter:data1"})

            if meta_price:
                fiyat_metni = meta_price.get("content", "0").strip()
                fiyat_metni = (
                    fiyat_metni.replace("TL", "")
                    .replace(" ", "")
                    .replace(",", ".")
                )
                guncel_fiyat = float(fiyat_metni)
            else:
                # Backup selector
                fiyat_elementi = soup.find(
                    "span", {"class": "current-price-elem"}
                )
                if fiyat_elementi:
                    fiyat_metni = (
                        fiyat_elementi.text.strip()
                        .replace("TL", "")
                        .replace(".", "")
                        .replace(",", ".")
                    )
                    guncel_fiyat = float(fiyat_metni.split()[0])
                else:
                    return (
                        jsonify(
                            {
                                "durum": "HTML_AYRISTIRMA_HATASI",
                                "mesaj": "Price metadata could not be found on the page.",
                            }
                        ),
                        500,
                    )

            # Price Comparison
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
                        "mesaj": "Fiyat henuz dusmedi. Takibe devam...",
                        "guncel_fiyat_tl": guncel_fiyat,
                        "hedef_fiyat_tl": HEDEF_FIYAT,
                    }
                ),
                200,
            )

        return (
            jsonify(
                {
                    "durum": "BERSHKA_BAGLANTI_HATASI",
                    "mesaj": f"Could not open Bershka page. Code: {response.status_code}",
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
    return "Bershka Web Scraper System is Active.", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)