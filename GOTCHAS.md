# Gotchas & Fixes — Medicine Explainer

> A running log of real issues hit during setup and how they were resolved.
> Updated as the project progresses. Phase and step are noted for each entry.

---

## Phase 0 · Step 1 — System Setup

---

### Gotcha 1 — `ollama pull` interrupted mid-download

**What happened:**
Running `ollama pull mistral:7b` started a ~4.1 GB download. Pressing Enter
mid-download caused confusion about whether the download had stopped or was
still running.

**Why it happens:**
The `&` in `ollama serve &` puts the server in the background. Any key press
after that just adds a blank line — it does not interrupt the download. However
if the terminal session itself was reset, the download could genuinely stop.

**How to check state:**
```bash
ollama list
# If mistral:7b appears with a size → download completed fine
```

**How to fix if interrupted:**
```bash
ollama pull mistral:7b
# Ollama resumes from where it stopped — does not re-download from scratch
```

**Lesson:** Ollama pull is resumable. Never re-download from zero.

---

### Gotcha 2 — Ollama server logs appearing in terminal

**What happened:**
After running `curl http://localhost:11434`, the terminal showed GIN server
logs instead of a clean response.

**Why it happens:**
The Ollama server was started with `ollama serve &` in the same terminal
session. GIN logs are normal — they confirm the server is running correctly.

**Best practice:**
Run `ollama serve` in a dedicated terminal tab. Do all project work in a
separate tab.

**Quick verify:**
```bash
curl http://localhost:11434
# Expected: Ollama is running
```

---

### Gotcha 3 — `ollama list` showed empty NAME column after install

**What happened:**
Running `ollama list` right after installing Ollama showed no models.

**Why it happens:**
Installing Ollama does not include any models. Models must be pulled separately.

**Fix:**
```bash
ollama pull mistral:7b
```

---

### Gotcha 4 — `pip install` failed with `Invalid requirement: "cat > requirements.txt"`

**What happened:**
Pasting the `cat` heredoc and `pip install` together caused pip to read the
shell syntax as package names.

**Fix — always run as two separate commands:**
```bash
# Step 1: write the file
cat > requirements.txt << 'EOF'
streamlit>=1.32.0
...
EOF

# Step 2: install
pip install -r requirements.txt
```

**Lesson:** Never paste file-creation and pip install in the same block.

---

### Gotcha 5 — Project folder did not exist at verification time

**What happened:**
`ls ~/Desktop/medicine-explainer` returned "No such file or directory".

**Fix:**
```bash
mkdir ~/Desktop/medicine-explainer
cd ~/Desktop/medicine-explainer
# Then run all mkdir -p and touch commands
```

---

### Gotcha 6 — pip upgraded itself then threw a version note

**What happened:**
pip self-upgrade from 26.1 to 26.1.1 looked alarming alongside the later error.

**Why it happens:**
Completely normal. Safe to ignore as long as it says "Successfully installed".

---

## Phase 0 · Step 2 — Settings + Database

*No gotchas encountered. All commands ran cleanly.*

---

## Phase 0 · Step 3 — Prompts + LLM Explainer

*No gotchas encountered. Mistral responded correctly on first run.*

---

## Phase 0 · Step 4 — OCR Engine

*No gotchas encountered. OCR confidence scored at 0.77 (high) on test image.*

---

## Phase 0 · Step 5 — Medicine Extractor

*No gotchas encountered. Paracetamol and Amoxicillin extracted with 100%
match score. Patient name, doctor name, and dosage correctly ignored.*

---

## Phase 0 · Step 6 — Pipeline

*No gotchas encountered. Both image and typed name paths worked correctly.*

---

## Phase 0 · Step 7 — Streamlit UI

---

### Gotcha 7 — ModuleNotFoundError: No module named 'app'

**What happened:**
Running `streamlit run app/main.py` threw ModuleNotFoundError.

**Why it happens:**
Streamlit doesn't know to look for modules from the project root folder.

**Fix:**
```bash
PYTHONPATH=. streamlit run app/main.py
```

