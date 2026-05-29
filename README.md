💊 Medicine Explainer

Upload a prescription or medicine pack image and get a plain-English
explanation of what each medicine is commonly used for.
Powered by local OCR and a local LLM — your data never leaves your machine.


⚠️ Medical Disclaimer
This tool provides general information only. It does not diagnose
conditions, recommend treatment, or replace advice from a doctor or
pharmacist. Always confirm medicine details with a qualified healthcare
professional before taking any medication.

What it does

You upload a prescription image, medicine strip photo, or type a medicine name
Tesseract OCR reads the text from the image
The system identifies probable medicine names
A local LLM (Mistral 7B via Ollama) explains each medicine in simple English
Every result includes a confidence indicator and a safety disclaimer

What it never does

Diagnose any disease or condition
Recommend a dosage
Suggest starting, stopping, or changing medication
Send your data to any external server


Demo

Screenshots and demo GIF will be added after UI is complete.


Features

📷 Upload prescription or medicine pack images (JPG, PNG, BMP, TIFF)
⌨️ Type a medicine name directly
🔍 OCR with per-word confidence scoring
🤖 Local LLM explanations — fully offline, no API key needed
⚠️ Honest uncertainty messaging when confidence is low
👴 Elderly-friendly UI — large text, minimal clutter
💾 SQLite cache — instant results for repeat lookups
🔒 100% local — prescriptions never leave your machine


Tech stack
LayerTechnologyFrontendStreamlitOCRTesseract 5 + pytesseractImage preprocessingOpenCVLLMMistral 7B via OllamaMedicine matchingRapidFuzz fuzzy matchingCacheSQLiteLanguagePython 3.11

Architecture
Upload (image / text)
        │
        ▼
   OCR Engine              ← Tesseract + confidence scoring
        │
        ▼
Medicine Extractor         ← Fuzzy match + suffix heuristics
        │
        ▼
  LLM Explainer            ← Mistral 7B via Ollama
        │
        ▼
Safety Guardrails          ← Post-generation filter
        │
        ▼
  Streamlit UI             ← Result + disclaimer
        │
        ▼
  SQLite Cache             ← Store for repeat lookups

Project structure
medicine-explainer/
│
├── app/
│   ├── main.py                   # Streamlit entry point
│   ├── core/
│   │   ├── pipeline.py           # Orchestrates full flow
│   │   ├── ocr_engine.py         # Tesseract + confidence scoring
│   │   ├── medicine_extractor.py # Name identification
│   │   ├── llm_explainer.py      # Ollama prompt + response
│   │   └── safety_guardrails.py  # Output safety filter
│   ├── db/
│   │   └── cache.py              # SQLite read/write
│   ├── utils/
│   │   ├── image_preprocessor.py # Contrast, denoise, resize
│   │   └── text_cleaner.py       # OCR output normalisation
│   └── config/
│       ├── settings.py           # Central config
│       └── prompts.py            # LLM prompt templates
│
├── data/
│   └── sample_images/            # Test images (gitignored)
│
├── tests/                        # Unit tests per module
├── docs/
│   ├── GOTCHAS.md                # Real issues hit + fixes
│   └── screenshots/
│
├── .env.example
├── requirements.txt
├── setup.sh
└── README.md

Prerequisites
ToolVersionInstallmacOSAny (M-series recommended)—Python3.11+brew install python@3.11Tesseract5.xbrew install tesseractOllamaLatestbrew install ollama

Quick start
1. Clone the repo
bashgit clone https://github.com/your-username/medicine-explainer.git
cd medicine-explainer
2. Create virtual environment
bashpython3.11 -m venv venv
source venv/bin/activate
3. Install dependencies
bashpip install -r requirements.txt
4. Pull the LLM model
bashollama pull mistral:7b
5. Configure environment
bashcp .env.example .env
# Edit .env if needed — defaults work out of the box
6. Initialise database
bashpython -c "from app.db.cache import init_db; init_db()"
7. Run
bashstreamlit run app/main.py
Open http://localhost:8501 in your browser.

Configuration
All settings live in .env:
envOLLAMA_MODEL=mistral:7b
OLLAMA_HOST=http://localhost:11434
DB_PATH=data/medicine_cache.db

Safety design
This project treats safety as a first-class concern, not an afterthought.
Three layers of protection:

Prompt-level guardrails — the system prompt instructs the LLM to
never diagnose, never recommend dosage, and always hedge with
"commonly used for" language.
Post-generation filter — a safety pass scans LLM output for
dangerous phrases ("you should take", "stop taking", "you have") and
either removes or neutralises them before display.
Confidence-aware UI — OCR confidence is scored per word. Low
confidence triggers a visible warning telling the user not to rely
on the result and to consult a pharmacist.

Hard rules the system never breaks:

Never diagnose a disease
Never recommend a dosage
Never suggest stopping or changing medication
Never invent medicine names
Always end with a "confirm with your doctor" message


Limitations
Being honest about what this MVP cannot do:

Handwritten prescriptions — OCR accuracy drops significantly.
Printed text works well; cursive handwriting is unreliable.
Uncommon medicines — the medicine seed list covers ~50 common
drugs. Rare or newly approved medicines may not be recognised.
Non-English text — English only in this version.
Drug interactions — this tool explains individual medicines only.
It cannot check for interactions between multiple medicines.
Image quality — blurry, low-light, or heavily shadowed photos
produce poor OCR results. The confidence indicator will flag this.
LLM accuracy — Mistral 7B has general medical knowledge but is
not a verified medical database. Explanations are for awareness only.


Roadmap
Phase 0 — Setup ✅
System dependencies, project scaffold, virtual environment, database
Phase 1 — Core pipeline (in progress)
Settings, database, prompts, LLM explainer, OCR engine, medicine extractor
Phase 2 — Streamlit UI
Upload interface, results display, confidence indicators, safety banners
Phase 3 — Polish
Expanded medicine list, better image preprocessing, PDF support, export
Phase 4 — Deploy
Hugging Face Spaces, Docker, environment-based model switching

Running tests
bashpytest tests/

Uninstall everything
bash# 1. Remove project
rm -rf ~/Desktop/medicine-explainer

# 2. Remove Python 3.11
brew uninstall python@3.11

# 3. Remove Tesseract
brew uninstall tesseract

# 4. Remove Ollama model (frees 4.4 GB)
ollama rm mistral:7b

# 5. Remove Ollama
brew uninstall ollama
rm -rf ~/.ollama

Contributing
This is a portfolio project but PRs are welcome. Please open an issue
first to discuss what you'd like to change.

License
MIT License — see LICENSE for details.

Author
Built by Mayank as a portfolio project demonstrating AI workflow
orchestration, responsible AI design, and full-stack Python development.

For informational purposes only. Not a substitute for medical advice.