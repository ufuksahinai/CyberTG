import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time

st.set_page_config(layout="wide")
st.title("🕵️‍♂️ Telegram Kanal Tespit Aracı v6 (Final)")

# --- FONKSİYON ---
def hassas_tara(kelime, limit):
    kanallar = set()
    url = f"https://html.duckduckgo.com/html/?q=site:t.me {kelime}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        r = requests.post(url, data={'q': f'site:t.me {kelime}'}, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        for link in soup.select('.result__url'):
            url_text = link.get_text()
            if 't.me/' in url_text:
                kanal = url_text.split('t.me/')[-1].split('/')[0].split('?')[0]
                if len(kanal) > 3 and 's/' not in kanal:
                    kanallar.add(f"https://t.me/{kanal}")
    except Exception as e:
        st.error(f"Bağlantı Hatası: {e}")
    return list(kanallar)[:limit]

# --- ARAYÜZ (FORM İÇİNDE) ---
with st.form("arama_formu"):
    # Değişkenleri formun içinde tanımlıyoruz
    keyword = st.text_input("Arama Kelimesi:", "yapay zeka")
    limit = st.selectbox("Kaç kanal bulunsun?", [20, 50, 100])
    submit = st.form_submit_button("Tara")

# Butona basıldığında çalışır
if submit:
    if keyword:
        with st.spinner("Taranıyor..."):
            sonuclar = hassas_tara(keyword, limit)
            if sonuclar:
                st.session_state['bulunan_kanallar'] = sonuclar
                st.success(f"✅ {len(sonuclar)} kanal bulundu.")
                st.write(sonuclar)
            else:
                st.warning("Sonuç bulunamadı.")
    else:
        st.error("Lütfen bir kelime girin.")
