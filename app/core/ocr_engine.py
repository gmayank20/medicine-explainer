import pytesseract
from PIL import Image
from dataclasses import dataclass
from app.config.settings import Settings
from app.utils.image_preprocessor import preprocess_image


@dataclass
class OCRResult:
    raw_text: str
    confidence: float         # 0.0 to 1.0
    confidence_label: str     # "high" | "medium" | "low"
    word_confidences: list
    is_reliable: bool


def extract_text_with_confidence(image_path: str) -> OCRResult:
    """
    Run Tesseract and return extracted text with confidence scores.
    Confidence scoring drives honest uncertainty reporting in the UI.
    """
    try:
        processed = preprocess_image(image_path)
        pil_image = Image.fromarray(processed)

        # Get detailed data including per-word confidence scores
        data = pytesseract.image_to_data(
            pil_image,
            output_type=pytesseract.Output.DICT,
            config=Settings.TESSERACT_CONFIG
        )

        # Filter out empty detections and noise
        # -1 means Tesseract had no confidence value for that word
        word_confidences = [
            int(conf)
            for conf, text in zip(data["conf"], data["text"])
            if str(text).strip() and str(conf) != "-1"
        ]

        raw_text = pytesseract.image_to_string(
            pil_image,
            config=Settings.TESSERACT_CONFIG
        ).strip()

        if not word_confidences or not raw_text:
            return OCRResult(
                raw_text="",
                confidence=0.0,
                confidence_label="low",
                word_confidences=[],
                is_reliable=False
            )

        avg_confidence = sum(word_confidences) / len(word_confidences) / 100.0

        # Classify into tiers
        if avg_confidence >= Settings.OCR_CONFIDENCE_HIGH:
            label = "high"
            reliable = True
        elif avg_confidence >= Settings.OCR_CONFIDENCE_MEDIUM:
            label = "medium"
            reliable = True
        else:
            label = "low"
            reliable = False

        return OCRResult(
            raw_text=raw_text,
            confidence=avg_confidence,
            confidence_label=label,
            word_confidences=word_confidences,
            is_reliable=reliable
        )

    except Exception as e:
        return OCRResult(
            raw_text="",
            confidence=0.0,
            confidence_label="low",
            word_confidences=[],
            is_reliable=False
        )