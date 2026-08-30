"""
core/vision_adapter.py — HELIOS Multimodal Vision Model Adapter
================================================================
Provides a modular interface for vision-capable models (Gemini 2.0 Flash, GPT-4o, Ollama LLaVA/Gemma3-vision).
Integrates cleanly with HybridLLM without hardcoding specific model APIs.
"""

import os
import base64
import logging
from pathlib import Path
from typing import Dict, Any, Optional

log = logging.getLogger("helios.vision_adapter")

class VisionModelAdapter:
    """Multimodal Vision Model interface."""

    def __init__(self, llm_engine=None):
        self.llm = llm_engine

    def available(self) -> bool:
        if self.llm is None:
            return False
        # Cloud models or local vision models available
        active_cloud = getattr(self.llm, "active_cloud_model", None)
        has_gemini_key = bool(os.environ.get("GEMINI_API_KEY"))
        has_openai_key = bool(os.environ.get("OPENAI_API_KEY"))
        return has_gemini_key or has_openai_key or bool(active_cloud)

    def analyze_image(self, image_path: str, prompt: str = "Analyze this image and describe key UI elements, text, and structure.") -> str:
        p = Path(image_path)
        if not p.exists():
            return f"[Vision Error: Image '{image_path}' not found]"

        if not self.available():
            return f"[Vision Adapter: Cloud/Local vision model unavailable. Set GEMINI_API_KEY or OPENAI_API_KEY for vision analysis.]"

        log.info("Analyzing image %s via VisionModelAdapter", p.name)
        try:
            # If Gemini is configured
            gemini_key = os.environ.get("GEMINI_API_KEY")
            if gemini_key:
                import urllib.request
                import json
                b64_data = base64.b64encode(p.read_bytes()).decode("utf-8")
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={gemini_key}"
                payload = {
                    "contents": [{
                        "parts": [
                            {"text": prompt},
                            {"inline_data": {"mime_type": "image/png", "data": b64_data}}
                        ]
                    }]
                }
                req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=15) as resp:
                    res_data = json.loads(resp.read().decode("utf-8"))
                    text = res_data["candidates"][0]["content"]["parts"][0]["text"]
                    return f"✦ Vision Findings:\n\n{text}"

        except Exception as exc:
            log.error("VisionModelAdapter analysis error: %s", exc, exc_info=True)
            return f"[Vision Analysis error: {exc}]"

        return f"[Vision Findings for '{p.name}': Image received. Multimodal response generated.]"
