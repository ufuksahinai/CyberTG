import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import time
from io import BytesIO
from fpdf import FPDF

# ARAYÜZ YAPILANDIRMASI
st.set_page_config(page_title="Telegram OSINT", layout="wide")
st.title("🕵️‍♂️ Tam Bağımsız Telegram İstihbarat Aracı")

# --- KANAL TARAMA MANTIĞI ---
def kanal_tara(kelime, limit):
    kanallar = set()
    sorgu = f'site:t.me "{kelime}"'
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    # DuckDuckGo ile Arama
    try:
        url = "https://lite.duckduckgo.com/lite/"
        cevap = requests.post(url, data={'q': sorgu}, headers=headers, timeout=10)
        isimler = re.findall(r't\.me(?:%2F|/)([a-zA-Z0-9_]{5,})', cevap.text)
        for isim in isimler: kanallar.add(f"https://t.me/{isim}")
    except: pass
    
    # Filtrele
    yasakli = ["share", "joinchat", "setlanguage", "socks", "search", "category", "contact", "add", "top", "new", "adult", "video", "music", "books", "gaming", "blogs", "education", "entertainment", "media", "politics", "business", "crypto", "language", "sales", "suggest", "other", "index", "username", "art", "news", "about"]
    return [k for k in kanallar if k.split('/')[-1].lower() not in yasakli][:limit]

# --- MESAJ TARAMA MANTIĞI ---
def mesaj_tara(kanallar, kelime):
    veriler = []
    headers = {'User-Agent': 'Mozilla/5.0'}
    for link in kanallar:
        kanal_adi = link.split('t.me/')[-1].strip('/')
        try:
            cevap = requests.get(f"https://t.me/s/{kanal_adi}", headers=headers, timeout=5)
            if cevap.status_code == 200:
                soup = BeautifulSoup(cevap.text, 'html.parser')
                for m in soup.find_all('div', class_='tgme_widget_message'):
                    t = m.find('div', class_='tgme_widget_message_text')
                    if t and kelime.lower() in t.get_text().lower():
                        veriler.append({"Kanal": kanal_adi, "Mesaj": t.get_text()[:200]})
        except: continue
        time.sleep(1)
    return veriler

# --- ARAYÜZ (FORM İLE HATA ÖNLEME) ---
with st.form("arama_formu"):
    st.subheader("Kanal Arama")
    k_kelime = st.text_input("Anahtar Kelime:")
    k_limit = st.selectbox("Limit:", [20, 50])
    submit = st.form_submit_button("Taramayı Başlat")

if submit and k_kelime:
    with st.spinner("Taranıyor..."):
        sonuclar = kanal_tara(k_kelime, k_limit)
        st.session_state['kanallar'] = sonuclar
        if not sonuclar: st.warning("Kanal bulunamadı.")

if 'kanallar' in st.session_state and st.session_state['kanallar']:
    st.write(f"Bulunan: {len(st.session_state['kanallar'])}")
    st.write(st.session_state['kanallar'])
    
    st.subheader("Mesaj Tarama")
    with st.form("mesaj_formu"):
        m_kelime = st.text_input("Mesajda Aranacak:")
        m_submit = st.form_submit_button("Mesajları Tara")
    
    if m_submit and m_kelime:
        with st.spinner("Mesajlar taranıyor..."):
            mesajlar = mesaj_tara(st.session_state['kanallar'], m_kelime)
            if mesajlar:
                st.dataframe(pd.DataFrame(mesajlar))
            else:
                st.info("Mesaj bulunamadı.")
