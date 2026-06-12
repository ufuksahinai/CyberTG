import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
from io import BytesIO
from fpdf import FPDF

# --- ARAYÜZ YAPILANDIRMASI ---
st.set_page_config(page_title="Telegram OSINT", layout="wide")
st.title("🕵️‍♂️ Telegram İstihbarat Aracı")

# --- HAFIZA ---
if 'bulunan_kanallar' not in st.session_state: st.session_state['bulunan_kanallar'] = []
if 'bulunan_mesajlar' not in st.session_state: st.session_state['bulunan_mesajlar'] = []

# --- KANAL TARAMA ---
def kanal_tara(kelime):
    kanallar = set()
    # Maksimum 150 kanal hedefi için yaklaşık 15 sayfa tarama
    for sayfa in range(15):
        if len(kanallar) >= 150: break
        
        url = f"https://html.duckduckgo.com/html/?q=site:t.me {kelime}&s={sayfa*10}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        try:
            r = requests.post(url, data={'q': f'site:t.me {kelime}'}, headers=headers, timeout=10)
            soup = BeautifulSoup(r.text, 'html.parser')
            for link in soup.select('.result__url'):
                url_text = link.get_text()
                if 't.me/' in url_text:
                    k = url_text.split('t.me/')[-1].split('/')[0].split('?')[0]
                    if len(k) > 3 and 's/' not in k: kanallar.add(f"https://t.me/{k}")
            time.sleep(1) # Hız sınırı için
        except: continue
    return list(kanallar)

# --- ARAYÜZ (GELİŞMİŞ TASARIM) ---
with st.form("arama_formu"):
    c1, c2 = st.columns([0.8, 0.2])
    with c1:
        keyword = st.text_input("Tarama yapılacak anahtar kelime:")
    with c2:
        # "+" simgeli buton
        submitted = st.form_submit_button("➕ Tarat")

if submitted and keyword:
    with st.spinner(f"'{keyword}' için 150 kanal hedefleniyor..."):
        sonuclar = kanal_tara(keyword)
        st.session_state['bulunan_kanallar'] = sonuclar
        if not sonuclar: st.warning("Kanal bulunamadı.")
        else: st.success(f"{len(sonuclar)} kanal bulundu!")

# --- MESAJ TARAMA ---
if 'bulunan_kanallar' in st.session_state and st.session_state['bulunan_kanallar']:
    st.write("---")
    st.subheader("Mesaj Analizi")
    m_keyword = st.text_input("Mesajlarda aranacak kelime:")
    if st.button("💬 Mesajları Excel'e Aktar"):
        # Mesaj tarama mantığı...
        st.info("Analiz başlatıldı (Arka planda çalışıyor)...")
