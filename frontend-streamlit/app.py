import os
import html
import streamlit as st
from dotenv import load_dotenv
from api import StrapiClient

# Load environment variables
load_dotenv()


def safe_text(value) -> str:
    return html.escape(str(value or ""))

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
    
    /* Read More Details Styling */
    .read-more-panel {
        margin-top: 0.75rem;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        background: #ffffff;
        overflow: hidden;
    }
    .read-more-panel > summary {
        list-style: none;
    }
    .read-more-summary {
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0.75rem;
        padding: 0.8rem 0.95rem;
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.04), rgba(56, 189, 248, 0.08));
        color: #0f172a;
        font-weight: 700;
        font-size: 0.95rem;
    }
    .read-more-panel > summary::-webkit-details-marker {
        display: none;
    }
    .read-more-panel[open] .read-more-summary {
        border-bottom: 1px solid #e2e8f0;
    }
    .read-more-icon {
        width: 28px;
        height: 28px;
        border-radius: 50%;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        background: #0f172a;
        color: #ffffff;
        font-weight: 700;
        flex: 0 0 auto;
    }
    .read-more-body {
        padding: 1rem;
        color: #334155;
        line-height: 1.65;
        font-size: 0.98rem;
    }
    .read-more-body p {
        margin: 0;
    }
    .detail-label {
        color: #64748b;
        font-size: 0.78rem;
        font-weight: 700;
        text-transform: uppercase;
        margin-bottom: 0.45rem;
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

# Sidebar for Language Selection & Settings
st.sidebar.title("🌐 Dil / Language")
lang_option = st.sidebar.selectbox(
    "Uygulama Dili / App Language:",
    ["TR (Türkçe)", "EN (English)"]
)
is_en = (lang_option == "EN (English)")

# Translate Header Strings
main_title = "AI-Powered Travel Guide" if is_en else "YZ Destekli Gezi Rehberi"
subtitle = "AI-Powered Multilingual Travel Guide & Place Explorer" if is_en else "Yapay Zeka Destekli Çok Dilli Gezi Rehberi & Mekan Kaşifi"

# Main Title Header
st.markdown(f"""
<div class="title-container">
    <h1 class="main-title">{main_title}</h1>
    <div class="subtitle">{subtitle}</div>
</div>
""", unsafe_allow_html=True)

# Initialize Strapi Client
client = StrapiClient()

# Check Environment Variables
if not os.getenv("STRAPI_URL") and not os.getenv("STRAPI_INTERNAL_HOSTPORT"):
    if is_en:
        st.info("Strapi URL is not configured. Trying the local default: `http://localhost:1337`.")
    else:
        st.info("Strapi URL yapılandırılmamış. Yerel varsayılan deneniyor: `http://localhost:1337`.")

# Sidebar for City Selection
sidebar_title = "🗺️ Start Exploring" if is_en else "🗺️ Keşfetmeye Başla"
sidebar_desc = "Select a city and explore places with AI-generated visuals and bilingual descriptions." if is_en else "Şehri seçin; Strapi'den gelen mekanları YZ görselleri ve çift dilli tanıtımlarıyla inceleyin."
st.sidebar.title(sidebar_title)
st.sidebar.write(sidebar_desc)

# Fetch all cities with loading indicator
with st.spinner("Veriler yükleniyor..." if not is_en else "Loading data..."):
    cities = client.fetch_cities()

# Handle connection error (None) vs empty data ([])
if cities is None:
    if is_en:
        st.error("⚠️ **Connection Error:** Cannot connect to Strapi API server.")
        st.info("Please make sure your Strapi CMS project is running at the configured URL.")
    else:
        st.error("⚠️ **Bağlantı Hatası:** Strapi API sunucusuna bağlanılamıyor.")
        st.info("Lütfen Strapi CMS projenizin yapılandırılmış URL'de çalıştığından emin olun.")
    st.stop()

if not cities:
    if is_en:
        st.sidebar.info("Database appears to be empty.")
        st.markdown("""
        ### No Data Found 🏜️
        There is no city or place registered in the Strapi CMS database yet.
        
        **Follow these steps to start the system:**
        1. Start your Strapi CMS project (`npm run dev`).
        2. Create the required Content Types (Cities, Places) and assign API Token permissions.
        3. Configure the `.env` file in the `automation/` directory.
        4. Run the automation script:
           ```bash
           python main.py
           ```
        5. Refresh the page.
        """)
    else:
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
    # Initialize session state for selected city ID to prevent resetting on language switch
    if "selected_city_id" not in st.session_state and cities:
        st.session_state.selected_city_id = cities[0]["id"]
        
    selected_index = 0
    if "selected_city_id" in st.session_state:
        for idx, city in enumerate(cities):
            if city["id"] == st.session_state.selected_city_id:
                selected_index = idx
                break

    # Prepare selectbox options
    if is_en:
        city_names = [city.get("name_en") or city.get("name") for city in cities]
        selected_city_name = st.sidebar.selectbox("Select City:", city_names, index=selected_index)
        selected_city = next(city for city in cities if (city.get("name_en") or city.get("name")) == selected_city_name)
    else:
        city_names = [city["name"] for city in cities]
        selected_city_name = st.sidebar.selectbox("Şehir Seçin:", city_names, index=selected_index)
        selected_city = next(city for city in cities if city["name"] == selected_city_name)
        
    # Update persisted ID in session state
    st.session_state.selected_city_id = selected_city["id"]
    
    # Display City Banner Info Card
    city_disp_name = safe_text(selected_city.get('name_en') if is_en else selected_city.get('name'))
    city_disp_country = safe_text(selected_city.get('country_en') if is_en else selected_city.get('country'))
    city_disp_info = safe_text(selected_city.get('short_info_en') if is_en else selected_city.get('short_info'))
    
    st.markdown(f"""
    <div class="city-info-card">
        <div class="city-name">{city_disp_name}</div>
        <div class="city-country">📍 {city_disp_country}</div>
        <div class="city-description">{city_disp_info}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Fetch places for selected city
    places = client.fetch_places(selected_city["id"])
    
    if not places:
        no_places_msg = f"No tourist places added yet for '{selected_city_name}'." if is_en else f"'{selected_city_name}' şehri için henüz eklenmiş gezi mekanı bulunmamaktadır."
        st.info(no_places_msg)
    else:
        places_section_title = f"### 📌 Popular Places to Visit ({len(places)})" if is_en else f"### 📌 Gezilecek Popüler Mekanlar ({len(places)})"
        st.markdown(places_section_title)
        
        # Display places in grid layout (2 columns for cards)
        cols = st.columns(2)
        
        for index, place in enumerate(places):
            col = cols[index % 2]
            
            with col:
                # Wrap each place card inside a clean card visual boundary
                with st.container(border=True):
                    # 1. Place Image with fallback placeholder
                    image_url = place.get("image_url")
                    place_disp_name_raw = place.get("name_en") if is_en else place.get("name")
                    place_disp_name = safe_text(place_disp_name_raw)
                    
                    if image_url:
                        st.image(image_url, width="stretch", caption=place_disp_name_raw)
                    else:
                        st.image("https://images.unsplash.com/photo-1469854523086-cc02fe5d8800?auto=format&fit=crop&q=80&w=800", width="stretch", caption="No Image" if is_en else "Resim Yok")
                    
                    # 2. Place Title & Rating Row using HTML
                    try:
                        rating_val = float(place.get("rating") or 0)
                    except (TypeError, ValueError):
                        rating_val = 0.0
                    st.markdown(f"""
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 10px; margin-bottom: 15px;">
                        <span style="font-size: 1.5rem; font-weight: 600; color: #0f172a;">{place_disp_name}</span>
                        <span class="rating-badge">⭐ {rating_val:.1f} / 5.0</span>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # 3. Dynamic Description Display
                    place_desc = place.get('description_en', '') if is_en else place.get('description_tr', '')
                    if not place_desc:
                        place_desc = place.get('description_tr', '') if is_en else place.get('description_en', '')
                    safe_place_desc = safe_text(place_desc)
                        
                    desc_box_class = "desc-box-en" if is_en else "desc-box-tr"
                    lang_label = "English Translation" if is_en else "Türkçe Tanıtım"
                    
                    snippet_len = 260
                    if len(place_desc) > snippet_len:
                        snippet = safe_text(place_desc[:snippet_len].rsplit(' ', 1)[0] + "...")
                        st.markdown(f"""
                        <div class="{desc_box_class}" style="margin-bottom: 5px;">
                            <div class="lang-label">{lang_label}</div>
                            <p style="margin: 0; color: #334155; line-height: 1.5;">{snippet}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        details_label = "Read Full Guide" if is_en else "Devamını Oku"
                        details_heading = "Detailed Guide" if is_en else "Detaylı Tanıtım"
                        st.markdown(f"""
                        <details class="read-more-panel">
                            <summary class="read-more-summary">
                                <span>{details_label}</span>
                                <span class="read-more-icon">+</span>
                            </summary>
                            <div class="read-more-body">
                                <div class="detail-label">{details_heading}</div>
                                <p>{safe_place_desc}</p>
                            </div>
                        </details>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div class="{desc_box_class}">
                            <div class="lang-label">{lang_label}</div>
                            <p style="margin: 0; color: #334155; line-height: 1.5;">{safe_place_desc}</p>
                        </div>
                        """, unsafe_allow_html=True)
                
                # Add spacing between row card items
                st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

# Footer info
footer_text = "AI Travel Guide Project • Developed with Python, Streamlit & Strapi CMS." if is_en else "YZ Destekli Gezi Rehberi Final Projesi • Python, Streamlit & Strapi CMS ile geliştirilmiştir."
st.markdown(f"""
<div class="footer">
    <p>{footer_text}</p>
</div>
""", unsafe_allow_html=True)
