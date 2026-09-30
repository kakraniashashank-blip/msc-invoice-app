@echo off
title MSC Invoice Generator - Background Server
color 0A

echo ========================================================
echo MSC INVOICE APP IS STARTING...
echo ========================================================
echo.
echo IMPORTANT TIP:
echo Please DO NOT click or highlight text inside this black window. 
echo Windows "QuickEdit" mode will pause the app and make it look like 
echo it is "sleeping" or frozen until you press Enter.
echo.
echo If the app ever stops responding, just come here and press ENTER.
echo.
echo ========================================================

cd /d "%~dp0"

:: Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

:: Run streamlit
python -m streamlit run app.py

pause
