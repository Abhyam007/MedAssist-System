# 🏥 MedAssist Health Suite

A fully integrated medical web application that merges two projects:
- **OCR3** – Medical Report OCR & Analysis System  
- **medchat-streamlit** – AI-powered Medical Chatbot (Gemini + RAG)

---

## 🚀 Quick Start

### 1. Setup (one-time)
```bash
bash setup.sh
```

### 2. Activate environment
```bash
# Linux/macOS
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. Configure Gemini API Key (for chatbot)
Create `.streamlit/secrets.toml`:
```toml
GEMINI_API_KEY = "your_gemini_api_key_here"
```
Or set as environment variable:
```bash
export GEMINI_API_KEY="your_gemini_api_key_here"
```

### 4. Run the app
```bash
streamlit run app.py
```

---

## 📁 Project Structure

```
merged_app/
├── app.py                  # Main unified application
├── config.py               # Unified configuration (OCR + Gemini)
├── auth.py                 # User authentication
├── data_manager.py         # Report CRUD operations
├── ocr_processor.py        # PDF OCR processing
├── visualizer.py           # Plotly charts
├── gemini_engine.py        # Gemini AI integration
├── rag_engine.py           # FAISS vector store RAG
├── csv_engine.py           # CSV-based symptom lookup
├── txt_engine.py           # TXT-based medical info
├── requirements.txt        # All dependencies
├── setup.sh                # Automated setup script
├── data/
│   ├── users.json          # User accounts
│   ├── family_profiles.json
│   ├── reports/            # Per-user Excel reports
│   ├── medical.csv         # Med chatbot CSV data
│   └── medical.txt         # Med chatbot TXT data
└── vectorstore/
    └── db_faiss/           # FAISS vector database
```

---

## ✨ Features

### 🏠 Home Page (Post-Login)
- Welcome dashboard with two prominent buttons
- **Report Analysis** (left half) – navigates to OCR/report system
- **Med Chatbot** (right half) – navigates to AI chatbot
- Quick stats: total reports, family members, latest report date

### 📊 Report Analysis
- Upload PDF medical reports via OCR
- Manual entry of medical parameters
- Support for: Blood Test, LFT, CBP, Thyroid, Vitals, Ultrasound
- Family member profile management

### 📈 Dashboard
- Trend charts for medical parameters over time
- Latest report metrics

### 📋 All Reports
- View all reports in tabular format
- **Permanent Delete** – one-click delete that immediately removes the report from both Excel storage and the UI
- Download reports as Excel

### 🤖 Med Chatbot
- Describe symptoms in natural language
- RAG-powered responses using FAISS + medical PDF/CSV/TXT
- Gemini AI fallback for general medical queries
- Chat history within session

### 👨‍👩‍👧‍👦 Family Profiles
- Add/remove family members
- Switch profiles to manage multiple people's reports

---

## 🛠 System Requirements

| Dependency | Purpose | Install |
|-----------|---------|---------|
| Python 3.9+ | Runtime | python.org |
| Tesseract OCR | PDF text extraction | `apt install tesseract-ocr` |
| Poppler | PDF to image | `apt install poppler-utils` |
| Gemini API Key | AI chatbot | aistudio.google.com |

---

## 🔑 API Keys

| Key | Where to get | Required for |
|-----|-------------|--------------|
| `GEMINI_API_KEY` | https://aistudio.google.com | Med Chatbot AI responses |
| `OCR_SPACE_API_KEY` | Already set in config.py | PDF OCR (backup) |
