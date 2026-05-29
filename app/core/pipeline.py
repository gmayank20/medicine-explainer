from dataclasses import dataclass
from typing import Optional, List

from app.core.ocr_engine import OCRResult, extract_text_with_confidence
from app.core.medicine_extractor import ExtractedMedicine, extract_medicines
import os
from app.core.llm_explainer import ExplainerResult, explain_medicine

# Auto-detect environment — use cloud LLM if HF token present
_USE_CLOUD = bool(os.getenv("HF_API_TOKEN", ""))
if _USE_CLOUD:
    from app.core.llm_cloud import explain_medicine_cloud as explain_medicine
from app.db.cache import log_query


@dataclass
class MedicineResult:
    extracted_medicine: ExtractedMedicine
    explanation: ExplainerResult


@dataclass
class PipelineResult:
    ocr_result: Optional[OCRResult]
    medicines: List[MedicineResult]
    input_type: str            # "image" | "text"
    error: Optional[str] = None


def run_pipeline(
    image_path: str = None,
    typed_name: str = None
) -> PipelineResult:
    """
    Master orchestrator. Two entry points:
    - image_path → OCR → extract → explain
    - typed_name → skip OCR → explain directly
    """

    # ── Path 1: User typed a medicine name directly ──
    if typed_name:
        typed_name = typed_name.strip()

        if not typed_name:
            return PipelineResult(
                ocr_result=None,
                medicines=[],
                input_type="text",
                error="Please enter a medicine name."
            )

        from app.utils.indian_medicine_mapper import get_explain_name
        explain_name = get_explain_name(typed_name)

        med = ExtractedMedicine(
            name=typed_name.title(),
            confidence="probable",
            match_score=100.0,
            extraction_method="user_input",
            original_token=typed_name
        )

        explanation = explain_medicine(explain_name, med.confidence)

        explanation = explain_medicine(med.name, med.confidence)

        log_query(
            input_type="text",
            ocr_confidence=1.0,
            medicines_found=1
        )

        return PipelineResult(
            ocr_result=None,
            medicines=[MedicineResult(
                extracted_medicine=med,
                explanation=explanation
            )],
            input_type="text"
        )

    # ── Path 2: User uploaded an image ──
    if image_path:

        # Stage 1: OCR
        ocr_result = extract_text_with_confidence(image_path)

        if not ocr_result.raw_text.strip():
            log_query("image", 0.0, 0)
            return PipelineResult(
                ocr_result=ocr_result,
                medicines=[],
                input_type="image",
                error="No text could be extracted from this image. "
                      "Please try a clearer photo."
            )

        # Stage 2: Extract medicine names
        medicines = extract_medicines(ocr_result.raw_text)

        if not medicines:
            log_query("image", ocr_result.confidence, 0)
            return PipelineResult(
                ocr_result=ocr_result,
                medicines=[],
                input_type="image",
                error="No medicine names could be identified. "
                      "Please type the medicine name manually."
            )

    # Stage 3: Explain each medicine (cap at 5)
        from app.utils.indian_medicine_mapper import get_explain_name
        results = []
        for med in medicines[:5]:
            explain_name = get_explain_name(med.name)
            explanation = explain_medicine(explain_name, med.confidence)
            results.append(MedicineResult(
                extracted_medicine=med,
                explanation=explanation
            ))

        log_query("image", ocr_result.confidence, len(results))

        return PipelineResult(
            ocr_result=ocr_result,
            medicines=results,
            input_type="image"
        )

    # ── No input provided ──
    return PipelineResult(
        ocr_result=None,
        medicines=[],
        input_type="unknown",
        error="No input provided."
    )