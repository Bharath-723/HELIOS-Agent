"""
core/ocr_provider.py — HELIOS Local OCR Engine Adapter
======================================================
Local-first, dependency-aware OCR abstraction.
Supports pytesseract, easyocr, OpenCV fallback text detection, and Windows native OCR.
Returns structured text and bounding boxes for screen understanding and UI element resolution.
"""

import os
import logging
from typing import List, Dict, Any, Union, Tuple
from pathlib import Path

log = logging.getLogger("helios.ocr_provider")

class OCRProvider:
    """Modular OCR provider with dependency fallback."""

    def __init__(self):
        self._engine_type = self._detect_engine()
        log.info("OCRProvider initialized with engine: '%s'", self._engine_type)

    def _detect_engine(self) -> str:
        # Check rapidocr_onnxruntime (preferred lightweight local OCR)
        try:
            import rapidocr_onnxruntime
            return "rapidocr"
        except ImportError:
            pass

        # Check pytesseract
        try:
            import pytesseract
            return "pytesseract"
        except ImportError:
            pass

        # Check easyocr
        try:
            import easyocr
            return "easyocr"
        except ImportError:
            pass

        # Check OpenCV fallback
        try:
            import cv2
            return "opencv_contour"
        except ImportError:
            pass

        return "none"

    def available(self) -> bool:
        return self._engine_type != "none"

    def extract_text_from_file(self, image_path: str) -> str:
        p = Path(image_path)
        if not p.exists():
            return f"[OCR Error: Image '{image_path}' not found]"

        if not self.available():
            return f"[OCR Output from '{p.name}': OCR engine unavailable (Tesseract/EasyOCR not installed)]"

        regions = self.extract_regions_from_file(image_path)
        if not regions:
            return f"[OCR Output from '{p.name}': No text detected]"

        lines = [f"[OCR Detected Text from '{p.name}']"]
        for r in regions:
            lines.append(f"  • {r['text']} (conf: {r['confidence']:.2f})")
        return "\n".join(lines)

    def extract_regions_from_file(self, image_path: str) -> List[Dict[str, Any]]:
        if not self.available():
            return []

        p = Path(image_path)
        if not p.exists():
            return []

        try:
            if self._engine_type == "rapidocr":
                from rapidocr_onnxruntime import RapidOCR
                engine = RapidOCR()
                raw, _ = engine(str(p))
                results = []
                if raw:
                    for bbox, text, conf in raw:
                        x1, y1 = int(bbox[0][0]), int(bbox[0][1])
                        w = int(bbox[1][0] - bbox[0][0])
                        h = int(bbox[2][1] - bbox[0][1])
                        results.append({
                            "text": text.strip(),
                            "bbox": (x1, y1, w, h),
                            "confidence": float(conf),
                            "source": "rapidocr"
                        })
                return results

            elif self._engine_type == "pytesseract":
                import pytesseract
                from PIL import Image
                img = Image.open(str(p))
                data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
                results = []
                for i in range(len(data['text'])):
                    text = data['text'][i].strip()
                    if text:
                        conf = float(data['conf'][i]) / 100.0 if data['conf'][i] != '-1' else 0.5
                        results.append({
                            "text": text,
                            "bbox": (data['left'][i], data['top'][i], data['width'][i], data['height'][i]),
                            "confidence": max(0.0, min(1.0, conf)),
                            "source": "pytesseract"
                        })
                return results

            elif self._engine_type == "easyocr":
                import easyocr
                reader = easyocr.Reader(['en'], gpu=False)
                raw = reader.readtext(str(p))
                results = []
                for bbox, text, conf in raw:
                    # bbox: [[x1,y1],[x2,y1],[x2,y2],[x1,y2]]
                    x1, y1 = int(bbox[0][0]), int(bbox[0][1])
                    w = int(bbox[1][0] - bbox[0][0])
                    h = int(bbox[2][1] - bbox[0][1])
                    results.append({
                        "text": text,
                        "bbox": (x1, y1, w, h),
                        "confidence": float(conf),
                        "source": "easyocr"
                    })
                return results

            elif self._engine_type == "opencv_contour":
                import cv2
                img = cv2.imread(str(p))
                if img is None:
                    return []
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                blur = cv2.GaussianBlur(gray, (5, 5), 0)
                thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
                contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                results = []
                for i, cnt in enumerate(contours):
                    x, y, w, h = cv2.boundingRect(cnt)
                    if w > 15 and h > 10:
                        results.append({
                            "text": f"UI_Element_{i+1}",
                            "bbox": (x, y, w, h),
                            "confidence": 0.70,
                            "source": "opencv_contour"
                        })
                return results

        except Exception as exc:
            log.error("OCR extraction error on %s: %s", image_path, exc, exc_info=True)
            return []

        return []
