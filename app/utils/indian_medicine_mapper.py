import csv
import os
import re
from typing import Optional
from rapidfuzz import process, fuzz


# Path to the downloaded Indian medicines CSV
DATA_PATH = os.path.join(
    os.path.dirname(__file__),
    "../../data/indian_medicines.csv"
)

# Global lookup dictionary — built once on first use
_MEDICINE_MAP: dict = {}
_BRAND_NAMES: list = []
_MAP_LOADED: bool = False


def _clean_name(name: str) -> str:
    """
    Strip dosage, form, and noise from a medicine name.
    'Augmentin 625 Duo Tablet' -> 'augmentin'
    'Dolo 650mg'               -> 'dolo'
    """
    name = re.sub(
        r'\b\d+(\.\d+)?\s*(mg|ml|mcg|iu|g|%|gm|kg)?\b',
        '', name, flags=re.IGNORECASE
    )
    noise = [
        'tablet', 'tablets', 'capsule', 'capsules', 'syrup',
        'injection', 'drops', 'cream', 'gel', 'ointment',
        'suspension', 'solution', 'infusion', 'strip', 'bottle',
        'duo', 'forte', 'plus', 'junior', 'sr', 'er',
        'xr', 'od', 'bid', 'mr', 'ls', 'dx', 'lx', 'cv', 'ds'
    ]
    for word in noise:
        name = re.sub(
            rf'\b{word}\b', '', name, flags=re.IGNORECASE
        )
    # Collapse multiple spaces
    name = re.sub(r'\s+', ' ', name).strip().lower()
    return name


def _clean_composition(comp1: str, comp2: str) -> str:
    """
    Combine and clean composition fields.
    'Amoxycillin (500mg)' + 'Clavulanic Acid (125mg)'
    -> 'Amoxycillin + Clavulanic Acid'
    """
    parts = []
    for c in [comp1, comp2]:
        c = c.strip()
        if c:
            c = re.sub(r'\(.*?\)', '', c).strip()
            c = re.sub(
                r'\d+(\.\d+)?\s*(mg|ml|mcg|iu|g|%)',
                '', c, flags=re.IGNORECASE
            ).strip()
            if c:
                parts.append(c)
    return ' + '.join(parts) if parts else ''


def load_medicine_map() -> None:
    """
    Load the Indian medicines CSV into memory.
    Runs once — subsequent calls return immediately.
    """
    global _MEDICINE_MAP, _BRAND_NAMES, _MAP_LOADED

    if _MAP_LOADED:
        return

    print("Loading Indian medicine database...")

    try:
        with open(DATA_PATH, encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('Is_discontinued', '').strip().upper() == 'TRUE':
                    continue

                brand_name = row.get('name', '').strip()
                comp1 = row.get('short_composition1', '').strip()
                comp2 = row.get('short_composition2', '').strip()

                if not brand_name:
                    continue

                cleaned = _clean_name(brand_name)
                generic = _clean_composition(comp1, comp2)

                # ── Key fix: skip keys shorter than 4 characters ──
                # Prevents single letters and noise becoming lookup keys
                if cleaned and generic and len(cleaned) >= 4:
                    _MEDICINE_MAP[cleaned] = {
                        'brand_name': brand_name,
                        'generic': generic,
                        'composition1': comp1,
                        'composition2': comp2,
                    }

        _BRAND_NAMES = list(_MEDICINE_MAP.keys())
        _MAP_LOADED = True
        print(f"✅ Loaded {len(_MEDICINE_MAP):,} Indian medicines")

    except FileNotFoundError:
        print(f"⚠️  Indian medicine CSV not found at {DATA_PATH}")
        _MAP_LOADED = True


def lookup_indian_medicine(query: str) -> Optional[dict]:
    """
    Look up a medicine name from a prescription.

    Three strategies in order:
    1. Exact match
    2. Fuzzy match (high threshold — avoids false positives)
    3. Partial match (long queries only)
    """
    load_medicine_map()

    if not _MEDICINE_MAP:
        return None

    cleaned_query = _clean_name(query)

    # ── Minimum length guard ──
    # Prevents short noise words from matching anything
    if not cleaned_query or len(cleaned_query) < 4:
        return None

    # Strategy 1: Exact match
    if cleaned_query in _MEDICINE_MAP:
        result = _MEDICINE_MAP[cleaned_query].copy()
        result['match_type'] = 'exact'
        result['confidence'] = 100
        return result

    # Strategy 2: Fuzzy match — high threshold
    match = process.extractOne(
        cleaned_query,
        _BRAND_NAMES,
        scorer=fuzz.ratio,
        score_cutoff=90
    )
    if match:
        matched_key, score, _ = match
        result = _MEDICINE_MAP[matched_key].copy()
        result['match_type'] = 'fuzzy'
        result['confidence'] = score
        return result

    # Strategy 3: Partial match — query must match START of brand name only
    # This prevents 'guaifenesin' matching 'stayhappi ambroxol+guaifenesin'
    if len(cleaned_query) >= 6:
        for key in _BRAND_NAMES:
            if len(key) >= 6 and key.startswith(cleaned_query):
                result = _MEDICINE_MAP[key].copy()
                result['match_type'] = 'partial'
                result['confidence'] = 70
                return result

    return None


def get_explain_name(medicine_name: str) -> str:
    """
    Main function called by the pipeline.

    Given any medicine name (brand or generic), returns
    the best name to send to the LLM for explanation.

    Priority order:
    1. Indian medicine database (brand -> generic)
    2. FDA database (international generics)
    3. Original name as fallback

    Examples:
    'Augmentin'   -> 'Amoxycillin + Clavulanic Acid'
    'Dolo 650'    -> 'Paracetamol'
    'Guaifenesin' -> 'Guaifenesin' (via FDA fallback)
    'Paracetamol' -> 'Paracetamol' (already generic)
    """
    # Priority 1: Indian database
    result = lookup_indian_medicine(medicine_name)
    if result and result.get('generic'):
        generic = result['generic']
        print(f"  Indian DB: {medicine_name} -> {generic}")
        return generic

    # Priority 2: FDA database
    from app.utils.fda_medicine_mapper import get_fda_explain_name
    fda_result = get_fda_explain_name(medicine_name)
    if fda_result:
        return fda_result

    # Priority 3: Return original — LLM handles it
    print(f"  Not in DB: {medicine_name} -> using as-is")
    return medicine_name