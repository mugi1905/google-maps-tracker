import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import json

# Veri saklama için basit bir JSON dosyası kullanacağız
def load_data():
    try:
        with open('business_ratings.json', 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def save_data(data):
    with open('business_ratings.json', 'w') as file:
        json.dumps(data, file)

# Streamlit arayüzü
def main():
    st.set_page_config(page_title="İşletme Puanları Takip Sistemi", layout="wide")
    
    # Başlık ve açıklama
    st.title("📊 İşletme Puanları Takip Sistemi")
    st.markdown("---")
    
    # Sidebar - İşletme Ekleme
    with st.sidebar:
        st.header("🏢 İşletme Yönetimi")
        new_business = st.text_input("İşletme Adı")
        new_rating = st.slider("Puan", 0.0, 5.0, 4.0, 0.1)
        if st.button("İşletme Ekle"):
            data = load_data()
            if new_business:
                if new_business not in data:
                    data[new_business] = {
                        'ratings': [],
                        'dates': []
                    }
                data[new_business]['ratings'].append(new_rating)
                data[new_business]['dates'].append(datetime.now().strftime("%Y-%m-%d"))
                save_data(data)
                st.success(f"{new_business} başarıyla eklendi!")

    # Ana panel
    data = load_data()
    
    if not data:
        st.info("Henüz işletme eklenmemiş. Soldaki panelden işletme ekleyebilirsiniz.")
        return

    # İşletmelerin son puanlarını gösteren metrik kartları
    col1, col2, col3 = st.columns(3)
    for idx, (business, info) in enumerate(data.items()):
        with [col1, col2, col3][idx % 3]:
            current_rating = info['ratings'][-1]
            st.metric(
                label=f"🏪 {business}",
                value=f"{current_rating:.1f} ⭐",
                delta=f"{current_rating - info['ratings'][0]:.1f}" if len(info['ratings']) > 1 else None
            )

    # Grafik
    st.markdown("### 📈 Puan Değişim Grafiği")
    
    df_list = []
    for business, info in data.items():
        temp_df = pd.DataFrame({
            'İşletme': [business] * len(info['ratings']),
            'Tarih': pd.to_datetime(info['dates']),
            'Puan': info['ratings']
        })
        df_list.append(temp_df)
    
    if df_list:
        df = pd.concat(df_list)
        fig = px.line(df, x='Tarih', y='Puan', color='İşletme',
                     title='İşletme Puanları Zaman Grafiği')
        st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main() 