# Medicine Explainer — Plain English Project Guide

> Written for someone who wants to understand what was built,
> why it is organised the way it is, and what each file actually does.
> No technical jargon. No assumptions.

---

## The big picture — what this app does in one paragraph

A user opens the app in their browser. They either upload a photo of a
prescription or type a medicine name. The app reads the photo, figures out
which words are medicine names, asks an AI to explain each medicine in simple
English, and shows the explanation with a clear warning that this is not
medical advice. Everything happens on the user's own computer — no data is
sent anywhere.

---

## Why the project is split into folders

Think of the project like a restaurant kitchen.

A good kitchen has separate stations — one for prep, one for cooking, one for
plating. Each station has one job. The chef at the grill doesn't need to know
how the dessert station works. If something breaks at the salad station, it
doesn't affect the grill.

This project works the same way. Each folder is a station with one clear job.

```
medicine-explainer/         ← The whole restaurant
│
├── app/                    ← The kitchen (all working code lives here)
│   ├── core/               ← The cooking stations (main logic)
│   ├── config/             ← The recipe book (settings and prompts)
│   ├── db/                 ← The fridge (stores things for later)
│   └── utils/              ← The prep station (helper tools)
│
├── data/                   ← The pantry (test images, database file)
├── tests/                  ← The quality checker (verifies things work)
└── docs/                   ← The manual (guides like this one)
```

---

## Every file explained in plain English

---

### app/config/settings.py
**What it is:** The control panel for the entire app.

**What it does:** Holds all the important numbers and names in one place.
Things like which AI model to use, where the database file lives, and how
confident OCR needs to be before we trust it.

**Why it exists in config/:** Because if you ever want to change the AI model
or move the database, you change it in one place here — not scattered across
ten different files.

**Real example of what's inside:**
```
OLLAMA_MODEL = "mistral:7b"       ← which AI brain to use
DB_PATH = "data/medicine_cache.db" ← where to save explanations
OCR_CONFIDENCE_HIGH = 0.75         ← 75% confidence = we trust this reading
```

---

### app/config/prompts.py
**What it is:** The instruction manual we give to the AI.

**What it does:** Contains the exact words we use to instruct Mistral on how
to behave. It tells the AI: always say "commonly used for", never diagnose,
never recommend a dose, always end with "confirm with your doctor".

**Why it exists in config/:** Because prompts are configuration, not logic.
They are instructions, not code. Keeping them here means you can improve
the AI's behaviour by editing this one file without touching anything else.

**Why this file matters for safety:** The safety of the entire app depends
heavily on this file. A badly written prompt could lead to the AI saying
something dangerous. This is why it is carefully written and stored
separately where it can be reviewed easily.

---

### app/db/cache.py
**What it is:** The memory system.

**What it does:** Every time the AI explains a medicine, that explanation
gets saved to a database. Next time someone asks about the same medicine,
the app returns the saved answer instantly instead of asking the AI again.

**Why it exists in db/:** Because database code is its own concern. It
handles reading and writing to storage — nothing to do with OCR or AI.

**Real world analogy:** Like a pharmacist who writes notes. First time
someone asks about Paracetamol, they look it up and write it down. Next
time someone asks, they read from their notes instead of looking it up
again. Faster and consistent.

**What gets saved:**
- The medicine name
- The explanation text
- Which AI model produced it
- When it was saved
- How many times it has been looked up

---

### app/utils/image_preprocessor.py
**What it is:** The photo enhancer.

**What it does:** Before OCR tries to read a prescription image, this file
cleans it up. It converts the photo to black and white, removes graininess,
improves contrast, and enlarges it if it is too small. Like adjusting the
brightness and contrast on a photo before reading it.

**Why it exists in utils/:** Because image processing is a helper task —
it supports the OCR engine but is not OCR itself. Keeping it separate means
the OCR engine stays clean and focused on its own job.

**Why this matters:** A blurry, dark, or small image produces terrible OCR
results. This file is what makes the difference between reading
"Paracetamol" and reading "P4r4c3t4m01".

---

### app/core/ocr_engine.py
**What it is:** The eyes of the app.

**What it does:** Takes a prescription image, runs it through Tesseract
(the OCR tool), and extracts all the text. But crucially — it also scores
how confident Tesseract is about each word it read. Low confidence means
the image was unclear and the user should be warned.

**Why it exists in core/:** Because OCR is a core function of the app —
one of the main things the app was built to do.

**The confidence scoring explained:**
Tesseract gives each word a score between 0 and 100. This file averages
all those scores and classifies the result:
- Above 75% → high confidence → "we read this clearly"
- 45% to 75% → medium confidence → "we think we read this correctly"
- Below 45% → low confidence → "we are not sure — please verify"

This is what drives the warning messages in the UI.

---

### app/core/medicine_extractor.py
**What it is:** The filter.

**What it does:** Takes the raw text from OCR — which includes everything
on the prescription: patient name, doctor name, dosage instructions, dates —
and picks out only the medicine names.

**Why it exists in core/:** Because identifying medicines is a core function,
separate from reading the image or explaining the medicine.

**How it decides what is a medicine — two strategies:**

