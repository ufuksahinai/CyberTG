import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import re
from io import BytesIO
from fpdf import FPDF

# --- ARAYÜZ YAPILANDIRMASI ---
st.set_page_config(page_title="Siber Telegram OSINT", page_icon="🕵️‍♂️", layout="wide")
st.title("🕵️‍♂️ Siber Telegram Tarama Aracı")
st.write("UYARI: Yalnızca açık kaynakları tarar ve Telegram güncellemelerine bağlı olarak eksik veri sağlayabilir!")
st.markdown("---")

# --- HAFIZA (SESSION STATE) ---
if 'bulunan_kanallar' not in st.session_state:
    st.session_state.bulunan_kanallar = []
if 'bulunan_mesajlar' not in st.session_state:
    st.session_state.bulunan_mesajlar = []
if 'tarama_bitti' not in st.session_state:
    st.session_state.tarama_bitti = False

# ==========================================
# 1. AŞAMA: ALTERNATİF MOTORLAR İLE KANAL KEŞFİ
# ==========================================
st.header("1. Aşama: Hedef Kanalların Tespiti")
col1, col2 = st.columns(2)

with col1:
    hedef_kelime = st.text_input("Kanal Bulmak İçin Anahtar Kelime:", placeholder="Örn: yapay zeka")
with col2:
    kanal_limiti = st.selectbox("Bulunacak Maksimum Kanal Sayısı (Tahmini):", [20, 50, 100])

import urllib.parse

import urllib.parse
from bs4 import BeautifulSoup
import requests
import re
import time

def bagimsiz_kanal_ara(kelime, limit):
    kanallar = set()
    kelime_url = urllib.parse.quote(kelime)
    sorgu = urllib.parse.quote(f'site:t.me "{kelime}"')
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/json,application/xhtml+xml'
    }

    # ==========================================
    # YÖNTEM 1: DİZİNLER (Sadece Gerçek Kanalları Okur, Menüleri Atlar)
    # ==========================================
    try:
        # tlgrm.eu sitesindeki kanallar /channel/ ile başlar (Kategoriler ise /channels/ ile başlar)
        url = f"https://tlgrm.eu/channels?search={kelime_url}"
        cevap = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(cevap.text, 'html.parser')
        
        for a in soup.find_all('a', href=True):
            href = a['href']
            # Sadece gerçek kanal linklerini alıyoruz
            if href.startswith('/channel/') and not href.startswith('/channel/category'):
                kanal_adi = href.split('/')[-1]
                kanallar.add(f"https://t.me/{kanal_adi}")
    except:
        pass

    try:
        url = f"https://telegramchannels.me/search?q={kelime_url}"
        cevap = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(cevap.text, 'html.parser')
        
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href.startswith('https://telegramchannels.me/channels/') or href.startswith('/channels/'):
                isim = href.split('/')[-1]
                # Sitenin menü tuşlarını engelliyoruz
                if isim not in ['category', 'search', 'add', 'contact', 'top', 'new']:
                    kanallar.add(f"https://t.me/{isim}")
    except:
        pass

    # ==========================================
    # YÖNTEM 2: SEARXNG JSON API (HTML Parsing Gerektirmez, Doğrudan Link Verir)
    # ==========================================
    searx_motorlari = [
        f"https://searx.be/search?q={sorgu}&format=json",
        f"https://paulgo.io/search?q={sorgu}&format=json",
        f"https://search.mdosch.de/search?q={sorgu}&format=json"
    ]

    for url in searx_motorlari:
        if len(kanallar) >= limit: break
        try:
            cevap = requests.get(url, headers=headers, timeout=10)
            if cevap.status_code == 200:
                veriler = cevap.json() # Sitenin kaynak kodu yerine doğrudan JSON verisi çeker
                for sonuc in veriler.get('results', []):
                    link = sonuc.get('url', '')
                    if "t.me/" in link and not link.endswith(".me/"):
                        kanallar.add(link)
        except:
            pass

    # ==========================================
    # YÖNTEM 3: DUCKDUCKGO HTML (Yedek Ağ)
    # ==========================================
    if len(kanallar) < limit // 2:
        try:
            url = f"https://html.duckduckgo.com/html/?q={sorgu}"
            cevap = requests.get(url, headers=headers, timeout=10)
            isimler = re.findall(r't\.me(?:%2F|/)([a-zA-Z0-9_]{5,})', cevap.text)
            for isim in isimler:
                kanallar.add(f"https://t.me/{isim}")
        except: 
            pass

    # ==========================================
    # KESİN TEMİZLİK VE FİLTRELEME
    # ==========================================
    temiz_kanallar = list()
    
    # Karşınıza çıkan o can sıkıcı menü kelimelerini sonsuza dek kara listeye aldık
    yasakli_kelimeler = [
        "share", "joinchat", "setlanguage", "socks", "search", "proxy", "category",
        "adult", "video", "music", "books", "gaming", "blogs", "education", 
        "entertainment", "media", "politics", "business", "crypto", "language", 
        "sales", "suggest", "other", "index", "username", "contact", "art", "news"
    ]

    for kanal in kanallar:
        isim = kanal.split('/')[-1].lower()
        
        # 1. Kural: Kanal adı en az 5 harf olmalı (t.me/abc geçersizdir)
        # 2. Kural: Yasaklı listedeki menü isimlerinden biri olmamalı
        if len(isim) >= 5 and isim not in yasakli_kelimeler:
            # 3. Kural: Hatalı davet linkleri ve teknik komutlar olmamalı
            if not any(yasakli in kanal.lower() for yasakli in ["joinchat", "setlanguage", "share", "socks", "+"]):
                temiz_kanallar.append(kanal)

    return temiz_kanallar[:limit]
