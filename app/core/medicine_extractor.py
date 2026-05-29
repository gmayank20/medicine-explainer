import re
from rapidfuzz import fuzz, process
from dataclasses import dataclass
from typing import List


# ── Seed list of common medicines ──────────────────────────────
# These are well-known generic names. Fuzzy matching means
# minor OCR errors (Paracetamoi vs Paracetamol) still match.
COMMON_MEDICINES_SEED = [
    "Paracetamol", "Ibuprofen", "Amoxicillin", "Azithromycin",
    "Metformin", "Atorvastatin", "Omeprazole", "Pantoprazole",
    "Cetirizine", "Loratadine", "Aspirin", "Metoprolol",
    "Amlodipine", "Lisinopril", "Losartan", "Gabapentin",
    "Sertraline", "Fluoxetine", "Alprazolam", "Diazepam",
    "Ciprofloxacin", "Doxycycline", "Prednisolone", "Dexamethasone",
    "Insulin", "Levothyroxine", "Warfarin", "Clopidogrel",
    "Ranitidine", "Ondansetron", "Domperidone", "Metoclopramide",
    "Atenolol", "Ramipril", "Montelukast", "Salbutamol",
    "Amitriptyline", "Clonazepam", "Esomeprazole", "Lansoprazole",
    "Metronidazole", "Fluconazole", "Acyclovir", "Oseltamivir",
    "Hydroxychloroquine", "Ivermectin", "Albendazole", "Paracetamol",
    "Diclofenac", "Naproxen", "Tramadol", "Codeine",
    "Morphine", "Fentanyl", "Oxycodone", "Hydrocodone",
    "Methylprednisolone", "Hydrocortisone", "Betamethasone",
    "Clindamycin", "Erythromycin", "Clarithromycin", "Cephalexin",
    "Amoxicillin", "Ampicillin", "Piperacillin", "Vancomycin",
    "Telmisartan", "Valsartan", "Candesartan", "Olmesartan",
    "Rosuvastatin", "Simvastatin", "Pravastatin", "Lovastatin",
    "Glibenclamide", "Glimepiride", "Glipizide", "Sitagliptin",
    "Empagliflozin", "Dapagliflozin", "Liraglutide", "Insulin",
    "Thyroxine", "Carbimazole", "Propylthiouracil",
    "Ferrous Sulphate", "Folic Acid", "Vitamin D", "Calcium",
    "Zinc", "Vitamin B12", "Multivitamin"
]

# ── Pharmaceutical suffixes ─────────────────────────────────────
# International drug naming conventions use standardised endings.
# If a word ends in one of these, it is very likely a medicine.
MEDICINE_SUFFIXES = [
    "cillin", "mycin", "cycline", "floxacin", "prazole",
    "sartan", "pril", "olol", "statin", "mab", "nib",
    "zumab", "tidine", "dipine", "azole", "oxacin",
    "phylline", "fenac", "profen", "acetam", "codone",
    "setron", "lukast", "gliptin", "gliflozin", "glutide"
]

# ── Words to always ignore ──────────────────────────────────────
# Common words that appear on prescriptions but are never medicines
IGNORE_WORDS = {
    "patient", "name", "date", "doctor", "dr", "rx", "tab",
    "tablet", "tablets", "capsule", "capsules", "syrup",
    "injection", "dose", "daily", "twice", "thrice", "morning",
    "night", "evening", "after", "before", "food", "water",
    "days", "weeks", "month", "take", "oral", "apply", "use",
    "john", "smith", "kumar", "singh", "hospital", "clinic",
    "signature", "refill", "dispense", "quantity", "sig"
}


@dataclass
class ExtractedMedicine:
    name: str
    confidence: str        # "confirmed" | "probable" | "uncertain"
    match_score: float     # 0 to 100
    extraction_method: str # "seed_match" | "suffix_pattern"
    original_token: str    # Raw token from OCR text


def extract_medicines(ocr_text: str) -> List[ExtractedMedicine]:
    """
    Multi-strategy medicine extraction from raw OCR text.

    Strategy order:
    1. Fuzzy match against known medicine seed list (most reliable)
    2. Pharmaceutical suffix heuristic (catches unknown medicines)
    """
    results = []
    seen = set()

    # Tokenise — extract all words that look like they could be names
    # Must start with a letter, be at least 4 characters long
    tokens = re.findall(r'\b[A-Za-z][A-Za-z]{3,}\b', ocr_text)

    for token in tokens:
        token_lower = token.lower()

        # Skip tokens we know are not medicines
        if token_lower in IGNORE_WORDS:
            continue

        # Skip if already found this token
        if token_lower in seen:
            continue

        # ── Strategy 1: Fuzzy match against seed list ──
        match = process.extractOne(
            token,
            COMMON_MEDICINES_SEED,
            scorer=fuzz.ratio,
            score_cutoff=75
        )

        if match:
            med_name, score, _ = match
            confidence = "confirmed" if score >= 90 else "probable"
            results.append(ExtractedMedicine(
                name=med_name,
                confidence=confidence,
                match_score=float(score),
                extraction_method="seed_match",
                original_token=token
            ))
            seen.add(token_lower)
            continue

        # ── Strategy 2: Pharmaceutical suffix heuristic ──
        for suffix in MEDICINE_SUFFIXES:
            if token_lower.endswith(suffix) and len(token) > len(suffix) + 2:
                results.append(ExtractedMedicine(
                    name=token.capitalize(),
                    confidence="uncertain",
                    match_score=60.0,
                    extraction_method="suffix_pattern",
                    original_token=token
                ))
                seen.add(token_lower)
                break

    return results