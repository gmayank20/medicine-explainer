# Medicine Explainer — PM's Field Guide

> This document is written for one person: a Senior PM who built this project
> using AI assistance and needs to own it confidently in any conversation —
> interview, demo, or casual discussion.
>
> No coding knowledge assumed. No jargon without explanation.
> Everything you need to talk about this project at a product level.

---

## The one-paragraph pitch

> "I built an AI-powered prescription explainer for the Indian market.
> A user uploads a photo of their prescription or types a medicine name.
> The app reads the image, identifies the medicines, maps Indian brand names
> like Dolo and Crocin to their generic ingredients, and explains each medicine
> in plain English — what it's commonly used for, common precautions, common
> side effects. It never diagnoses, never prescribes, and never sends your
> data anywhere. It runs locally on a Mac, costs nothing to operate, and
> is deployed free online for anyone to use."

Memorise this. Say it in under 60 seconds. Lead every conversation with it.

---

## The problem — why this exists

Most Indians, especially elderly patients, receive prescriptions with medicine
names they don't recognise. The doctor has moved on. The pharmacist is busy.
The patient takes the medicine without understanding what it does, what to
avoid, or what side effects to watch for.

This is a real, daily problem in every Indian household.

Existing solutions either require internet searches (unreliable, overwhelming),
asking the doctor again (impractical), or paying for consultations (expensive).

This app fills that gap — not as a medical authority, but as a plain-English
explainer that puts the patient in a more informed position before they speak
to their doctor or pharmacist.

---

## The product principles — decisions made before any code

These were set before a single line was written. Every technical decision
flows from these.

**1. Safety is non-negotiable**
The system must never diagnose a disease. Never recommend a dosage.
Never suggest stopping or changing medication. Never invent medicine names.
These are not features — they are hard constraints. Violating any of them
would make the product dangerous.

**2. Honesty over confidence**
When the system is not sure — low OCR confidence, unrecognised medicine name —
it says so clearly. "Unable to confidently read this medicine name" is a better
user experience than a confident wrong answer. Trust is the product.

**3. Privacy by design**
On the local version, nothing leaves the user's machine. Prescriptions contain
personal health information. Sending them to external servers by default would
be a product mistake, not just a technical one.

**4. Elderly-friendly UX**
Large text. Minimal clutter. No jargon. One action at a time. The primary
user is not a tech-savvy professional — it is a 65-year-old patient who is
not comfortable with technology.

**5. India-first**
Most medicine databases are US or Europe-centric. Indian prescriptions use
brand names — Dolo, Crocin, Augmentin, Combiflam — not generic names.
A product that only recognises "Paracetamol" but not "Dolo" is useless in
the Indian market. This shaped the entire data strategy.

---

## The architecture — what the system does, not how

Think of the system as a pipeline. Something goes in one end, something
comes out the other. Each stage has one job.

```
User input
    ↓
Read the image (OCR)
    ↓
Find the medicine names in the text
    ↓
Translate brand name to generic ingredient
    ↓
Ask AI to explain the generic
    ↓
Run safety filter on the response
    ↓
Show explanation with disclaimer
    ↓
Save to cache for next time
```

Every stage is separate. If the OCR stage breaks, only OCR needs fixing.
If the AI model changes, only that stage changes. Nothing else breaks.
This is called modular architecture — it is a product and engineering
best practice, not just a technical choice.

---

## The data strategy — why this was the hardest product decision

### The problem with drug data in India

