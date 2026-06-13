@echo off
cd /d "%~dp0"
echo Installing dependencies...
pip install -r requirements.txt -q
echo.
echo Starting EduSpark Lead Gen App at http://localhost:8501
echo.
streamlit run app.py --server.port 8501
pause
