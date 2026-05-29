import os
from dataclasses import dataclass
from app.config.prompts import SYSTEM_PROMPT, SAFETY_FOOTER, build_explanation_prompt
from app.db.cache import get_cached_explanation, cache_explanation
from app.core.llm_explainer import apply_safety_filter

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_API_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.0-flash:generateContent"
)


@dataclass
class ExplainerResult:
    medicine_name: str
    explanation: str
    was_cached: bool
    model_used: str
    safety_footer: str


def explain_medicine_cloud(medicine_name: str, confidence: str) -> ExplainerResult:
    """
    Query Google Gemini API for medicine explanations.
    Used when deployed on Hugging Face Spaces.
    Free tier — no billing required.
    """
    # Check cache first — reduces API calls
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
    full_prompt = f"{SYSTEM_PROMPT}\n\n{prompt}"

    try:
        import requests

        url = f"{GEMINI_API_URL}?key={GEMINI_API_KEY}"

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": full_prompt}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 400,
            }
        }

        response = requests.post(url, json=payload, timeout=30)

        if response.status_code == 200:
            data = response.json()
            explanation = (
                data["candidates"][0]["content"]["parts"][0]["text"]
            )
            explanation = apply_safety_filter(explanation)

            cache_explanation(
                medicine_name, explanation, "gemini-2.0-flash"
            )

            return ExplainerResult(
                medicine_name=medicine_name,
                explanation=explanation,
                was_cached=False,
                model_used="gemini-2.0-flash",
                safety_footer=SAFETY_FOOTER
            )

        return ExplainerResult(
            medicine_name=medicine_name,
            explanation=f"Debug error: HTTP {response.status_code} — {response.text[:200]}",
            was_cached=False,
            model_used="error",
            safety_footer=SAFETY_FOOTER
        )

    except Exception as e:
        return ExplainerResult(
            medicine_name=medicine_name,
            explanation=f"Debug error for '{medicine_name}': {str(e)}",
            was_cached=False,
            model_used="error",
            safety_footer=SAFETY_FOOTER
        )