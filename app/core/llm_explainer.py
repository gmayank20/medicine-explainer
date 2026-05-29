import re
import ollama
from dataclasses import dataclass
from app.config.prompts import SYSTEM_PROMPT, SAFETY_FOOTER, build_explanation_prompt
from app.config.settings import Settings
from app.db.cache import get_cached_explanation, cache_explanation


@dataclass
class ExplainerResult:
    medicine_name: str
    explanation: str
    was_cached: bool
    model_used: str
    safety_footer: str


def apply_safety_filter(text: str) -> str:
    """
    Post-generation pass. Catches dangerous patterns even if prompt fails.
    """
    replacements = [
        (r"you should take",        "it is commonly taken"),
        (r"stop taking",            "speak to your doctor about"),
        (r"you have ",              "this medicine is used in cases of "),
        (r"your condition",         "the condition being treated"),
        (r"will cure",              "may help manage"),
        (r"will treat",             "is commonly used for"),
        (r"you (are|were) diagnosed", "people diagnosed"),
    ]
    result = text
    for pattern, replacement in replacements:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    return result


def explain_medicine(medicine_name: str, confidence: str) -> ExplainerResult:
    """
    Query Ollama with a safety-wrapped prompt.
    Checks SQLite cache first to avoid redundant LLM calls.
    """
    # Cache check first
    cached = get_cached_explanation(medicine_name)
    if cached:
        return ExplainerResult(
            medicine_name=medicine_name,
            explanation=cached,
            was_cached=True,
            model_used="cache",
            safety_footer=SAFETY_FOOTER
        )

    prompt = build_explanation_prompt(medicine_name, confidence)

    try:
        response = ollama.chat(
            model=Settings.OLLAMA_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": prompt}
            ],
            options={
                "temperature": 0.1,   # Low = consistent, less hallucination
                "num_predict": 400,   # Cap response length
            }
        )

        explanation = response["message"]["content"]
        explanation = apply_safety_filter(explanation)

        # Store in cache for next time
        cache_explanation(medicine_name, explanation, Settings.OLLAMA_MODEL)

        return ExplainerResult(
            medicine_name=medicine_name,
            explanation=explanation,
            was_cached=False,
            model_used=Settings.OLLAMA_MODEL,
            safety_footer=SAFETY_FOOTER
        )

    except Exception as e:
        return ExplainerResult(
            medicine_name=medicine_name,
            explanation=(
                f"Unable to retrieve information for '{medicine_name}'. "
                f"Please consult your pharmacist directly."
            ),
            was_cached=False,
            model_used="error",
            safety_footer=SAFETY_FOOTER
        )
