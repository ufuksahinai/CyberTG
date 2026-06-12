import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import time
from io import BytesIO
from fpdf import FPDF

# --- ÇÖKME ÖNLEYİCİ - DEĞİŞKENLERİ SABİTLE ---
hedef_kelime = ""
mesaj_kelimesi = ""

# --- ARAYÜZ YAPILANDIRMASI ---
st.set_page_config(page_title="Tam Bağımsız Telegram OSINT", page_icon="🕵️‍♂️", layout="wide")
st.title("🕵️‍♂️ Tam Bağımsız Telegram İstihbarat Aracı")
st.write("Google API veya Telegram girişi gerektirmez. %100 Anonim olarak açık kaynakları tarar.")
st.markdown("---")

# --- HAFIZA (SESSION STATE) ---
if 'bulunan_kanallar' not in st.session_state:
    st.session_state.bulunan_kanallar = []
if 'bulunan_mesajlar' not in st.session_state:
    st.session_state.bulunan_mesajlar = []
if 'tarama_bitti' not in st.session_state:
    st.session_state.tarama_bitti = False

# ==========================================
# KANAL TARAMA FONKSİYONU (SIFIR KÜTÜPHANE HATASI)
# ==========================================
def bagimsiz_kanal_ara(kelime, limit):
    kanallar = set()
    loglar = [] 
    sorgu = f'site:t.me "{kelime}"'
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    }

    # YÖNTEM 1: DUCKDUCKGO LITE
    try:
        url = "https://lite.duckduckgo.com/lite/"
        # requests kütüphanesi kodlamayı kendi yapar, urllib'e ihtiyaç duymaz.
        cevap = requests.post(url, data={'q': sorgu}, headers=headers, timeout=10)
        if cevap.status_code == 200:
            isimler = re.findall(r't\.me(?:%2F|/)([a-zA-Z0-9_]{5,})', cevap.text)
            for isim in isimler:
                kanallar.add(f"https://t.me/{isim}")
            loglar.append(f"✅ DuckDuckGo Lite: Başarıyla {len(isimler)} veri topladı.")
        else:
            loglar.append(f"❌ DuckDuckGo Lite Engelledi: HTTP Kodu {cevap.status_code}")
    except Exception as e:
        loglar.append("❌ DuckDuckGo Lite Bağlantı Hatası.")

    # YÖNTEM 2: SEARXNG (Özgür Motorlar)
    searx_motorlari = [
        "https://searx.be/search",
        "https://searx.tiekoetter.com/search",
        "https://search.mdosch.de/search"
    ]
    
    for motor in searx_motorlari:
        if len(kanallar) >= limit: break
        try:
            params = {'q': sorgu, 'format': 'json'}
            cevap = requests.get(motor, params=params, headers=headers, timeout=10)
            if cevap.status_code == 200:
                veriler = cevap.json()
                yeni_bulunan = 0
                for sonuc in veriler.get('results', []):
                    link = sonuc.get('url', '')
                    if "t.me/" in link:
                        eslesme = re.search(r't\.me(?:%2F|/)([a-zA-Z0-9_]{5,})', link)
                        if eslesme:
                            kanallar.add(f"https://t.me/{eslesme.group(1)}")
                            yeni_bulunan += 1
                loglar.append(f"✅ SearXNG ({motor.split('/')[2]}): {yeni_bulunan} veri topladı.")
            else:
                loglar.append(f"❌ SearXNG ({motor.split('/')[2]}): Engellendi.")
        except Exception:
            pass

    # KESİN TEMİZLİK
    temiz_kanallar = list()
    yasakli_kelimeler = [
        "share", "joinchat", "setlanguage", "socks", "search", "category", "contact", 
        "add", "top", "new", "adult", "video", "music", "books", "gaming", "blogs", 
        "education", "entertainment", "media", "politics", "business", "crypto", 
        "language", "sales", "suggest", "other", "index", "username", "art", "news", "about"
    ]
    
    for k in kanallar:
        isim = k.split('/')[-1].lower()
        if len(isim) >= 5 and isim not in yasakli_kelimeler:
            if not any(y in k.lower() for y in ["joinchat", "setlanguage", "share"]):
                temiz_kanallar.append(k)

    # GÖRSEL RAPOR EKRANI
    with st.expander("🔍 Geliştirici Raporu (Hangi Veri Nereden Çekildi?)", expanded=True):
        for log in loglar:
            if "❌" in log: st.error(log)
            else: st.success(log)
            
        if len(temiz_kanallar) == 0:
            st.warning("⚠️ Tarama çalıştı ancak motorlarda bu kelimeyle eşleşen Telegram davet linki bulunamadı.")

    return temiz_kanallar[:limit]


# ==========================================
# 1. AŞAMA: ARAYÜZ (FORM KULLANIMI)
# ==========================================
st.header("1. Aşama: Hedef Kanalların Tespiti")

with st.form("kanal_arama_formu"):
    col1, col2 = st.columns(2)
    with col1:
        hedef_kelime = st.text_input("Kanal Bulmak İçin Anahtar Kelime:", placeholder="Örn: bahis")
    with col2:
        kanal_limiti = st.selectbox("Bulunacak Maksimum Kanal Sayısı (Tahmini):", [20, 50, 100])
    
    kanal_arama_baslat = st.form_submit_button("🔍 Kanal Taramasını Başlat")