**The correct command to start the app every time:**
```bash
cd ~/Desktop/medicine-explainer
source venv/bin/activate
PYTHONPATH=. streamlit run app/main.py
```

**Lesson:** Always prefix with `PYTHONPATH=.` for projects with package structure.

---

### Gotcha 8 — Medicine cards and disclaimer box text invisible

**What happened:**
Medicine cards and disclaimer box showed invisible text — only visible when
selected with cursor.

**Why it happens:**
Streamlit's theming overrides custom CSS text colours unless forced.

**Fix:**
Use dark backgrounds with white text and `!important` on all colour rules:
```css
.medicine-card {
    background-color: #1a365d !important;
    color: #ffffff !important;
}
```

**Lesson:** Always use `!important` on Streamlit custom CSS colour rules.

---

## Phase 1 — Indian Medicine Database Integration

---

### Gotcha 9 — Guaifenesin falsely mapping to Amlodipine

**What happened:**
International generic name `Guaifenesin` mapped to `Amlodipine` incorrectly.

**Why it happened:**
`_clean_name` stripped too much from some names, leaving single character
keys like `'a'`, `'s'`, `'e'` in the dictionary. `'guaifenesin'` contains
those characters so partial match fired incorrectly.

**Fix:**
Added minimum key length of 4 characters when building the dictionary,
and minimum length of 6 on both query and key during partial matching.

---

### Gotcha 10 — Guaifenesin matching a combination drug

**What happened:**
After fixing Gotcha 9, Guaifenesin still mapped to `Ambroxol + Guaifenesin`
from an Indian combination drug `StayHappi Ambroxol+Guaifenesin+Terbutaline`.

**Why it happened:**
Partial match checked if query appeared anywhere inside a brand name —
including inside long combination drug names.

**Fix:**
Changed partial matching to only fire when query matches the START of a
brand name using `key.startswith(cleaned_query)`.

**Lesson:** Always anchor medical name matches to the start of strings.

---

## Phase 1 — GitHub Setup

---

### Gotcha 11 — venv folder being tracked by Git

**What happened:**
`git status` showed thousands of files from the `venv/` folder being staged.

**Why it happens:**
`.gitignore` was not in effect before `git init` was run, so Git cached
all files including venv before the ignore rules were applied.

**Fix:**
```bash
rm -rf .git
git init
git add .
git status
```

Starting fresh with `.gitignore` already in place prevents venv from
ever being staged.

**Lesson:** Always create `.gitignore` before running `git init`.

---

### Gotcha 12 — Large data files tracked by Git

**What happened:**
`drug-ndc-0001-of-0001.json.zip` appeared in `git status` — too large
for GitHub (limit is 100MB).

**Why it happens:**
The zip file was in the project root, not in `data/`, so the `.gitignore`
rule for `data/` didn't catch it.

**Fix:**
Added root-level entry to `.gitignore`:
```
drug-ndc-0001-of-0001.json.zip
```
Then removed from staging:
```bash
git rm --cached drug-ndc-0001-of-0001.json.zip
```

---

### Gotcha 13 — GitHub push requires Personal Access Token

**What happened:**
Git push asked for username and password. Using GitHub account password
failed with authentication error.

**Why it happens:**
GitHub removed password authentication in 2021. Personal Access Tokens
are required instead.

**Fix:**
1. Go to https://github.com/settings/tokens
2. Generate new token (classic) with `repo` permissions
3. Use token as password when Git prompts

---

## Phase 1 — Hugging Face Deployment

---

### Gotcha 14 — HF Space configuration error in README

**What happened:**
HF Space showed "configuration error" because README had no HF metadata.

**Fix:**
Add yaml frontmatter at the very top of README.md:
```yaml
---
title: Medicine Explainer
emoji: 💊
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
license: mit
---
```

---

### Gotcha 15 — Dockerfile failed: `libgl1-mesa-glx` not found

**What happened:**
Build failed with:
```
E: Package 'libgl1-mesa-glx' has no installation candidate
```

