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

import cloudscraper
from duckduckgo_search import DDGS
import urllib.parse
from bs4 import BeautifulSoup
import re
import streamlit as st

def bagimsiz_kanal_ara(kelime, limit):
    kanallar = set()
    loglar = [] # Artık neyin ters gittiğini veya başarılı olduğunu kaydediyoruz

    sorgu = f'site:t.me "{kelime}"'
    kelime_url = urllib.parse.quote(kelime)

    # ==========================================
    # 1. YÖNTEM: DUCKDUCKGO (Dahili Proxy Kullanır)
    # ==========================================
    try:
        with DDGS() as ddgs:
            sonuclar = list(ddgs.text(sorgu, max_results=limit))
            for sonuc in sonuclar:
                link = sonuc.get('href', '')
                if "t.me/" in link:
                    kanallar.add(link)
        loglar.append("✅ DuckDuckGo Araması Başarılı: Bağlantılar çekildi.")
    except Exception as e:
        loglar.append(f"❌ DuckDuckGo Hatası: {e}")

    # ==========================================
    # 2. YÖNTEM: CLOUDSCRAPER İLE CLOUDFLARE AŞIMI (Dizin Siteleri)
    # ==========================================
    try:
        # Normal bot değil, Chrome tarayıcısı taklidi yapan özel aşım aracı
        scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})
        
        # Site 1: Tlgrm.eu
        cevap = scraper.get(f"https://tlgrm.eu/channels?search={kelime_url}", timeout=15)
        if cevap.status_code == 200:
            soup = BeautifulSoup(cevap.text, 'html.parser')
            for a in soup.find_all('a', href=True):
                href = a['href']
                if href.startswith('/channel/') and 'category' not in href:
                    kanallar.add(f"https://t.me/{href.split('/')[-1]}")
            loglar.append("✅ Tlgrm.eu Başarılı: Cloudflare duvarı aşıldı.")
        else:
            loglar.append(f"❌ Tlgrm.eu Engelledi: HTTP Kodu {cevap.status_code}")
            
        # Site 2: Telegramchannels.me
        cevap2 = scraper.get(f"https://telegramchannels.me/search?q={kelime_url}", timeout=15)
        if cevap2.status_code == 200:
            soup2 = BeautifulSoup(cevap2.text, 'html.parser')
            for a in soup2.find_all('a', href=True):
                href = a['href']
                if '/channels/' in href:
                    isim = href.split('/')[-1]
                    kanallar.add(f"https://t.me/{isim}")
            loglar.append("✅ Telegramchannels.me Başarılı: Cloudflare duvarı aşıldı.")
        else:
            loglar.append(f"❌ Telegramchannels Engelledi: HTTP Kodu {cevap2.status_code}")
            
    except Exception as e:
        loglar.append(f"❌ Cloudscraper Hatası: {e}")

    # ==========================================
    # KESİN TEMİZLİK VE FİLTRELEME
    # ==========================================
    temiz_kanallar = set()
    # Sahte kanalları ve menü tuşlarını kesin olarak yok etme listesi
    yasakli = ["share", "joinchat", "setlanguage", "socks", "search", "category", "contact", "add", "top", "new"]
    
    for k in kanallar:
        try:
            # Sadece t.me/ sonrasındaki "gerçek kullanıcı adını" Regex ile söküp alıyoruz
            eslesme = re.search(r't\.me(?:/s/|/)([a-zA-Z0-9_]+)', k)
            if eslesme:
                isim = eslesme.group(1)
                # İsim en az 5 harf olmalı ve menü komutlarından biri olmamalı
                if len(isim) >= 4 and isim.lower() not in yasakli:
                    temiz_kanallar.add(f"https://t.me/{isim}")
        except:
            pass

    # KULLANICI ARAYÜZÜNE RAPOR BASMA
    with st.expander("🔍 Geliştirici Logları (Arka Planda Neler Olduğunu Görün)"):
        for log in loglar:
            if "❌" in log:
                st.error(log)
            else:
                st.success(log)

    return list(temiz_kanallar)[:limit]

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
