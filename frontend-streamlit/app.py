import os
import streamlit as nn
import streamlit as st
from dotenv import load_dotenv
from api import StrapiClient

# Load environment variables
load_dotenv()

# Set Streamlit Page Configuration
st.set_page_config(
    page_title="AI Travel Guide | YZ Destekli Gezi Rehberi",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for rich aesthetics and modern card designs
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
    
    /* Global font override */
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    /* Main Title Styling */
    .title-container {
        text-align: center;
        padding: 1.5rem 0;
        margin-bottom: 2rem;
        background: linear-gradient(135deg, rgba(255, 90, 95, 0.1), rgba(63, 81, 181, 0.1));
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .main-title {
        font-size: 2.8rem;
        font-weight: 700;
        background: linear-gradient(45deg, #FF5A5F, #FF7B54, #3F51B5);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
    }
    .subtitle {
        font-size: 1.1rem;
        color: #777;
        margin-top: 0.5rem;
    }
    
    /* City Info Block Styling */
    .city-info-card {
        background: linear-gradient(135deg, #1e293b, #0f172a);
        color: #f8fafc;
        border-radius: 16px;
        padding: 1.8rem;
        margin-bottom: 2.5rem;
        border: 1px solid rgba(255, 255, 255, 0.08);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
    }
    .city-name {
        font-size: 2.2rem;
        font-weight: 700;
        color: #38bdf8;
        margin-bottom: 0.2rem;
    }
    .city-country {
        font-size: 1rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 2px;
        color: #94a3b8;
        margin-bottom: 0.8rem;
    }
    .city-description {
        font-size: 1.1rem;
        line-height: 1.6;
        color: #cbd5e1;
    }
    
    /* Place Card CSS (applied around native streamlit elements using containers) */
    .place-header {
        font-size: 1.6rem;
        font-weight: 600;
        color: #1e293b;
        margin-top: 1rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .rating-badge {
        background-color: #fef08a;
        color: #854d0e;
        padding: 4px 10px;
        border-radius: 30px;
        font-size: 0.95rem;
        font-weight: bold;
        display: inline-flex;
        align-items: center;
        gap: 4px;
        border: 1px solid #fde047;
    }
    
    /* Custom Info Boxes for TR/EN */
    .desc-box-tr {
        background-color: rgba(255, 90, 95, 0.04);
        border-left: 4px solid #FF5A5F;
        padding: 1rem;
        border-radius: 0 8px 8px 0;
        margin-top: 0.5rem;
        margin-bottom: 0.5rem;
    }
    
    .desc-box-en {
        background-color: rgba(63, 81, 181, 0.04);
        border-left: 4px solid #3F51B5;
        padding: 1rem;
        border-radius: 0 8px 8px 0;
        margin-top: 0.5rem;
        margin-bottom: 0.5rem;
    }
    
    .lang-label {
        font-weight: bold;
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: #64748b;
        margin-bottom: 0.3rem;
    }
    
    /* Footer Styling */
    .footer {
        text-align: center;
        margin-top: 5rem;
        padding: 1.5rem;
        color: #64748b;
        font-size: 0.9rem;
        border-top: 1px solid rgba(0, 0, 0, 0.05);
    }
</style>
""", unsafe_allow_html=True)

# Main Title Header
st.markdown("""
<div class="title-container">
    <h1 class="main-title">YZ Destekli Gezi Rehberi</h1>
    <div class="subtitle">AI-Powered Multilingual Travel Guide & Place Explorer</div>
</div>
""", unsafe_allow_html=True)

# Initialize Strapi Client
client = StrapiClient()

# Check Environment Variables
if not os.getenv("STRAPI_URL"):
    st.warning("⚠️ **Lütfen Dikkat:** Strapi API bağlantı parametreleri yapılandırılmamış.")
    st.info("Projeyi tam çalıştırmak için `frontend-streamlit/.env` dosyasını oluşturun ve `STRAPI_URL` değerini girin.")
    st.stop()

# Sidebar for City Selection & Settings
st.sidebar.image("https://images.unsplash.com/photo-1488646953014-85cb44e25828?auto=format&fit=crop&q=80&w=300", use_container_width=True)
st.sidebar.title("🗺️ Keşfetmeye Başla")
st.sidebar.write("Gezmek istediğiniz şehri seçin ve yapay zeka ile oluşturulan görseller ile mekanları inceleyin.")

# Fetch all cities
cities = client.fetch_cities()

if not cities:
    st.sidebar.info("Veritabanı boş görünüyor.")
    st.markdown("""
    ### Veri Bulunamadı 🏜️
    Strapi CMS veritabanında henüz kayıtlı bir şehir veya mekan bulunmuyor.
    
    **Sistemi başlatmak için şu adımları izleyin:**
    1. Strapi CMS projenizi ayağa kaldırın (`npm run dev`).
    2. Gerekli İçerik Tiplerini (Cities, Places) oluşturun ve API Token yetkilerini atayın.
    3. `automation` dizinindeki `.env` dosyasını yapılandırın.
    4. Otomasyon scriptini çalıştırın:
       ```bash
       python main.py
       ```
    5. Sayfayı yenileyin.
    """)
else:
    # Prepare selectbox options
    city_names = [city["name"] for city in cities]
    selected_city_name = st.sidebar.selectbox("Şehir Seçin:", city_names)
    
    # Get selected city dictionary
    selected_city = next(city for city in cities if city["name"] == selected_city_name)
    
    # Display City Banner Info Card
    st.markdown(f"""
    <div class="city-info-card">
        <div class="city-name">{selected_city['name']}</div>
        <div class="city-country">📍 {selected_city['country']}</div>
        <div class="city-description">{selected_city['short_info']}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Fetch places for selected city
    places = client.fetch_places(selected_city["id"])
    
    if not places:
        st.info(f"'{selected_city_name}' şehri için henüz eklenmiş gezi mekanı bulunmamaktadır.")
    else:
        st.markdown(f"### 📌 Gezilecek Popüler Mekanlar ({len(places)})")
        
        # Display places in grid layout (2 columns for cards)
        cols = st.columns(2)
        
        for index, place in enumerate(places):
            col = cols[index % 2]
            
            with col:
                # Wrap each place card inside a clean card visual boundary
                with st.container(border=True):
                    # 1. Place Image with fallback placeholder
                    image_url = place.get("image_url")
                    if image_url:
                        st.image(image_url, use_container_width=True, caption=place["name"])
                    else:
                        st.image("https://images.unsplash.com/photo-1469854523086-cc02fe5d8800?auto=format&fit=crop&q=80&w=800", use_container_width=True, caption="Resim Yok")
                    
                    # 2. Place Title & Rating Row using HTML
                    rating_val = place.get("rating", 5.0)
                    st.markdown(f"""
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 10px; margin-bottom: 15px;">
                        <span style="font-size: 1.5rem; font-weight: 600; color: #0f172a;">{place['name']}</span>
                        <span class="rating-badge">⭐ {rating_val:.1f} / 5.0</span>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # 3. Multilingual Description Tabs
                    tab_tr, tab_en = st.tabs(["🇹🇷 Türkçe Açıklama", "🇬🇧 English Description"])
                    
                    with tab_tr:
                        st.markdown(f"""
                        <div class="desc-box-tr">
                            <div class="lang-label">Türkçe Tanıtım</div>
                            <p style="margin: 0; color: #334155; line-height: 1.5;">{place.get('description_tr', '')}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                    with tab_en:
                        st.markdown(f"""
                        <div class="desc-box-en">
                            <div class="lang-label">English Translation</div>
                            <p style="margin: 0; color: #334155; line-height: 1.5;">{place.get('description_en', '')}</p>
                        </div>
                        """, unsafe_allow_html=True)
                
                # Add spacing between row card items
                st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

# Footer info
st.markdown("""
<div class="footer">
    <p>YZ Destekli Gezi Rehberi Final Projesi • Python, Streamlit & Strapi CMS ile geliştirilmiştir.</p>
</div>
""", unsafe_allow_html=True)
