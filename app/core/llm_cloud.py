import os
from dataclasses import dataclass
from app.config.prompts import SYSTEM_PROMPT, SAFETY_FOOTER, build_explanation_prompt
from app.db.cache import get_cached_explanation, cache_explanation
from app.core.llm_explainer import apply_safety_filter

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
    Query HF Inference using huggingface_hub InferenceClient.
    Works inside HF Spaces without external network calls.
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
        from huggingface_hub import InferenceClient

        client = InferenceClient(
            model="mistralai/Mistral-7B-Instruct-v0.3",
            token=HF_API_TOKEN
        )

        formatted_prompt = f"<s>[INST] {SYSTEM_PROMPT}\n\n{prompt} [/INST]"

        response = client.text_generation(
            formatted_prompt,
            max_new_tokens=400,
            temperature=0.1,
            do_sample=False
        )

        explanation = response
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

    except Exception as e:
        return ExplainerResult(
            medicine_name=medicine_name,
            explanation=f"Debug error for '{medicine_name}': {str(e)}",
            was_cached=False,
            model_used="error",
            safety_footer=SAFETY_FOOTER
        )