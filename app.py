import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import time
from io import BytesIO
from fpdf import FPDF

# --- ARAYÜZ YAPILANDIRMASI ---
st.set_page_config(page_title="Telegram OSINT", layout="wide")
st.title("🕵️‍♂️ Tam Bağımsız Telegram İstihbarat Aracı")

# --- HAFIZA (SESSION STATE) ---
if 'bulunan_kanallar' not in st.session_state: st.session_state['bulunan_kanallar'] = []
if 'bulunan_mesajlar' not in st.session_state: st.session_state['bulunan_mesajlar'] = []
if 'tarama_bitti' not in st.session_state: st.session_state['tarama_bitti'] = False

# --- KANAL TARAMA FONKSİYONU ---
def bagimsiz_kanal_ara(kelime, limit):
    kanallar = set()
    loglar = []
    sorgu = f'site:t.me "{kelime}"'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'}

    try:
        url = "https://lite.duckduckgo.com/lite/"
        cevap = requests.post(url, data={'q': sorgu}, headers=headers, timeout=10)
        if cevap.status_code == 200:
            isimler = re.findall(r't\.me(?:%2F|/)([a-zA-Z0-9_]{5,})', cevap.text)
            for isim in isimler: kanallar.add(f"https://t.me/{isim}")
            loglar.append("✅ DuckDuckGo Başarılı.")
    except: loglar.append("❌ DuckDuckGo Hatası.")

    # Temizlik
    yasakli = ["share", "joinchat", "setlanguage", "socks", "search", "category", "contact", "add", "top", "new", "adult", "video", "music", "books", "gaming", "blogs", "education", "entertainment", "media", "politics", "business", "crypto", "language", "sales", "suggest", "other", "index", "username", "art", "news", "about"]
    temiz = [k for k in kanallar if k.split('/')[-1].lower() not in yasakli]
    
    with st.expander("🔍 Geliştirici Raporu", expanded=True):
        for log in loglar: st.success(log)
    return temiz[:limit]

# --- ARAYÜZ ---
# Değişkenleri burada tanımlıyoruz
hedef_kelime = st.text_input("Anahtar Kelime:", key="input_kelime")
kanal_limiti = st.selectbox("Maksimum Kanal:", [20, 50, 100])

if st.button("🔍 Kanal Taramasını Başlat"):
    if hedef_kelime:
        with st.spinner("Taranıyor..."):
            sonuclar = bagimsiz_kanal_ara(hedef_kelime, kanal_limiti)
            st.session_state['bulunan_kanallar'] = sonuclar
            st.session_state['tarama_bitti'] = False
    else:
        st.error("Lütfen bir kelime girin.")

if len(st.session_state['bulunan_kanallar']) > 0:
    st.write(f"Bulunan: {len(st.session_state['bulunan_kanallar'])}")
    mesaj_kelimesi = st.text_input("Mesajda Aranacak Kelime:")
    if st.button("💬 Mesaj Taramasını Başlat"):
        # Mesaj tarama mantığı buraya eklenecek
        st.info("Kanal içi tarama başlatıldı...")
