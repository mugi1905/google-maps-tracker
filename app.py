import streamlit as st
import pandas as pd
from datetime import datetime
import time
import json
import os
from playwright.sync_api import sync_playwright
import plotly.express as px

# JSON dosya işlemleri
DATA_FILE = 'maps_data.json'

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for business in data:
                for record in data[business]:
                    record['date'] = datetime.fromisoformat(record['date'])
            return data
    return {}

def save_data(data):
    data_to_save = {}
    for business in data:
        data_to_save[business] = []
        for record in data[business]:
            record_copy = record.copy()
            record_copy['date'] = record['date'].isoformat()
            data_to_save[business].append(record_copy)
    
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data_to_save, f, ensure_ascii=False, indent=2)

def get_place_info(url):
    """Playwright ile Google Maps bilgilerini çeker"""
    try:
        with sync_playwright() as p:
            # Tarayıcıyı başlat
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                locale='tr-TR'
            )
            page = context.new_page()
            
            try:
                # URL'yi düzenle
                url = url.strip()
                if not url.startswith('http'):
                    url = 'https://' + url
                
                # Sayfayı yükle
                page.goto(url)
                page.wait_for_load_state('networkidle')
                time.sleep(5)
                
                # Scroll yaparak tüm içeriğin yüklenmesini sağla
                page.mouse.wheel(0, 200)
                time.sleep(2)
                
                # İşletme adı
                name = page.locator('h1').text_content().strip()
                
                # Puan - birden fazla seçici dene
                rating = 0.0
                selectors = [
                    'span.ceNzKf',
                    'div.fontDisplayLarge',
                    '[aria-label*="yıldız"]',
                    '[aria-label*="stars"]'
                ]
                
                for selector in selectors:
                    try:
                        element = page.locator(selector).first
                        if element:
                            text = element.text_content().strip()
                            # Aria-label için özel kontrol
                            if 'yıldız' in text or 'stars' in text:
                                text = text.split()[0]
                            if text and (',' in text or '.' in text):
                                rating = float(text.replace(',', '.'))
                                break
                    except:
                        continue
                
                # Yorum sayısı - birden fazla seçici dene
                reviews = 0
                review_selectors = [
                    'button.HHrUdb',
                    'span.fontBodyMedium',
                    '[aria-label*="değerlendirme"]',
                    '[aria-label*="reviews"]'
                ]
                
                for selector in review_selectors:
                    try:
                        element = page.locator(selector).first
                        if element:
                            text = element.text_content().strip()
                            if '(' in text:
                                text = text.split('(')[1].split(')')[0]
                            num = int(''.join(filter(str.isdigit, text)))
                            if num > 0:
                                reviews = num
                                break
                    except:
                        continue
                
                # Debug için ekran görüntüsü
                page.screenshot(path="debug.png")
                
                if name:
                    return {
                        'name': name,
                        'rating': rating,
                        'reviews': reviews,
                        'url': url
                    }
                return None
                
            finally:
                browser.close()
                
    except Exception as e:
        st.error(f"Hata: {str(e)}")
        return None

# Fonksiyonları ekleyin (CSS'den önce)
def update_business(business_name):
    """İşletme bilgilerini günceller"""
    # Son kaydedilen URL'yi al
    last_record = st.session_state.businesses[business_name][-1]
    if 'url' in last_record:
        url = last_record['url']
        info = get_place_info(url)
        if info:
            st.session_state.businesses[business_name].append({
                'date': datetime.now(),
                'rating': info['rating'],
                'reviews': info['reviews'],
                'url': url
            })
            save_data(st.session_state.businesses)
            st.success(f"✅ {business_name} bilgileri güncellendi!")
            st.rerun()
        else:
            st.error(f"{business_name} için bilgiler güncellenemedi.")
    else:
        st.error("URL bilgisi bulunamadı. Lütfen işletmeyi tekrar ekleyin.")

def delete_business(business_name):
    """İşletmeyi siler"""
    if business_name in st.session_state.businesses:
        del st.session_state.businesses[business_name]
        save_data(st.session_state.businesses)
        st.success(f"✅ {business_name} silindi!")
        st.rerun()

# Streamlit arayüzü
st.set_page_config(
    page_title="Google Maps İşletme Takip",
    page_icon="🗺️",
    layout="wide"
)

