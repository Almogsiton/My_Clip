@echo off
cd /d "%~dp0"

echo Starting ClipMaker...

if exist venv\Scripts\activate.bat (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo Virtual environment not found, trying global python...
)

echo Running Streamlit app...
streamlit run app.py

if %errorlevel% neq 0 (
    echo.
    echo An error occurred. Please check the output above.
    pause
)