Strategy 1 — Known medicines list:
The file has a list of about 80 common medicines. It uses fuzzy matching,
which means even if OCR misread "Paracetamol" as "Parasetamol", it still
matches. A score above 90 = confirmed. Between 75 and 90 = probable.

Strategy 2 — Medicine word endings:
International drug naming rules mean most medicines end in recognisable
patterns — "-cillin", "-mycin", "-prazole", "-statin" etc. If a word ends
in one of these, it is probably a medicine even if it is not on the list.

**What it ignores:**
Common words like "patient", "doctor", "tablet", "daily", "morning",
"after", "food" — these are explicitly filtered out so they never get
sent to the AI as medicine names.

---

### app/core/llm_explainer.py
**What it is:** The brain of the app.

**What it does:** Takes a medicine name, checks if it is already in the
cache, and if not, asks Mistral to explain it. It sends the carefully
written instructions from prompts.py along with the medicine name, gets
the response back, runs it through a safety filter, and returns the result.

**Why it exists in core/:** Because generating explanations is the most
important core function of the app.

**The safety filter explained:**
Even with careful instructions, an AI can sometimes say something it
should not. The safety filter scans every response before it is shown
to the user and replaces dangerous phrases. For example:
- "you should take" → becomes → "it is commonly taken"
- "stop taking" → becomes → "speak to your doctor about"
- "will cure" → becomes → "may help manage"

**Why temperature is set to 0.1:**
AI models have a "temperature" setting that controls how creative or
random their responses are. High temperature = more creative but less
predictable. For a medical information app, we want consistent and
factual responses every time — so we set it very low at 0.1.

---

### app/core/pipeline.py
**What it is:** The manager that connects everything.

**What it does:** This is the file that runs the whole show. When a user
submits something, the pipeline decides what to do:

If the user uploaded an image:
1. Send the image to the OCR engine → get text
2. Send the text to the medicine extractor → get medicine names
3. Send each medicine name to the LLM explainer → get explanations
4. Package everything into one result and return it

If the user typed a medicine name:
1. Skip straight to the LLM explainer → get explanation
2. Return the result

**Why it exists in core/:** Because orchestration is a core responsibility.

**Why this file matters:**
Before this file existed, OCR, extraction, and explanation were all
separate pieces that had never talked to each other. This file is what
connects them into a working product.

---

### app/main.py (not yet written)
**What it will be:** The face of the app — what users actually see.

**What it will do:** Build the Streamlit web interface. The upload button,
the results display, the confidence indicators, the safety disclaimers.
It will call pipeline.py and display whatever comes back.

**Why it lives in app/ directly:** Because it is the entry point — the
first file that runs when the app starts.

---

### data/medicine_cache.db
**What it is:** The database file — created automatically when the app runs.

**What it stores:** Every medicine explanation the AI has ever produced,
indexed by medicine name so lookups are instant.

**Why it is gitignored:** Because it is generated data, not source code.
Every developer who clones the project builds their own cache over time.

---

### .env
**What it is:** Your personal settings file.

**What it does:** Lets you override any setting from settings.py without
touching the code. On your machine it says "use mistral:7b". On a server
it might say "use a different model". Same code, different behaviour.

**Why it is gitignored:** Because it can contain sensitive information like
API keys. You never put .env on GitHub.

---

### requirements.txt
**What it is:** The shopping list.

**What it does:** Lists every Python package the project needs with the
minimum version required. When someone clones the project and runs
pip install -r requirements.txt, they get exactly the right packages.

---

### docs/GOTCHAS.md
**What it is:** The honest lessons-learned log.

**What it does:** Every real problem hit during setup is recorded here
with the exact fix. Prevents repeating the same mistakes.

---

## How the files talk to each other

Here is the journey of a single prescription image through the app:

```
User uploads image
        ↓
   main.py               ← receives the uploaded file
        ↓
   pipeline.py           ← decides what to do with it
        ↓
   ocr_engine.py         ← reads the text from the image
        ↑
   image_preprocessor.py ← cleans the image first
        ↓
   medicine_extractor.py ← picks out the medicine names
        ↓
   llm_explainer.py      ← asks Mistral to explain each medicine
        ↑
   prompts.py            ← provides the instructions for Mistral
        ↑
   settings.py           ← provides the model name and config
        ↓
   cache.py              ← saves the explanation for next time
        ↓
   pipeline.py           ← packages everything up
        ↓
   main.py               ← displays the result to the user
```

Every file has one job. No file tries to do everything.
That is what makes the project easy to understand, fix, and improve.

---

## The one-line summary of each file

| File | One line |
|---|---|
| settings.py | The control panel — all config in one place |
| prompts.py | The instruction manual for the AI |
| cache.py | The memory — saves answers so we don't ask twice |
| image_preprocessor.py | The photo enhancer — cleans images before reading |
| ocr_engine.py | The eyes — reads text from images with confidence scores |
| medicine_extractor.py | The filter — finds medicine names in raw text |
| llm_explainer.py | The brain — asks Mistral to explain medicines safely |
| pipeline.py | The manager — connects all the pieces together |
| main.py | The face — what the user actually sees |

---

*Last updated: Step 5 complete — pipeline.py written, UI next*