# Minimal CSS güncellemesi
st.markdown("""
<style>
    /* İşletme isimlerini görünür yap */
    .business-title {
        font-size: 1.4rem !important;
        font-weight: 600 !important;
        color: #2d3748 !important;
        padding: 1rem 0 !important;
        display: block !important;
    }
    
    /* Sadece gereksiz div'leri gizle */
    div.stMarkdown div:has(> p:empty) {
        display: none !important;
    }
    
    /* Ana container */
    .block-container {
        padding: 3rem 5rem !important;
    }
    
    /* İşletme kartı */
    .stExpander {
        border: 1px solid #e2e8f0 !important;
        border-radius: 15px !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1) !important;
        background: white !important;
        margin-bottom: 1rem !important;
    }
    
    /* Buton grubu */
    .button-group {
        display: flex !important;
        justify-content: flex-end !important;
        gap: 0.5rem !important;
        padding: 1rem 0 !important;
    }
    
    /* Butonlar */
    button[key*="update"], button[key*="delete"] {
        width: 40px !important;
        height: 40px !important;
        border-radius: 10px !important;
        padding: 0.5rem !important;
        border: none !important;
        transition: all 0.3s ease !important;
    }
    
    /* Güncelle butonu */
    button[key*="update"] {
        background: #4FD1C5 !important;
        color: white !important;
    }
    
    /* Sil butonu */
    button[key*="delete"] {
        background: #FC8181 !important;
        color: white !important;
    }
    
    /* Buton hover efektleri */
    button[key*="update"]:hover, button[key*="delete"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important;
    }
    
    /* Metrik kutuları */
    [data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: 600 !important;
        color: #2d3748 !important;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 1rem !important;
        color: #718096 !important;
        font-weight: 500 !important;
    }
    
    [data-testid="metric-container"] {
        background: #f7fafc !important;
        border-radius: 12px !important;
        padding: 1.5rem !important;
        border: 1px solid #e2e8f0 !important;
    }
    
    /* Alt başlıklar */
    h3 {
        color: #2d3748 !important;
        font-size: 1.5rem !important;
        font-weight: 600 !important;
        margin: 2rem 0 1rem 0 !important;
    }
</style>
""", unsafe_allow_html=True)

# Tarih formatını güncelleyelim
def format_date(date):
    """Tarihi kısa formatta döndürür"""
    return date.strftime('%H:%M')

# Session state başlatma (en üstte olmalı)
if 'businesses' not in st.session_state:
    st.session_state.businesses = load_data()

# Ana başlık
st.markdown("""
    <div class="title-container">
        <h1 style='font-size: 2.5rem; font-weight: 600;'>🗺️ Google Maps İşletme Takip</h1>
        <p style='font-size: 1.1rem; opacity: 0.9; margin-top: 1rem;'>İşletmelerinizin puanlarını ve yorumlarını takip edin</p>
    </div>
""", unsafe_allow_html=True)

# URL giriş ve arama bölümünü güncelleyelim
st.markdown('<div class="search-title">🔍 Yeni İşletme Ekle</div>', unsafe_allow_html=True)

col1, col2 = st.columns([4,1])
with col1:
    maps_url = st.text_input(
        "Google Maps Linki",
        placeholder="https://www.google.com/maps/place/...",
        label_visibility="collapsed"
    )
with col2:
    st.markdown('<div style="height: 8px"></div>', unsafe_allow_html=True)
    if st.button("🔍 Ara", type="primary", use_container_width=True):
        if maps_url:
            if not any(x in maps_url for x in ['maps.google.com', 'google.com/maps', 'maps.app.goo.gl']):
                st.error("Lütfen geçerli bir Google Maps linki girin")
            else:
                with st.spinner('Bilgiler alınıyor...'):
                    info = get_place_info(maps_url)
                    if info:
                        st.success("✅ Bilgiler başarıyla alındı!")
                        
                        # Verileri kaydet
                        if info['name'] not in st.session_state.businesses:
                            st.session_state.businesses[info['name']] = []
                        
                        st.session_state.businesses[info['name']].append({
                            'date': datetime.now(),
                            'rating': info['rating'],
                            'reviews': info['reviews'],
                            'url': maps_url
                        })
                        
                        save_data(st.session_state.businesses)
                        st.rerun()
                    else:
                        st.error("❌ Bilgiler alınamadı!")
        else:
            st.warning("⚠️ Lütfen bir Google Maps linki girin")

# Kayıtlı işletmeler bölümünü güncelleyelim
if st.session_state.businesses:
    st.markdown("---")
    st.subheader("📋 Kayıtlı İşletmeler")
    
    for business, history in st.session_state.businesses.items():
        last_record = history[-1]
        with st.expander("", expanded=True):
            cols = st.columns([4,1])
            with cols[0]:
                st.markdown(f'<div class="business-title">🏪 {business}</div>', unsafe_allow_html=True)
            with cols[1]:
                st.markdown('<div class="button-group">', unsafe_allow_html=True)
                col1, col2 = st.columns([1,1])
                with col1:
                    if st.button("🔄", key=f"update_{business}", help="Güncelle"):
                        update_business(business)
                with col2:
                    if st.button("🗑️", key=f"delete_{business}", help="Sil"):
                        delete_business(business)
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Metrikler
            metric_cols = st.columns([1,1,1])
            with metric_cols[0]:
                st.metric("⭐ Puan", f"{last_record['rating']:.1f}")
            with metric_cols[1]:
                st.metric("💬 Yorum", f"{last_record['reviews']:,}")
            with metric_cols[2]:
                st.metric("🕒 Son Kontrol", format_date(last_record['date']))