if kanal_arama_baslat:
    if hedef_kelime:
        with st.spinner(f"Açık kaynaklarda '{hedef_kelime}' için gizlice Telegram kanalları aranıyor..."):
            sonuclar = bagimsiz_kanal_ara(hedef_kelime, kanal_limiti)
            st.session_state.bulunan_kanallar = sonuclar
            st.session_state.bulunan_mesajlar = [] 
            st.session_state.tarama_bitti = False
    else:
        st.error("Lütfen arama yapmak için bir anahtar kelime girin.")

# ==========================================
# KANAL LİSTELEME VE 2. AŞAMAYA GEÇİŞ
# ==========================================
if len(st.session_state.bulunan_kanallar) > 0:
    st.success(f"✅ Başarılı! {len(st.session_state.bulunan_kanallar)} adet benzersiz Telegram kanalı tespit edildi.")
    with st.expander("Bulunan Kanalların Listesini Gör"):
        st.write(st.session_state.bulunan_kanallar)
    
    st.markdown("---")
    st.header("2. Aşama: Kanal İçi Mesaj Taraması (Kimliksiz)")
    
    with st.form("mesaj_arama_formu"):
        mesaj_kelimesi = st.text_input("Sohbet Geçmişinde Aranacak Kelime:", placeholder="Örn: iddaa")
        mesaj_arama_baslat = st.form_submit_button("💬 Sohbet Taramasını Başlat")

    def web_view_mesaj_tara(kanallar, aranacak_kelime):
        veriler = []
        aranacak_kelime_kucuk = aranacak_kelime.lower()
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        
        ilerleme = st.progress(0)
        for index, link in enumerate(kanallar):
            kanal_adi = link.split('t.me/')[-1].strip('/')
            web_url = f"https://t.me/s/{kanal_adi}"
            
            try:
                cevap = requests.get(web_url, headers=headers, timeout=10)
                if cevap.status_code == 200:
                    soup = BeautifulSoup(cevap.text, 'html.parser')
                    mesaj_bloklari = soup.find_all('div', class_='tgme_widget_message')
                    
                    for blok in mesaj_bloklari:
                        metin_div = blok.find('div', class_='tgme_widget_message_text')
                        if metin_div:
                            metin = metin_div.get_text(separator=' ', strip=True)
                            if aranacak_kelime_kucuk in metin.lower():
                                tarih_tag = blok.find('time')
                                tarih = tarih_tag['datetime'][:16].replace('T', ' ') if tarih_tag else "Bilinmeyen Tarih"
                                
                                veriler.append({
                                    "Kanal Adı": kanal_adi,
                                    "Kanal Linki": link,
                                    "Tarih": tarih,
                                    "Mesaj İçeriği": metin[:300] + "..."
                                })
            except Exception:
                pass 
                
            time.sleep(1) 
            ilerleme.progress((index + 1) / len(kanallar))
            
        return veriler

    if mesaj_arama_baslat:
        if mesaj_kelimesi:
            with st.spinner("Telegram Web Görünümü üzerinden mesajlar aranıyor..."):
                sonuclar = web_view_mesaj_tara(st.session_state.bulunan_kanallar, mesaj_kelimesi)
                st.session_state.bulunan_mesajlar = sonuclar
                st.session_state.tarama_bitti = True
        else:
            st.error("Lütfen aranacak mesaj kelimesini girin.")

# ==========================================
# 3. AŞAMA: SONUÇ RAPORLAMA VE İNDİRME
# ==========================================
if st.session_state.tarama_bitti:
    st.markdown("---")
    st.header("📊 Tarama Sonuçları")
    
    if len(st.session_state.bulunan_mesajlar) > 0:
        df = pd.DataFrame(st.session_state.bulunan_mesajlar)
        st.dataframe(df, use_container_width=True)
        
        excel_output = BytesIO()
        with pd.ExcelWriter(excel_output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Bulgular')
        excel_data = excel_output.getvalue()
        
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="Anonim Telegram OSINT Raporu", ln=True, align='C')
        pdf.ln(10)
        
        for index, row in df.iterrows():
            metin = f"Kanal: {row['Kanal Adı']} | Tarih: {row['Tarih']}\nMesaj: {row['Mesaj İçeriği']}\n\n"
            temiz_metin = metin.encode('latin-1', 'replace').decode('latin-1')
            pdf.multi_cell(0, 10, txt=temiz_metin)
        
        pdf_data = pdf.output(dest='S').encode('latin-1')

        st.success("Taramalar başarıyla raporlandı! Aşağıdan dosyalarınızı indirebilirsiniz.")
        col_ex, col_pdf = st.columns(2)
        with col_ex:
            st.download_button(label="📥 Excel Olarak İndir", data=excel_data, file_name="telegram_rapor.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        with col_pdf:
            st.download_button(label="📄 PDF Olarak İndir", data=pdf_data, file_name="telegram_rapor.pdf", mime="application/pdf")
    else:
        st.warning(f"Belirlediğiniz kanalların son güncel mesajları arasında aranan kelimeye rastlanmadı.")
