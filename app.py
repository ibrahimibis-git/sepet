import os
from bs4 import BeautifulSoup
from flask import Flask, jsonify
import requests

app = Flask(__name__)

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
                    "mesaj": "SCRAPER_API_KEY is missing!",
                }
            ),
            500,
        )

    scraper_url = "https://api.scraperapi.com/"
    # ultra_fast veya render=false modunu zorlayarak sayfayi hafif sekilde cekiyoruz
    payload = {
        "api_key": SCRAPER_API_KEY,
        "url": TARGET_URL,
        "keep_headers": "true",
    }

    try:
        # Sunucu tarafli beklemeyi 60 saniyeye cikariyoruz
        response = requests.get(scraper_url, params=payload, timeout=60)

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")

            # Inditex SEO meta fiyat tag kontrolu
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
                # Sayfa icindeki json verisinden fiyati ayiklama yedegi
                # Eger meta etiketleri sunucuda eksik gelirse saf metinde arayalim
                if "price" in response.text:
                    return (
                        jsonify(
                            {
                                "durum": "BEKLEMEDE",
                                "mesaj": "Sayfa geldi ancak meta ayiklanamadi. Loglari inceleyin.",
                                "html_boyutu": len(response.text),
                            }
                        ),
                        200,
                    )

                return (
                    jsonify(
                        {
                            "durum": "HTML_AYRISTIRMA_HATASI",
                            "mesaj": "Price metadata could not be found.",
                        }
                    ),
                    500,
                )

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
                    }
                ),
                200,
            )

        return (
            jsonify(
                {
                    "durum": "BERSHKA_BAGLANTI_HATASI",
                    "mesaj": f"Connection code: {response.status_code}",
                }
            ),
            response.status_code,
        )

    except requests.exceptions.Timeout:
        return (
            jsonify(
                {
                    "durum": "ZAMAN_ASIMI",
                    "mesaj": "ScraperAPI sunucusu zamaninda cevap vermedi. Tekrar deneyin.",
                }
            ),
            504,
        )
    except Exception as e:
        return (
            jsonify({"durum": "SISTEM_HATASI", "detay": str(e)}),
            500,
        )


@app.route("/")
def home():
    return "System Active.", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)