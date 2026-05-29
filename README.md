---
title: Medicine Explainer
emoji: 💊
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
license: mit
---

# 💊 Medicine Explainer

> Upload a prescription or medicine pack image and get a plain-English
> explanation of what each medicine is commonly used for.
> Powered by local OCR and a local LLM — your data never leaves your machine.

---

⚠️ **Medical Disclaimer**
This tool provides general information only. It does **not** diagnose
conditions, recommend treatment, or replace advice from a doctor or
pharmacist. Always confirm medicine details with a qualified healthcare
professional before taking any medication.

---

## What it does

1. You upload a prescription image, medicine strip photo, or type a medicine name
2. Tesseract OCR reads the text from the image
3. The system identifies probable medicine names
4. A local LLM explains each medicine in simple English
5. Every result includes a confidence indicator and a safety disclaimer

## What it never does

- Diagnose any disease or condition
- Recommend a dosage
- Suggest starting, stopping, or changing medication
- Send your data to any external server

---

## Features

- 📷 Upload prescription or medicine pack images (JPG, PNG, BMP, TIFF)
- ⌨️ Type a medicine name directly
- 🔍 OCR with per-word confidence scoring
- 🤖 LLM explanations powered by Mistral 7B
- ⚠️ Honest uncertainty messaging when confidence is low
- 👴 Elderly-friendly UI — large text, minimal clutter
- 💾 SQLite cache — instant results for repeat lookups
- 🇮🇳 190,000+ Indian medicines database included

---

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit |
| OCR | Tesseract 5 + pytesseract |
| Image preprocessing | OpenCV |
| LLM (local) | Mistral 7B via Ollama |
| LLM (cloud) | Mistral 7B via HF Inference API |
| Medicine matching | RapidFuzz fuzzy matching |
| Indian medicines | 190,043 medicine database |
| FDA medicines | 50,000+ drug database |
| Cache | SQLite |
| Language | Python 3.11 |

---

## Quick start (local)

```bash
git clone https://github.com/gmayank20/medicine-explainer.git
cd medicine-explainer
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
ollama pull mistral:7b
cp .env.example .env
python -c "from app.db.cache import init_db; init_db()"
PYTHONPATH=. streamlit run app/main.py
```

---

## Safety design

Three layers of protection:

1. Prompt-level guardrails — never diagnose, never recommend dosage
2. Post-generation filter — catches dangerous phrases before display
3. Confidence-aware UI — warns when OCR confidence is low

---

## Limitations

- Handwritten prescriptions — OCR accuracy drops significantly
- Uncommon medicines — may not be in database
- Non-English text — English only in this version
- Drug interactions — explains individual medicines only

---

## License

MIT License

---

*For informational purposes only. Not a substitute for medical advice.*