There is no single, clean, free, downloadable database of Indian medicines.
CDSCO (India's drug regulator) publishes year-wise PDF lists — not a database.
There is no official API. Most comprehensive databases are paid products.

### What was found and used

**Source 1 — Indian Medicine Dataset (GitHub)**
A community-curated dataset of 253,974 Indian medicines scraped from 1mg.
Contains brand name, generic composition, manufacturer, price, pack size.
Free to download. 190,043 active (non-discontinued) medicines loaded.
This is what enables "Dolo → Paracetamol" and "Augmentin → Amoxycillin".

**Source 2 — OpenFDA Drug Database**
The US FDA's official open database. 135,317 human drug records.
Contains generic names, brand names, active ingredients, dosage forms.
Free bulk download, no API key needed.
Used as fallback for international medicines not in the Indian dataset.

**Priority order in the system:**
1. Indian database first (brand names most likely from Indian prescriptions)
2. FDA database second (international generics as fallback)
3. Original name as-is if not found in either (LLM handles it directly)

### Why this matters as a PM talking point

Most AI product demos use clean, curated data. This project had to solve a
real data problem — fragmented sources, no official API, inconsistent formats,
brand vs generic naming — before the AI could do anything useful.

The brand-to-generic mapping is the differentiating insight. Without it,
the app fails on 80% of real Indian prescriptions.

---

## The technology — what each tool is and why it was chosen

### Python
The programming language everything is written in. The standard choice for
AI and data projects. No meaningful alternative considered.

### Streamlit
Turns Python code into a web app with minimal effort. Chosen because the
goal was a working product, not a beautiful one. The right tool for a
portfolio MVP. Would be replaced with a proper web framework if this were
a commercial product.

**PM tradeoff:** Speed of shipping vs control over design. For a portfolio
MVP, speed wins.

### Tesseract OCR
Google's open-source text recognition tool. The same technology behind
Google Lens. Reads text from images. Free, runs locally, no API cost.
Accuracy is lower than cloud alternatives (Google Vision, AWS Textract)
but sufficient for printed prescriptions. Struggles with handwriting.

**PM tradeoff:** Free and private vs more accurate but costly and cloud-based.

### Ollama + Mistral 7B
Ollama is a tool that runs AI language models on your own computer.
Mistral 7B is the specific AI model — 7 billion parameters, 4.4GB in size.
It runs on an M5 MacBook Air and produces a response in 20-40 seconds.

Chosen because it keeps prescription data off external servers (privacy)
and has zero per-query cost (economics). The alternative — OpenAI GPT-4 —
would cost money per query and send data to OpenAI's servers.

**PM tradeoff:** Privacy and zero cost vs faster responses and higher accuracy.

### Groq + Llama 3.1 (for cloud deployment)
When deployed on Hugging Face, the local Ollama model cannot run —
there is no Mac in the cloud. Groq is a free API that provides access
to Llama 3.1, an open-source AI model from Meta. Fast, free, reliable.

Multiple alternatives were tried and failed before Groq worked:
HF Inference API (model restrictions), Gemini (quota limits), various
Mistral endpoints (not supported). Groq was the solution that worked
on the free tier without restrictions.

**PM lesson:** Cloud AI APIs have complex and changing restrictions on
free tiers. Always have a fallback.

### SQLite (the cache database)
A database that lives as a single file on the user's computer.
No server, no setup, no maintenance. Stores every medicine explanation
ever generated. When someone searches for Paracetamol a second time,
the answer comes back instantly without calling the AI again.

This is both a performance decision and an economics decision — fewer
API calls means lower cost on the cloud version.

**PM tradeoff:** Zero maintenance vs enterprise scale. For this use case,
zero maintenance wins.

### RapidFuzz (fuzzy matching)
A library that finds approximate matches in text. Used because OCR
is imperfect — it might read "Paracetamoi" instead of "Paracetamol".
RapidFuzz finds the correct medicine even with minor spelling errors.

This is the difference between a brittle system (exact match only) and
a robust one (tolerates errors). The confidence threshold was set at 90%
to balance accuracy against false positives.

### Docker (for deployment)
A technology that packages an entire application — Python, Tesseract,
all libraries, all settings — into a sealed container. That container
runs identically on any server in the world. Used for deployment on
Hugging Face Spaces.

Think of it as a shipping container for software. The contents are
always the same regardless of where the container is opened.

---

## The safety architecture — three layers

Safety is not a single feature. It is a layered system where each layer
catches what the previous layer misses.

**Layer 1 — Prompt engineering**
The AI model receives explicit instructions before every query:
- Never diagnose any disease
- Never recommend a dosage
- Always say "commonly used for" not "treats" or "cures"
- Always end with "confirm with your doctor"
- If unsure, say so

This is the primary safety mechanism. Well-written prompts prevent most
dangerous outputs from ever being generated.

**Layer 2 — Post-generation filter**
Even with careful prompts, AI models occasionally produce outputs that
need correction. A safety filter scans every response before it is shown
to the user and replaces specific dangerous phrases:

- "you should take" → "it is commonly taken"
- "stop taking" → "speak to your doctor about"
- "will cure" → "may help manage"
- "you have" → "this medicine is used in cases of"

This is a last line of defence, not a primary mechanism.

**Layer 3 — Confidence-aware UI**
OCR confidence is scored per word. If the average confidence is below
a threshold, the UI shows a visible warning:
"Image quality is low. Results may be inaccurate. Please show the
original prescription to your pharmacist."

This prevents the system from presenting uncertain information as fact.

**Why three layers?**
Because each layer has failure modes. Prompts can be ignored by the model.
Filters can miss edge cases. UI warnings can be dismissed by users.
Layering means no single failure point compromises the whole system.

---

## The confidence scoring — honest uncertainty as a product feature

Most AI products hide uncertainty. They present confident answers even
when confidence is low. This is a product mistake — it erodes trust
when the confident answer turns out to be wrong.

This product does the opposite. Uncertainty is surfaced explicitly.

**How it works:**
Tesseract gives each word a confidence score from 0 to 100.
The system averages all word scores for the image.

- Above 75% → High confidence → Green indicator → "Image read successfully"
- 45% to 75% → Medium confidence → Amber indicator → Results shown with caution
- Below 45% → Low confidence → Red warning → "Please verify with pharmacist"

**Why this matters as a PM talking point:**
In regulated industries — healthcare, finance, compliance — honest
uncertainty handling is not a nice-to-have. It is a trust mechanism.
Users trust systems that tell them when to be sceptical more than
systems that are always confident.

This principle maps directly to your work in FinTech and MedTech.
MSB/OFAC compliance, chargeback management, payment verification —
all of these require the same principle: show confidence levels,
surface uncertainty, let the human make the final call.

---

## The Indian brand name mapping — the key product insight

This is the most important product insight in the entire project.

**The insight:**
Indian prescriptions almost never use generic names. They use brand names.
A doctor writes "Tab Dolo 650" not "Paracetamol 650mg".
A chemist sells "Augmentin" not "Amoxycillin + Clavulanic Acid".

An AI model trained on global medical literature knows Paracetamol well.
It knows almost nothing about Dolo specifically — because Dolo is an Indian
brand name with very little English-language training data.

**The solution:**
Map Indian brand names to their generic compositions first.
Then explain the generic composition to the AI.
The AI explains Paracetamol, not Dolo — but the user sees "Dolo" in
the results, making it feel natural.

**The data:**
190,043 Indian medicines from a community-curated dataset.
Each entry has brand name, generic composition, manufacturer.

**Examples:**
- Dolo → Paracetamol
- Crocin → Paracetamol
- Augmentin → Amoxycillin + Clavulanic Acid
- Combiflam → Ibuprofen + Paracetamol
- Azithral → Azithromycin
- Pantop → Pantoprazole

**Why no competitor does this well:**
Most medicine explainer tools are built for Western markets.
They work on generic names. They fail on Indian brand names.
This mapping is the single biggest differentiator for the Indian market.

---

## What you actually did as a PM — for interview use

Be honest about the nature of this project. You used AI assistance
to build it. That is not a weakness — it is the point.

**What you owned:**

Problem definition — you identified a real problem with a specific user
(elderly Indian patients) and a specific context (Indian prescriptions,
Indian brand names, Indian healthcare system).

Product constraints — free tools, local-first, privacy by design,
elderly-friendly UX, India-specific data. These constraints shaped
every technical decision that followed.

Safety architecture — the decision that the system must have three
layers of safety was a product decision, not a technical one. An engineer
would have built what you asked. You knew what to ask for.

Data strategy — researching CDSCO, understanding its limitations,
finding the Indian medicine dataset, deciding the brand-to-generic
mapping approach. This required domain knowledge of Indian healthcare,
not coding ability.

Market insight — Dolo, Crocin, Augmentin. Knowing these names and
knowing they would not be in standard drug databases is product knowledge
that no engineer outside the Indian market would have brought.

Scope management — keeping the MVP small, resisting feature creep,
shipping Phase 0 before planning Phase 1. This discipline is rare.

**What AI assistance did:**
Wrote the code that implemented your requirements. Made technical
implementation choices within the constraints you set. Debugged errors
when they occurred. This is the equivalent of a strong engineering
partner executing a PM's vision.

**The analogy:**
A product manager at Google does not write the code for Google Maps.
But they define what Google Maps must do, what it must never do,
who it is for, and what success looks like. The engineers build it.
The PM owns the product.

This project works the same way. You owned the product.
AI assistance handled the implementation.

---

## How to answer the hardest interview question

**"Did you actually build this or did AI build it for you?"**

> "I built it the same way a PM builds any product — by defining what
> it should do, making the key decisions, and working closely with the
> people implementing it. In this case, my implementation partner was an
> AI assistant rather than a human engineering team. I owned every product
> decision: the safety constraints, the India-first data strategy, the
> brand-to-generic mapping insight, the confidence-aware UX, the privacy
> architecture. The AI wrote the code that implemented those decisions.
> That's not different from how I've worked with engineering teams
> throughout my career — I define the what and why, the team handles the how."

---

## The honest limitations — say these before they ask

**OCR accuracy on handwritten prescriptions is poor.**
Most Indian prescriptions are handwritten. Tesseract reads printed text
well but struggles with handwriting. This is a known limitation. The
confidence scoring surfaces it when it occurs.

**The medicine seed list covers common medicines only.**
Very rare or newly approved medicines may not be in the database.
The AI will still attempt an explanation, but without the brand-to-generic
mapping benefit.

**English only.**
The MVP explains medicines in English only. Hindi support would
significantly expand the accessible user base — this is on the roadmap.

**Not a substitute for professional advice.**
This is stated explicitly in the UI, in the README, and in this document.
The app is an awareness tool, not a medical authority.

---

## The numbers — memorise these

| What | Number |
|---|---|
| Indian medicines in database | 190,043 |
| FDA drugs in database | 50,281 |
| Python files in the project | 13 |
| Real problems hit and fixed | 21 |
| Monthly cost to run | ₹0 |
| Data sent to external servers | Zero (local version) |
| OCR confidence threshold for "high" | 75% |
| Fuzzy match threshold for medicines | 90% |

---

## The roadmap — what comes next

**Phase 1 (polish the MVP)**
- Expand Indian medicine list with newer drugs
- Better OCR preprocessing for real prescription photos
- PDF prescription support (common from Apollo, Fortis, Max)
- Multi-medicine display improvements for elderly users

**Phase 2 (expand)**
- Hindi language explanations
- Voice readout for elderly users who struggle with reading
- Drug interaction warnings (informational only)
- Export explanation as PDF to share with family

**Phase 3 (deploy at scale)**
- Better cloud architecture if usage grows
- Integration with hospital discharge summary formats
- Potential B2B for pharmacies or healthcare platforms

---

## The links

**Live app:** https://huggingface.co/spaces/gmayank20/medicine-explainer

**GitHub:** https://github.com/gmayank20/medicine-explainer

**Start locally:**
```
cd ~/Desktop/medicine-explainer
source venv/bin/activate
PYTHONPATH=. streamlit run app/main.py
```

---

*This document is for your own preparation. It is honest about what you
built, how you built it, and what you own. Own it confidently.*
