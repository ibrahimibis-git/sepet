import os
from bs4 import BeautifulSoup
from flask import Flask, jsonify
import requests

app = Flask(__name__)

# Gömleðin doðrudan web linki
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
                    "mesaj": "SCRAPER_API_KEY Render ortam degiskenlerine eklenmemis!",
                }
            ),
            500,
        )

    # Istegi ScraperAPI uzerinden dogrudan web sayfasina atiyoruz
    scraper_url = "https://api.scraperapi.com/"
    payload = {"api_key": SCRAPER_API_KEY, "url": TARGET_URL}

    try:
        response = requests.get(scraper_url, params=payload, timeout=30)

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")

            # Inditex sitelerinde fiyat bilgisi genellikle bir meta etiketinde saklanir.
            # <meta property="product:price:amount" content="1299.00"> yapisini ariyoruz.
            meta_price = soup.find(
                "meta", property="product:price:amount"
            ) or soup.find("meta", attrs={"name": "twitter:data1"})

            if meta_price:
                # Meta etiketinin content degerini alip temizliyoruz
                fiyat_metni = meta_price.get("content", "0").strip()
                # Sadece rakamlari ve noktayi birakacak sekilde temizleme yapalim
                fiyat_metni = (
                    fiyat_metni.replace("TL", "")
                    .replace(" ", "")
                    .replace(",", ".")
                )
                guncel_fiyat = float(fiyat_metni)
            else:
                # Alternatif olarak sayfa icindeki fiyat class'ini aramayi deneyelim
                # Inditex dinamik oldugu icin meta her zaman daha guvenlidir ama yedek olarak dursun
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
                                "mesaj": "Sayfa basariyla indirildi ancak icinde fiyat etiketi bulunamadi. Bershka tasarim degistirmis olabilir.",
                            }
                        ),
                        500,
                    )

            # Fiyat Karsilastirma
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
                    "durum": "BERSHKA_BAGLANTI_HATASI",
                    "mesaj": f"Bershka sayfasi acilamadi. Kod: {response.status_code}",
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
    return "Bershka Web Scraper Sistemi Aktif.", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)