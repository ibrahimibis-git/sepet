import os
from flask import Flask, jsonify
import requests

app = Flask(__name__)

# --- YAPILANDIRMA AYARLARI ---
# Render'da "Environment Variables" kýsmýndan yönetebilirsiniz.
# Deðer girilmezse varsayýlan olarak gönderdiðin gömlek kodunu (226924398) kullanýr.
URUN_ID = os.environ.get("URUN_ID", "226924398")
HEDEF_FIYAT = float(os.environ.get("HEDEF_FIYAT", "1500"))


@app.route("/kontrol-et", methods=["GET"])
def fiyat_kontrol_et():
    # Bershka Türkiye stok/fiyat API linki
    api_url = f"https://www.bershka.com/itxrest/2/v1/shop/bershkatr/products/{URUN_ID}/stock"

    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
        "Accept": "application/json",
    }

    try:
        response = requests.get(api_url, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()
            # Bershka kuruþ cinsinden verir (Örn: 129900), 100'e bölerek TL yapýyoruz
            guncel_fiyat = data.get("price", {}).get("current", 0) / 100

            # 1. DURUM: ÝNDÝRÝM VAR
            if guncel_fiyat > 0 and guncel_fiyat <= HEDEF_FIYAT:
                # Render loglarýna büyük harflerle uyarý basar
                print(
                    f"\n!!! ALARM !!! URUNDE INDIRIM VAR! Guncel Fiyat: {guncel_fiyat} TL (Hedef: {HEDEF_FIYAT} TL)\n"
                )

                # Tarayýcý ekranýna vereceði yanýt
                return (
                    jsonify(
                        {
                            "durum": "INDIRIM_YAKALANDI",
                            "mesaj": "Müjde! Ürün hedef fiyatýn altýna düþtü!",
                            "guncel_fiyat_tl": guncel_fiyat,
                            "hedef_fiyat_tl": HEDEF_FIYAT,
                            "urun_kodu": URUN_ID,
                        }
                    ),
                    200,
                )

            # 2. DURUM: FÝYAT HENÜZ DÜÞMEDÝ
            print(
                f"Fiyat kontrol edildi: {guncel_fiyat} TL. Hedef fiyat ({HEDEF_FIYAT} TL) henüz aþýlmadý."
            )
            return (
                jsonify(
                    {
                        "durum": "BEKLEMEDE",
                        "mesaj": "Fiyat henüz düþmedi. Takibe devam...",
                        "guncel_fiyat_tl": guncel_fiyat,
                        "hedef_fiyat_tl": HEDEF_FIYAT,
                    }
                ),
                200,
            )

        # 3. DURUM: BERSHKA SUNUCUSU HATA VERDÝ
        print(f"Bershka API Hata Kodu: {response.status_code}")
        return (
            jsonify(
                {
                    "durum": "BERSHKA_HATASI",
                    "mesaj": f"Bershka sunucusu hata kodu döndürdü: {response.status_code}",
                }
            ),
            400,
        )

    except Exception as e:
        print(f"Sistem Hatasý: {str(e)}")
        return (
            jsonify(
                {
                    "durum": "SISTEM_HATASI",
                    "mesaj": "Kod çalýþýrken bir hata oluþtu.",
                    "detay": str(e),
                }
            ),
            500,
        )


# Ana sayfa (Render'ýn sitenin açýk olduðunu anlamasý için)
@app.route("/")
def home():
    return (
        "Bershka Fiyat Takip Sistemi Aktif! Kontrol için /kontrol-et sayfasýna gidin.",
        200,
    )


if __name__ == "__main__":
    # Render'ýn dinamik port hatasýný (status 1) engellemek için bu yapý þarttýr
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)