**Why it happens:**
HF Spaces uses Debian Trixie where `libgl1-mesa-glx` has been replaced
by `libgl1`.

**Fix:**
Replace in Dockerfile:
```dockerfile
# Before
libgl1-mesa-glx

# After
libgl1
```

**Lesson:** Always check package names against the target Debian version.

---

### Gotcha 16 — `llm_cloud.py` missing from repository

**What happened:**
HF build failed with `ModuleNotFoundError: No module named 'app.core.llm_cloud'`.

**Why it happened:**
The file was never created locally — only described in the blueprint.

**Fix:**
Create the file manually in VS Code, then commit and push:
```bash
git add .
git commit -m "Add missing llm_cloud.py"
git push origin main
git push space main
```

---

### Gotcha 17 — HF push rejected: authentication failed

**What happened:**
`git push space main` returned "Invalid username or password".

**Why it happens:**
HF requires a token with write permissions embedded in the remote URL.

**Fix:**
```bash
git remote set-url space https://USERNAME:hf_TOKEN@huggingface.co/spaces/USERNAME/SPACE
```

---

### Gotcha 18 — HF push rejected: fetch first

**What happened:**
Push rejected because HF Space had default files not present locally.

**Fix:**
```bash
git pull space main --allow-unrelated-histories
git push space main --force
```

---

### Gotcha 19 — HF Inference API: model not supported

**What happened:**
Multiple model errors when trying to use HF Inference API:
- `mistralai/Mistral-7B-Instruct-v0.3` → not a chat model
- `HuggingFaceH4/zephyr-7b-beta` → not supported by provider
- `meta-llama/Llama-3.2-3B-Instruct` → not supported by any enabled provider

**Why it happens:**
HF free tier has restricted which models are accessible via Inference API.
Most good models require paid Pro subscription or third-party API credits.

**Fix:**
Switched to Groq API (genuinely free, fast, reliable).

---

### Gotcha 20 — Gemini API: HTTP 429 quota exceeded

**What happened:**
After switching to Gemini, got HTTP 429 "quota exceeded" on free tier.

**Why it happens:**
Gemini free tier has strict per-minute rate limits.

**Fix:**
Switched to Groq API which has a more generous free tier.

---

### Gotcha 21 — Groq model decommissioned: `llama3-8b-8192`

**What happened:**
Groq returned HTTP 400:
```
The model llama3-8b-8192 has been decommissioned
```

**Fix:**
Updated model name to current version:
```python
"model": "llama-3.1-8b-instant"
```

**Lesson:** Always check provider deprecation pages when models stop working.
Current Groq models: https://console.groq.com/docs/deprecations

---

## Quick Reference — Verified Working Versions

| Tool | Version | Install method |
|---|---|---|
| macOS chip | Apple M5 | — |
| Python | 3.11.15 | `brew install python@3.11` |
| Tesseract | 5.5.2 | `brew install tesseract` |
| Ollama | running | `brew install ollama` |
| mistral:7b | 4.4 GB | `ollama pull mistral:7b` |
| streamlit | 1.57.0 | requirements.txt |
| pytesseract | 0.3.13 | requirements.txt |
| opencv-python-headless | 4.13.0.92 | requirements.txt |
| ollama (python) | 0.6.2 | requirements.txt |
| rapidfuzz | 3.14.5 | requirements.txt |
| sqlite-utils | 3.39 | requirements.txt |
| Cloud LLM | Groq llama-3.1-8b-instant | API key |

---

## Command to start the app locally

```bash
cd ~/Desktop/medicine-explainer
source venv/bin/activate
PYTHONPATH=. streamlit run app/main.py
```

Open browser at: http://localhost:8501

---

## Live deployment

```
https://huggingface.co/spaces/gmayank20/medicine-explainer
```

---

## Push to both remotes

```bash
git add .
git commit -m "your message"
git push origin main
git push space main
```

---

## Uninstall Everything

```bash
# 1. Remove project
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
```

---

*Last updated: Deployment complete — app live on Hugging Face Spaces*
