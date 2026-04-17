@echo off
echo ================================================
echo  HELIOS Setup
echo ================================================

echo.
echo [1/4] Creating virtual environment...
python -m venv venv
call venv\Scripts\activate.bat

echo.
echo [2/4] Installing dependencies...
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

echo.
echo [3/4] Checking Ollama...
ollama list >nul 2>&1
if %errorlevel% neq 0 (
    echo  WARNING: Ollama not found. Install from https://ollama.ai
) else (
    echo  Ollama found. Pulling mistral model...
    ollama pull mistral
)

echo.
echo [4/4] Setup complete!
echo.
echo To run HELIOS:
echo   venv\Scripts\activate
echo   python helios_popup.py    (floating chat window)
echo   python main.py            (CLI mode)
echo.
pause
