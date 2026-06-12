import streamlit as st
import pandas as pd
import asyncio
import time
from telethon import TelegramClient
from duckduckgo_search import DDGS
from io import BytesIO
from fpdf import FPDF

# --- TELEGRAM API BİLGİLERİ ---
API_ID = st.secrets.get("API_ID", "")
API_HASH = st.secrets.get("API_HASH", "")
SESSION_NAME = "osint_session"

# --- ARAYÜZ YAPILANDIRMASI ---
st.set_page_config(page_title="Gelişmiş Telegram İstihbaratı", page_icon="🕵️‍♂️", layout="wide")
st.title("🕵️‍♂️ 2 Aşamalı Telegram OSINT Aracı")
st.markdown("---")

# --- HAFIZA (SESSION STATE) YÖNETİMİ ---
# Streamlit her butona basıldığında sayfayı yeniler. Verilerin kaybolmaması için hafızada tutuyoruz.
if 'bulunan_kanallar' not in st.session_state:
    st.session_state.bulunan_kanallar = []
if 'bulunan_mesajlar' not in st.session_state:
    st.session_state.bulunan_mesajlar = []
if 'tarama_bitti' not in st.session_state:
    st.session_state.tarama_bitti = False

# ==========================================
# 1. AŞAMA: KANAL KEŞFİ
# ==========================================
st.header("1. Aşama: Hedef Kanalların Tespiti")
col1, col2 = st.columns(2)

with col1:
    hedef_kelime = st.text_input("Kanal Bulmak İçin Anahtar Kelime:", placeholder="Örn: yapay zeka, siber güvenlik")
with col2:
    kanal_limiti = st.number_input("Bulunacak Maksimum Kanal Sayısı:", min_value=1, max_value=100, value=20)

if st.button("🔍 Kanal Taramasını Başlat"):
    if hedef_kelime:
        with st.spinner(f"Açık kaynaklarda '{hedef_kelime}' ile ilgili Telegram kanalları aranıyor..."):
            dork_sorgusu = f'site:t.me "{hedef_kelime}"'
            potansiyel_linkler = []
            
            try:
                # DuckDuckGo ile arama işlemi
                with DDGS() as ddgs:
                    # Gelen sonuçları bir listeye çeviriyoruz
                    sonuclar = list(ddgs.text(dork_sorgusu, max_results=kanal_limiti))
                    
                    if not sonuclar:
                        st.error("Arama motoru hiçbir sonuç döndürmedi. Bulut sunucusu (IP) geçici olarak engellenmiş olabilir.")
                    else:
                        for r in sonuclar:
                            link = r.get("href", "")
                            # t.me/ içeren geçerli bağlantıları ayıkla
                            if "t.me/" in link and not link.endswith(".me/"):
                                potansiyel_linkler.append(link)
                
                # Tekrarlayan linkleri temizle ve hafızaya kaydet
                st.session_state.bulunan_kanallar = list(set(potansiyel_linkler))
                st.session_state.bulunan_mesajlar = [] # Yeni aramada eski mesajları temizle
                st.session_state.tarama_bitti = False
                
                # Eğer arama yapıldı ama 0 kanal bulunduysa kullanıcıyı uyar
                if len(st.session_state.bulunan_kanallar) == 0 and len(sonuclar) > 0:
                    st.warning(f"Sonuçlar tarandı ancak '{hedef_kelime}' kelimesi için geçerli bir Telegram davet linki bulunamadı.")
                    
            except Exception as e:
                st.error(f"Arama altyapısında bir hata oluştu: {e}")
    else:
        st.warning("Lütfen arama yapmak için bir anahtar kelime girin.")

# ==========================================
# KANAL LİSTELEME VE 2. AŞAMAYA GEÇİŞ
# ==========================================
# Eğer hafızada bulunmuş kanallar varsa bu bölüm ekranda görünür
if len(st.session_state.bulunan_kanallar) > 0:
    st.success(f"✅ Başarılı! {len(st.session_state.bulunan_kanallar)} adet Telegram kanalı bulundu.")
    with st.expander("Bulunan Kanalların Listesini Gör"):
        st.write(st.session_state.bulunan_kanallar)
    
    st.markdown("---")
    st.header("2. Aşama: Kanal İçi Mesaj Taraması")
    
    col3, col4 = st.columns(2)
    with col3:
        mesaj_kelimesi = st.text_input("Sohbet Geçmişinde Aranacak Kelime:", placeholder="Örn: sızma testi, veritabanı")
    with col4:
        mesaj_limiti = st.number_input("Kanal Başına Taranacak Mesaj Sayısı:", min_value=10, max_value=500, value=50)

    # Telethon Asenkron Tarama Fonksiyonu
    async def mesaj_tara(kanallar, m_kriteri, m_limit):
        veriler = []
        client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
        await client.connect()
        
        ilerleme = st.progress(0)
        for index, link in enumerate(kanallar):
            kanal_adi = link.split('t.me/')[-1].split('/')[0]
            try:
                entity = await client.get_entity(kanal_adi)
                async for message in client.iter_messages(entity, search=m_kriteri, limit=m_limit):
                    if message.text:
                        veriler.append({
                            "Kanal Adı": kanal_adi,
                            "Kanal Linki": link,
                            "Tarih": message.date.strftime("%Y-%m-%d %H:%M"),
                            "Mesaj İçeriği": message.text[:300] + "..." # Uzun mesajları kısaltır
                        })
            except Exception as e:
                pass # Gizli veya erişilemez kanalları atla
            
            time.sleep(1) # Ban riskine karşı bekleme süresi
            ilerleme.progress((index + 1) / len(kanallar))
            
        await client.disconnect()
        return veriler

    if st.button("💬 Sohbet Taramasını Başlat"):
        if mesaj_kelimesi:
            with st.spinner("Bulunan Herkese Açık kanalların içerisine girilerek mesajlar taranıyor..."):
                # Bulunan kanalları asenkron fonksiyona gönder
                sonuclar = asyncio.run(mesaj_tara(st.session_state.bulunan_kanallar, mesaj_kelimesi, mesaj_limiti))
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
        
        # EXCEL ÇIKTISI
        excel_output = BytesIO()
        with pd.ExcelWriter(excel_output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Bulgular')
        excel_data = excel_output.getvalue()
        
        # PDF ÇIKTISI (Basit Şablon)
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="Telegram OSINT Raporu", ln=True, align='C')
        pdf.ln(10)
        
        for index, row in df.iterrows():
            # PDF kütüphanesi Türkçe karakterlerde sorun yaşamasın diye İngilizce karaktere çeviriyoruz
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
        st.warning("Tüm kanallar tarandı ancak belirlediğiniz kriterde bir mesaja rastlanmadı.")
