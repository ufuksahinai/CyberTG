import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time

st.set_page_config(layout="wide")
st.title("🕵️‍♂️ Telegram Kanal Tespit Aracı v5 (Nokta Atışı)")

with st.form("arama_formu"):
    keyword = st.text_input("Arama Kelimesi:", "yapay zeka")
    submit = st.form_submit_button("Tara")

def hassas_tara(kelime):
    kanallar = set()
    # DuckDuckGo'nun HTML arama sonuçlarını hedefliyoruz (Botlara en dayanıklı olan)
    url = f"https://html.duckduckgo.com/html/?q=site:t.me {kelime}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        r = requests.post(url, data={'q': f'site:t.me {kelime}'}, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # Sadece sonuç linklerini (result__url) hedefle, menüleri görmezden gel
        for link in soup.select('.result__url'):
            url_text = link.get_text()
            if 't.me/' in url_text:
                # t.me/s/ seklinde olanlari temizle, kanal adini cikar
                kanal = url_text.split('t.me/')[-1].split('/')[0].split('?')[0]
                if len(kanal) > 3 and 's/' not in kanal:
                    kanallar.add(f"https://t.me/{kanal}")
    except Exception as e:
        st.error(f"Hata: {e}")
    return list(kanallar)

if submit:
    with st.spinner("Taranıyor..."):
        sonuclar = hassas_tara(keyword)
        if sonuclar:
            st.success(f"✅ {len(sonuclar)} kanal bulundu.")
            st.write(sonuclar)
        else:
            st.warning("Sonuç bulunamadı.")
