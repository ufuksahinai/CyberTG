import streamlit as st
import pandas as pd
import asyncio
import time
from telethon import TelegramClient
from duckduckgo_search import DDGS

# --- TELEGRAM API BİLGİLERİ ---
# Güvenlik için bu bilgileri Streamlit Secrets üzerinden çekeceğiz
API_ID = st.secrets["API_ID"]
API_HASH = st.secrets["API_HASH"]
SESSION_NAME = "bulut_oturum"

# --- ARAYÜZ YAPILANDIRMASI ---
st.set_page_config(page_title="OSINT Telegram Tarayıcı", page_icon="🔍")
st.title("🔍 Siber Telegram Sorgu Aracı")
st.write("Belirlediğiniz anahtar kelimelere göre açık kaynaklardan Telegram gruplarını bulur ve içeriklerini tarar.")
st.markdown("---")

# --- KULLANICI GİRDİLERİ ---
hedef_kelime = st.text_input("Kanal Bulmak İçin Anahtar Kelime:", placeholder="Örn: yapay zeka")
mesaj_kelimesi = st.text_input("Sohbet Geçmişinde Aranacak Kelime:", placeholder="Örn: makine öğrenmesi")
kanal_limiti = st.slider("Bulunacak Maksimum Kanal Sayısı:", min_value=1, max_value=20, value=5)
mesaj_limiti = st.slider("Kanal Başına Taranacak Eski Mesaj Sayısı:", min_value=10, max_value=500, value=150)

# --- ASENKRON TARAMA FONKSİYONU ---
async def tarama_islemi(hedef, mesaj_kriteri, k_limit, m_limit):
    bulunan_veriler = []
    
    # 1. Aşama: Google Dork ile Kanal Bulma
    st.info(f"1. ADIM: Google üzerinde '{hedef}' ile ilgili Telegram grupları aranıyor...")
    dork_sorgusu = f'site:t.me "{hedef}"' # Özel sorgu oluşturulur
    potansiyel_linkler = []
    
    #İPTAL googlesearch-python kütüphanesi aramalar arasına bekleme süresi koyarak IP banı yemenizi engeller.
    potansiyel_linkler = []
    
    # DuckDuckGo kütüphanesi bulut sunucularında CAPTCHA engeline takılmaz
    with DDGS() as ddgs:
        sonuclar = ddgs.text(dork_sorgusu, max_results=k_limit)
        for r in sonuclar:
            link = r.get("href", "")
            if "t.me/" in link and not link.endswith(".me/"):
                potansiyel_linkler.append(link)
    
    # 2. Aşama: Telethon ile Mesaj Tarama
    st.info("2. ADIM: Bulunan kanalların içerisine girilerek mesajlar taranıyor...")
    
    # Telegram istemcisini başlatıyoruz
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    await client.connect()
    
    ilerleme_cubugu = st.progress(0)
    for index, link in enumerate(potansiyel_linkler):
        kanal_adi = link.split('t.me/')[-1].split('/')[0]
        try:
            # Sadece herkese açık (Public) grupları ve kanalları hedefler.
            entity = await client.get_entity(kanal_adi)
            
            # Belirli anahtar kelimelerin yer aldığı mesajların listelenmesini sağlar.
            async for message in client.iter_messages(entity, search=mesaj_kriteri, limit=m_limit):
                if message.text:
                    bulunan_veriler.append({
                        "Kanal Adı": kanal_adi,
                        "Kanal Linki": link,
                        "Mesaj ID": message.id,
                        "Tarih": message.date.strftime("%Y-%m-%d %H:%M"),
                        "Mesaj İçeriği": message.text[:200] + "..." # İlk 200 karakter
                    })
        except Exception as e:
            pass # Gizli kanal veya erişim izni yoksa atla
            
        # İşlemler arasına rastgele gecikmeler (time.sleep) eklenmesi sistemin sağlığı için kritik bir adımdır.
        time.sleep(2) 
        ilerleme_cubugu.progress((index + 1) / len(potansiyel_linkler))
        
    await client.disconnect()
    return bulunan_veriler

# --- ÇALIŞTIRMA BUTONU ---
if st.button("🚀 Taramayı Başlat"):
    if hedef_kelime and mesaj_kelimesi:
        # Asenkron fonksiyonu Streamlit içinde güvenle çalıştırmak için
        sonuclar = asyncio.run(tarama_islemi(hedef_kelime, mesaj_kelimesi, kanal_limiti, mesaj_limiti))
        
        if sonuclar:
            st.success("Tarama Başarıyla Tamamlandı! 🎉")
            # Toplanan tüm sonuçlar, Pandas kütüphanesi yardımıyla hızlıca düzenli bir tabloya dönüştürülür.
            df = pd.DataFrame(sonuclar)
            st.dataframe(df)
            
            # Excel Çıktısı Hazırlama
            from io import BytesIO
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Bulgular')
            
            # Excel tablosu hazırlayacak ve indirmeye sunacak
            st.download_button(
                label="📥 Sonuçları Excel Olarak İndir",
                data=output.getvalue(),
                file_name=f"osint_raporu_{hedef_kelime}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.warning("Kanallar tarandı ancak belirtilen anahtar kelimeyi içeren bir mesaj bulunamadı.")
    else:
        st.error("Lütfen taramayı başlatmadan önce arama kelimelerini eksiksiz girin.")
