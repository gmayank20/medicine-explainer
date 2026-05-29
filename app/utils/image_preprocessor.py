import cv2
import numpy as np


def preprocess_image(image_path: str) -> np.ndarray:
    """
    Enhance image quality before OCR.
    Handles poor lighting, low resolution, and uneven contrast
    which are common in prescription photos taken on phones.
    """
    img = cv2.imread(image_path)

    if img is None:
        raise ValueError(f"Could not read image at path: {image_path}")

    # Step 1: Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Step 2: Denoise
    # Reduces speckle noise without blurring text edges
    denoised = cv2.fastNlMeansDenoising(gray, h=10)

    # Step 3: Adaptive thresholding
    # Handles uneven lighting across the image (very common in phone photos)
    thresh = cv2.adaptiveThreshold(
        denoised, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11, 2
    )

    # Step 4: Upscale if image is too small
    # Tesseract accuracy improves significantly on larger images
    h, w = thresh.shape
    if w < 1000:
        scale = 1000 / w
        thresh = cv2.resize(
            thresh, None,
            fx=scale, fy=scale,
            interpolation=cv2.INTER_CUBIC
        )

    return thresh


def preprocess_for_display(image_path: str) -> np.ndarray:
    """
    Lighter version just for showing the image in the UI.
    Keeps colour, just converts BGR to RGB for display.
    """
    img = cv2.imread(image_path)

    if img is None:
        raise ValueError(f"Could not read image at path: {image_path}")

    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    return rgb