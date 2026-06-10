@echo off
echo ============================================
echo   YZ Destekli Gezi Rehberi - Baslat
echo   AI-Powered Travel Guide - Start
echo ============================================
echo.

REM Step 1: Run automation pipeline
echo [1/2] Otomasyon pipeline'i calistiriliyor...
echo        (Ceviri, gorsel uretimi ve Strapi'ye veri yuklemesi)
echo.
cd automation
if not exist venv (
    echo Sanal ortam olusturuluyor...
    python -m venv venv
)
call venv\Scripts\activate
pip install -r requirements.txt -q
echo.
python main.py
echo.
cd ..

REM Step 2: Launch Streamlit frontend
echo.
echo [2/2] Streamlit arayuzu baslatiliyor...
echo        Tarayicinizda http://localhost:8501 adresi acilacaktir.
echo.
cd frontend-streamlit
if not exist venv (
    echo Sanal ortam olusturuluyor...
    python -m venv venv
)
call venv\Scripts\activate
pip install -r requirements.txt -q
echo.
streamlit run app.py
cd ..
