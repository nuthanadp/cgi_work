@echo off
echo 🏦 Starting APS - Automatic Payment System Frontend
echo ================================================

echo 📦 Installing dependencies...
pip install -r requirements.txt

echo.
echo 🚀 Launching Streamlit app...
echo.
echo Open your browser and go to: http://localhost:8501
echo.
echo To stop the app, press Ctrl+C
echo.

streamlit run streamlit_app.py