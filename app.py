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

def bagimsiz_kanal_ara(kelime, limit):
    kanallar = set()
    # Sayfa sayısını limitinize göre otomatik hesapla (Her sayfada ~10 sonuç var)
    sayfa_sayisi = (limit // 10) + 2
    
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    for sayfa in range(sayfa_sayisi):
        if len(kanallar) >= limit: break # İstenen sayıya ulaştık, dur.
        
        # DuckDuckGo'nun sayfa parametresini (s) kullanarak 2. ve 3. sayfaya geçiyoruz
        start = sayfa * 10
        url = f"https://html.duckduckgo.com/html/?q=site:t.me {kelime}&s={start}"
        
        try:
            r = requests.post(url, data={'q': f'site:t.me {kelime}'}, headers=headers, timeout=10)
            soup = BeautifulSoup(r.text, 'html.parser')
            
            for link in soup.select('.result__url'):
                url_text = link.get_text()
                if 't.me/' in url_text:
                    kanal = url_text.split('t.me/')[-1].split('/')[0].split('?')[0]
                    if len(kanal) > 3 and 's/' not in kanal:
                        kanallar.add(f"https://t.me/{kanal}")
            
            time.sleep(1.5) # Arama motorunu yormamak ve banlanmamak için bekleme
        except: 
            continue
            
    return list(kanallar)[:limit]

if submit:
    with st.spinner("Taranıyor..."):
        sonuclar = hassas_tara(keyword)
        if sonuclar:
            st.success(f"✅ {len(sonuclar)} kanal bulundu.")
            st.write(sonuclar)
        else:
            st.warning("Sonuç bulunamadı.")
