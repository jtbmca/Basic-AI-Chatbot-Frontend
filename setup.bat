@echo off
REM Simple setup script for Windows

echo Setting up Tibs Chat Interface...

REM Install Python dependencies
echo Installing Python dependencies...
pip install -r requirements.txt

REM Create .env file if it doesn't exist
if not exist .env (
    echo Creating configuration file...
    copy config.env.example .env
    echo Configuration file created as .env
    echo Please edit .env to set your BERT model path and other settings
) else (
    echo .env file already exists
)

echo Setup complete!
echo.
echo Next steps:
echo 1. Edit .env file to set your BERT model path
echo 2. Make sure Ollama is running
echo 3. Run: streamlit run app.py
pause
