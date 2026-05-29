import os
import requests
from dataclasses import dataclass
from app.config.prompts import SYSTEM_PROMPT, SAFETY_FOOTER, build_explanation_prompt
from app.db.cache import get_cached_explanation, cache_explanation
from app.core.llm_explainer import apply_safety_filter

# Hugging Face Inference API
HF_API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.3"
HF_API_TOKEN = os.getenv("HF_API_TOKEN", "")


@dataclass
class ExplainerResult:
    medicine_name: str
    explanation: str
    was_cached: bool
    model_used: str
    safety_footer: str


def explain_medicine_cloud(medicine_name: str, confidence: str) -> ExplainerResult:
    """
    Query Hugging Face Inference API instead of local Ollama.
    Used when deployed on Hugging Face Spaces.
    Falls back gracefully if API is unavailable.
    """
    # Check cache first — reduces API calls significantly
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

    # Format for Mistral instruct format
    formatted_prompt = f"<s>[INST] {SYSTEM_PROMPT}\n\n{prompt} [/INST]"

    headers = {
        "Authorization": f"Bearer {HF_API_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "inputs": formatted_prompt,
        "parameters": {
            "max_new_tokens": 400,
            "temperature": 0.1,
            "do_sample": False,
            "return_full_text": False
        }
    }

    try:
        response = requests.post(
            HF_API_URL,
            headers=headers,
            json=payload,
            timeout=60
        )

        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and result:
                explanation = result[0].get('generated_text', '')
                explanation = apply_safety_filter(explanation)
                cache_explanation(
                    medicine_name, explanation,
                    "mistral-7b-instruct-hf"
                )
                return ExplainerResult(
                    medicine_name=medicine_name,
                    explanation=explanation,
                    was_cached=False,
                    model_used="mistral-7b-instruct-hf",
                    safety_footer=SAFETY_FOOTER
                )

        return ExplainerResult(
            medicine_name=medicine_name,
            explanation=(
                "The explanation service is temporarily unavailable. "
                "Please try again in a moment or consult your pharmacist."
            ),
            was_cached=False,
            model_used="error",
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