if st.button("🔍 Kanal Taramasını Başlat"):
    if hedef_kelime:
        with st.spinner(f"Açık kaynaklarda '{hedef_kelime}' için gizlice Telegram kanalları aranıyor..."):
            sonuclar = bagimsiz_kanal_ara(hedef_kelime, kanal_limiti)
            st.session_state.bulunan_kanallar = sonuclar
            st.session_state.bulunan_mesajlar = [] 
            st.session_state.tarama_bitti = False
            
            if len(sonuclar) == 0:
                st.warning("Eşleşen geçerli bir genel (public) kanal bulunamadı veya arama motoru anlık yanıt vermedi.")
    else:
        st.warning("Lütfen arama yapmak için bir anahtar kelime girin.")

# ==========================================
# KANAL LİSTELEME VE 2. AŞAMAYA GEÇİŞ
# ==========================================
if len(st.session_state.bulunan_kanallar) > 0:
    st.success(f"✅ Başarılı! {len(st.session_state.bulunan_kanallar)} adet benzersiz Telegram kanalı tespit edildi.")
    with st.expander("Bulunan Kanalların Listesini Gör"):
        st.write(st.session_state.bulunan_kanallar)
    
    st.markdown("---")
    st.header("2. Aşama: Kanal İçi Mesaj Taraması (Kimliksiz)")
    
    mesaj_kelimesi = st.text_input("Sohbet Geçmişinde Aranacak Kelime:", placeholder="Örn: siber saldırı")

    def web_view_mesaj_tara(kanallar, aranacak_kelime):
        veriler = []
        aranacak_kelime_kucuk = aranacak_kelime.lower()
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        
        ilerleme = st.progress(0)
        for index, link in enumerate(kanallar):
            # Normal t.me/ linkini, okunabilir Web View (t.me/s/) linkine çevir
            kanal_adi = link.split('t.me/')[-1].strip('/')
            web_url = f"https://t.me/s/{kanal_adi}"
            
            try:
                cevap = requests.get(web_url, headers=headers, timeout=10)
                if cevap.status_code == 200:
                    soup = BeautifulSoup(cevap.text, 'html.parser')
                    
                    # Sayfadaki tüm mesaj bloklarını bul
                    mesaj_bloklari = soup.find_all('div', class_='tgme_widget_message')
                    
                    for blok in mesaj_bloklari:
                        metin_div = blok.find('div', class_='tgme_widget_message_text')
                        if metin_div:
                            metin = metin_div.get_text(separator=' ', strip=True)
                            
                            # Mesajın içinde aradığımız kelime var mı?
                            if aranacak_kelime_kucuk in metin.lower():
                                tarih_tag = blok.find('time')
                                tarih = tarih_tag['datetime'][:16].replace('T', ' ') if tarih_tag else "Bilinmeyen Tarih"
                                
                                veriler.append({
                                    "Kanal Adı": kanal_adi,
                                    "Kanal Linki": link,
                                    "Tarih": tarih,
                                    "Mesaj İçeriği": metin[:300] + "..." # Uzun metni kırp
                                })
            except Exception as e:
                pass # Ulaşılamayan kanalları atla
                
            time.sleep(1) # IP banı yememek için bekle
            ilerleme.progress((index + 1) / len(kanallar))
            
        return veriler

    if st.button("💬 Sohbet Taramasını Başlat"):
        if mesaj_kelimesi:
            with st.spinner("Telegram Web Görünümü (Web View) üzerinden mesajlar kimliksiz olarak okunuyor..."):
                sonuclar = web_view_mesaj_tara(st.session_state.bulunan_kanallar, mesaj_kelimesi)
                st.session_state.bulunan_mesajlar = sonuclar
                st.session_state.tarama_bitti = True
        else:
            st.warning("Lütfen aranacak mesaj kelimesini girin.")

# ==========================================
# 3. AŞAMA: SONUÇ RAPORLAMA VE İNDİRME
# ==========================================
if st.session_state.tarama_bitti:
    st.markdown("---")
    st.header("📊 Tarama Sonuçları")
    
    if len(st.session_state.bulunan_mesajlar) > 0:
        df = pd.DataFrame(st.session_state.bulunan_mesajlar)
        st.dataframe(df, use_container_width=True)
        
        # Excel
        excel_output = BytesIO()
        with pd.ExcelWriter(excel_output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Bulgular')
        excel_data = excel_output.getvalue()
        
        # PDF
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

        st.success("Tarama tamamlandı! Kimliğiniz tamamen gizli tutularak elde edilen bulgular aşağıdadır.")
        col_ex, col_pdf = st.columns(2)
        with col_ex:
            st.download_button(label="📥 Excel Olarak İndir", data=excel_data, file_name="anonim_osint_raporu.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        with col_pdf:
            st.download_button(label="📄 PDF Olarak İndir", data=pdf_data, file_name="anonim_osint_raporu.pdf", mime="application/pdf")
    else:
        st.warning(f"Taranan kanalların son güncel mesajları arasında '{mesaj_kelimesi}' kelimesine rastlanmadı.")
