import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
from io import BytesIO

st.set_page_config(layout="wide")
st.title("🕵️‍♂️ Telegram Kanal Tespit Aracı v4 (Agresif Mod)")

with st.form("tarama_formu"):
    keyword = st.text_input("Kanal Anahtar Kelimesi:", "bilim")
    submitted = st.form_submit_button("Taramayı Başlat")

def agresif_kanal_tara(kelime):
    kanallar = set()
    # Doğrudan Telegram Dizin Siteleri (Arama motoru değil, dizin veritabanı)
    dizinler = [
        f"https://tlgrm.eu/channels?search={kelime}",
        f"https://telegramchannels.me/search?q={kelime}"
    ]
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    
    for url in dizinler:
        try:
            r = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(r.text, 'html.parser')
            for a in soup.find_all('a', href=True):
                if '/channel/' in a['href'] or '/channels/' in a['href']:
                    isim = a['href'].split('/')[-1]
                    if len(isim) > 5 and isim not in ['category', 'search', 'add']:
                        kanallar.add(f"https://t.me/{isim}")
        except: continue
    return list(kanallar)

if submitted:
    with st.spinner("Telegram dizinleri taranıyor..."):
        sonuclar = agresif_kanal_tara(keyword)
        if sonuclar:
            st.session_state['kanallar'] = sonuclar
            st.success(f"✅ {len(sonuclar)} kanal bulundu!")
            st.write(sonuclar)
        else:
            st.error("Kanal bulunamadı. Lütfen daha genel bir kelime (örn: 'haber') deneyin.")
