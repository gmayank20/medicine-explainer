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
# Ollama resumes from where it stopped — it does not re-download from scratch
```

**Lesson:** Ollama pull is resumable. Never re-download from zero.

---

### Gotcha 2 — Ollama server logs appearing in terminal

**What happened:**
After running `curl http://localhost:11434`, the terminal showed GIN server
logs like:
```
[GIN] 2026/05/28 - 13:56:58 | 200 | 164.708µs | 127.0.0.1 | HEAD "/"
```
instead of a clean response.

**Why it happens:**
The Ollama server was started with `ollama serve &` in the same terminal
session. Its log output mixes into the same terminal stream. The GIN logs
are just Ollama's internal HTTP framework logging every request — they are
normal and not errors.

**What the logs mean:**
- `200` = request succeeded
- `HEAD "/"` or `GET "/api/tags"` = health check requests from curl
- These logs confirm the server is running correctly

**Best practice going forward:**
Run `ollama serve` in a dedicated terminal tab and keep it open. Do all
project work in a separate tab. This keeps logs visible but out of the way.

**Quick verify Ollama is running:**
```bash
curl http://localhost:11434
# Expected clean output: Ollama is running
```

---

### Gotcha 3 — `ollama list` showed empty NAME column after install

**What happened:**
Running `ollama list` right after installing Ollama showed:
```
NAME    ID    SIZE    MODIFIED
```
with no models listed.

**Why it happens:**
Installing Ollama does not include any models. Models must be pulled
separately. The `ollama pull` command is a distinct step.

**Fix:**
```bash
ollama pull mistral:7b
# Wait for full download (~4.4 GB on M5)
```

**After successful pull:**
```bash
ollama list
# NAME          ID              SIZE      MODIFIED
# mistral:7b    6577803aa9a0    4.4 GB    About a minute ago
```

---

### Gotcha 4 — `pip install` failed with `Invalid requirement: "cat > requirements.txt"`

**What happened:**
Running the combined command block:
```bash
cat > requirements.txt << 'EOF'
streamlit>=1.32.0
...
EOF
pip install -r requirements.txt
```
caused pip to throw:
```
ERROR: Invalid requirement: "cat > requirements.txt << 'EOF'"
```

**Why it happens:**
When the `cat` heredoc and `pip install` are pasted together as one block,
the shell may execute `pip install` before the file write completes, or pip
itself reads the heredoc syntax as package names.

**Fix — always run as two separate commands:**
```bash
# Step 1: write the file
cat > requirements.txt << 'EOF'
streamlit>=1.32.0
pytesseract>=0.3.10
Pillow>=10.0.0
opencv-python-headless>=4.8.0
ollama>=0.1.7
python-dotenv>=1.0.0
rapidfuzz>=3.5.0
sqlite-utils>=3.35
numpy>=1.24.0
EOF

# Step 2: install from the file
pip install -r requirements.txt
```

**Lesson:** Never paste shell file-creation and pip install in the same
terminal block. Write file first, verify it exists, then install.

---

### Gotcha 5 — Project folder did not exist at verification time

**What happened:**
Running `ls ~/Desktop/medicine-explainer` returned:
```
ls: /Users/Mayank/Desktop/medicine-explainer: No such file or directory
```

**Why it happens:**
The scaffold creation step was skipped or not run before verification.

**Fix:**
```bash
mkdir ~/Desktop/medicine-explainer
cd ~/Desktop/medicine-explainer
# Then run all mkdir -p and touch commands from the scaffold step
```

**Lesson:** Always verify the folder exists before running any Python imports
that assume relative paths like `app/config/settings.py`.

---

### Gotcha 6 — pip upgraded itself then threw a version note

**What happened:**
Running `pip install --upgrade pip` showed:
```
Found existing installation: pip 26.1
Successfully uninstalled pip-26.1
Successfully installed pip-26.1.1
```
This looked alarming alongside the later error.

**Why it happens:**
Completely normal — pip upgrades itself from 26.1 to 26.1.1. Not an error.
The actual error that followed was Gotcha 4 (the cat/pip mix-up), unrelated
to the pip upgrade.

**Lesson:** pip self-upgrade output is always safe to ignore as long as it
says `Successfully installed`.

---

## Phase 0 · Step 2 — Settings + Database

*No gotchas encountered. All commands ran cleanly.*

---

## Quick Reference — Verified Working Versions

| Tool | Version | Install method |
|---|---|---|
| macOS chip | Apple M5 | — |
| Python | 3.11.15 | `brew install python@3.11` |
| Tesseract | 5.5.2 | `brew install tesseract` |
| Ollama | running | `brew install ollama` |
| mistral:7b | 4.4 GB | `ollama pull mistral:7b` |
| pip | 26.1.1 | auto-upgraded in venv |
| streamlit | 1.57.0 | requirements.txt |
| pytesseract | 0.3.13 | requirements.txt |
| opencv-python-headless | 4.13.0.92 | requirements.txt |
| ollama (python) | 0.6.2 | requirements.txt |
| rapidfuzz | 3.14.5 | requirements.txt |
| sqlite-utils | 3.39 | requirements.txt |

---

## Uninstall Everything

Run in this exact order when the project is complete and you want a clean slate:

```bash
# 1. Remove project (code + venv + database)
rm -rf ~/Desktop/medicine-explainer

# 2. Remove Homebrew Python 3.11
brew uninstall python@3.11

# 3. Remove Tesseract
brew uninstall tesseract

# 4. Remove Ollama model first (frees 4.4 GB)
ollama rm mistral:7b

# 5. Remove Ollama app
brew uninstall ollama

# 6. Remove Ollama hidden data folder
rm -rf ~/.ollama
```

> Note: This does not remove Homebrew itself.
> To remove Homebrew: `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/uninstall.sh)"`

---

*Last updated: Phase 0 · Step 2 complete*