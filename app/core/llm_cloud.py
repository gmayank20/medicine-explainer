import os
import requests
from dataclasses import dataclass
from app.config.prompts import SYSTEM_PROMPT, SAFETY_FOOTER, build_explanation_prompt
from app.db.cache import get_cached_explanation, cache_explanation
from app.core.llm_explainer import apply_safety_filter

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"


@dataclass
class ExplainerResult:
    medicine_name: str
    explanation: str
    was_cached: bool
    model_used: str
    safety_footer: str


def explain_medicine_cloud(medicine_name: str, confidence: str) -> ExplainerResult:
    """
    Query Groq API for medicine explanations.
    Free tier — fast, reliable, no billing required.
    Model: llama3-8b-8192
    """
    # Check cache first
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
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "llama3-8b-8192",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": prompt}
            ],
            "max_tokens": 400,
            "temperature": 0.1
        }

        response = requests.post(
            GROQ_API_URL,
            headers=headers,
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            explanation = data["choices"][0]["message"]["content"]
            explanation = apply_safety_filter(explanation)

            cache_explanation(
                medicine_name, explanation, "groq-llama3-8b"
            )

            return ExplainerResult(
                medicine_name=medicine_name,
                explanation=explanation,
                was_cached=False,
                model_used="groq-llama3-8b",
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