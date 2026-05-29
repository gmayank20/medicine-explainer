import json
import os
import re
from typing import Optional
from rapidfuzz import process, fuzz


# Path to the FDA JSON file
DATA_PATH = os.path.join(
    os.path.dirname(__file__),
    "../../data/drug-ndc-0001-of-0001.json"
)

# Global lookup dictionaries
_GENERIC_MAP: dict = {}    # generic name → details
_BRAND_MAP: dict = {}      # brand name → details
_GENERIC_NAMES: list = []
_BRAND_NAMES: list = []
_MAP_LOADED: bool = False


def _clean_name(name: str) -> str:
    """
    Normalise a drug name for consistent lookup.
    'Mucus Relief Maximum Strength' → 'mucus relief'
    'GUAIFENESIN'                   → 'guaifenesin'
    """
    name = name.lower().strip()
    # Remove strength/dosage
    name = re.sub(
        r'\b\d+(\.\d+)?\s*(mg|ml|mcg|iu|g|%|gm)?\b',
        '', name, flags=re.IGNORECASE
    )
    # Remove common suffixes
    noise = [
        'maximum strength', 'extra strength', 'extended release',
        'tablet', 'capsule', 'syrup', 'solution', 'injection',
        'oral', 'topical', 'cream', 'gel', 'drops', 'sr', 'er',
        'xr', 'od', 'plus', 'forte'
    ]
    for word in noise:
        name = re.sub(rf'\b{word}\b', '', name, flags=re.IGNORECASE)
    return name.strip()


def _format_ingredients(active_ingredients: list) -> str:
    """
    Extract just the ingredient names without strengths.
    [{'name': 'GUAIFENESIN', 'strength': '1200 mg/1'}]
    → 'Guaifenesin'
    """
    if not active_ingredients:
        return ''
    names = [
        i.get('name', '').strip().title()
        for i in active_ingredients
        if i.get('name')
    ]
    return ' + '.join(names)


def load_fda_map() -> None:
    """
    Load the FDA drug database into memory.
    Runs once — subsequent calls return immediately.
    """
    global _GENERIC_MAP, _BRAND_MAP
    global _GENERIC_NAMES, _BRAND_NAMES, _MAP_LOADED

    if _MAP_LOADED:
        return

    print("Loading FDA medicine database...")

    try:
        with open(DATA_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)

        results = data.get('results', [])

        for record in results:
            # Skip non-human or unfinished records
            if not record.get('finished', False):
                continue
            if 'HUMAN' not in record.get('product_type', '').upper():
                continue

            generic = record.get('generic_name', '').strip()
            brand = record.get('brand_name', '').strip()
            ingredients = _format_ingredients(
                record.get('active_ingredients', [])
            )
            dosage_form = record.get('dosage_form', '').strip()
            route = record.get('route', [])

            entry = {
                'generic_name': generic,
                'brand_name': brand,
                'ingredients': ingredients,
                'dosage_form': dosage_form,
                'route': route[0] if route else '',
                'source': 'FDA'
            }

            # Index by generic name
            if generic:
                cleaned_generic = _clean_name(generic)
                if cleaned_generic:
                    _GENERIC_MAP[cleaned_generic] = entry

            # Index by brand name
            if brand:
                cleaned_brand = _clean_name(brand)
                if cleaned_brand:
                    _BRAND_MAP[cleaned_brand] = entry

        _GENERIC_NAMES = list(_GENERIC_MAP.keys())
        _BRAND_NAMES = list(_BRAND_MAP.keys())
        _MAP_LOADED = True

        print(
            f"✅ Loaded {len(_GENERIC_MAP):,} FDA generics "
            f"and {len(_BRAND_MAP):,} FDA brands"
        )

    except FileNotFoundError:
        print(f"⚠️  FDA JSON not found at {DATA_PATH}")
        _MAP_LOADED = True


def lookup_fda_medicine(query: str) -> Optional[dict]:
    """
    Look up a medicine in the FDA database.
    Tries generic names first, then brand names.
    Uses fuzzy matching to handle OCR errors.
    """
    load_fda_map()

    if not _GENERIC_MAP:
        return None

    cleaned = _clean_name(query)
    if not cleaned or len(cleaned) < 3:
        return None

    # Strategy 1: Exact generic match
    if cleaned in _GENERIC_MAP:
        result = _GENERIC_MAP[cleaned].copy()
        result['match_type'] = 'exact_generic'
        result['confidence'] = 100
        return result

    # Strategy 2: Exact brand match
    if cleaned in _BRAND_MAP:
        result = _BRAND_MAP[cleaned].copy()
        result['match_type'] = 'exact_brand'
        result['confidence'] = 100
        return result

    # Strategy 3: Fuzzy generic match
    match = process.extractOne(
        cleaned,
        _GENERIC_NAMES,
        scorer=fuzz.ratio,
        score_cutoff=85
    )
    if match:
        key, score, _ = match
        result = _GENERIC_MAP[key].copy()
        result['match_type'] = 'fuzzy_generic'
        result['confidence'] = score
        return result

    # Strategy 4: Fuzzy brand match
    match = process.extractOne(
        cleaned,
        _BRAND_NAMES,
        scorer=fuzz.ratio,
        score_cutoff=85
    )
    if match:
        key, score, _ = match
        result = _BRAND_MAP[key].copy()
        result['match_type'] = 'fuzzy_brand'
        result['confidence'] = score
        return result

    return None


def get_fda_explain_name(medicine_name: str) -> Optional[str]:
    """
    Returns the best generic name for a medicine from FDA data.
    Returns None if not found — caller falls back to original name.
    """
    result = lookup_fda_medicine(medicine_name)

    if result:
        # Prefer ingredients list over generic name
        # because ingredients are cleaner for LLM explanation
        explain = result.get('ingredients') or result.get('generic_name')
        if explain:
            print(f"  FDA mapped: {medicine_name} → {explain}")
            return explain

    return None