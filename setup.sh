#!/bin/bash
# ============================================================
# MedAssist Health Suite – Environment Setup Script
# Run this once to create the virtual environment and install
# all dependencies for both projects.
# ============================================================

set -e  # Exit on error

echo "================================================"
echo "  MedAssist Health Suite – Setup"
echo "================================================"

# 1. Check Python
python3 --version || { echo "❌ Python 3 not found. Please install Python 3.9+"; exit 1; }

# 2. Create virtual environment
echo ""
echo "📦 Creating virtual environment (venv)..."
python3 -m venv venv
echo "✅ Virtual environment created at ./venv"

# 3. Activate venv
echo ""
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# 4. Upgrade pip
echo ""
echo "⬆️  Upgrading pip..."
pip install --upgrade pip --quiet

# 5. Install all requirements
echo ""
echo "📥 Installing all dependencies (this may take a few minutes)..."
pip install -r requirements.txt

echo ""
echo "================================================"
echo "  ✅ All dependencies installed successfully!"
echo "================================================"

# 6. Check for system dependencies
echo ""
echo "🔍 Checking system dependencies for OCR..."

# Tesseract
if command -v tesseract &>/dev/null; then
    echo "  ✅ Tesseract OCR: $(tesseract --version 2>&1 | head -1)"
else
    echo "  ⚠️  Tesseract OCR not found."
    echo "     Ubuntu/Debian: sudo apt-get install tesseract-ocr"
    echo "     macOS:         brew install tesseract"
    echo "     Windows:       https://github.com/UB-Mannheim/tesseract/wiki"
fi

# Poppler (for pdf2image)
if command -v pdftoppm &>/dev/null; then
    echo "  ✅ Poppler (pdf2image): found"
else
    echo "  ⚠️  Poppler not found."
    echo "     Ubuntu/Debian: sudo apt-get install poppler-utils"
    echo "     macOS:         brew install poppler"
    echo "     Windows:       https://github.com/oschwartz10612/poppler-windows"
fi

echo ""
echo "================================================"
echo "  🚀 How to run the app:"
echo ""
echo "  1. Activate the venv:"
echo "     source venv/bin/activate   (Linux/macOS)"
echo "     venv\\Scripts\\activate      (Windows)"
echo ""
echo "  2. Set your Gemini API key (for chatbot):"
echo "     export GEMINI_API_KEY=your_key_here"
echo "     OR add it to .streamlit/secrets.toml:"
echo "     GEMINI_API_KEY = \"your_key_here\""
echo ""
echo "  3. Run the app:"
echo "     streamlit run app.py"
echo ""
echo "================================================"
