"""
HELIOS - Hybrid LLM Engine v4
Local: Mistral / Gemma / Llama via Ollama
Cloud: GPT-4o-mini (OpenAI) OR Gemini (Google) — your choice
Uses google-genai (new SDK) instead of deprecated google-generativeai
"""

import os
import time
import requests
from enum import Enum
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


class LLMProvider(Enum):
    LOCAL  = "local"
    GPT    = "gpt"
    GEMINI = "gemini"


@dataclass
class LLMResponse:
    content: str
    provider: LLMProvider
    model: str
    tokens_used: int = 0
    latency_ms: float = 0.0


ONLINE_TRIGGERS = [
    "latest news", "current weather", "weather in",
    "stock price", "search the web", "live score",
    "real-time", "look up online",
]


class HybridLLM:
    def __init__(self):
        self.ollama_url   = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.ollama_model = os.getenv("OLLAMA_MODEL", "mistral")
        self.mode         = os.getenv("LLM_MODE", "offline").lower()

        # OpenAI
        self.openai_key   = os.getenv("OPENAI_API_KEY", "")
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

        # Google Gemini
        self.gemini_key   = os.getenv("GEMINI_API_KEY", "")
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

        # Which cloud to use: "gemini" or "gpt"
        self.cloud_provider = os.getenv("CLOUD_PROVIDER", "gemini").lower()

    # ── Runtime control ───────────────────────────────────────────────────
    def set_model(self, model: str):
        self.ollama_model = model

    def set_mode(self, mode: str):
        self.mode = mode.lower()

    def set_cloud(self, provider: str):
        self.cloud_provider = provider.lower()

    def get_available_models(self) -> list:
        local = []
        try:
            r = requests.get(f"{self.ollama_url}/api/tags", timeout=4)
            local = list(dict.fromkeys(
                m["name"].split(":")[0] for m in r.json().get("models", [])))
        except Exception:
            pass
        cloud = []
        if self._has_gemini_key():
            cloud += ["gemini-2.0-flash", "gemini-1.5-pro"]
        if self._has_openai_key():
            cloud += ["gpt-4o-mini", "gpt-4o"]
        return local + cloud

    # ── Checks ────────────────────────────────────────────────────────────
    def _ollama_alive(self) -> bool:
        try:
            return requests.get(f"{self.ollama_url}/api/tags", timeout=3).status_code == 200
        except Exception:
            return False

    def _internet_ok(self) -> bool:
        try:
            requests.get("https://www.google.com", timeout=3)
            return True
        except Exception:
            return False

    def _has_openai_key(self) -> bool:
        k = self.openai_key
        return bool(k and k.startswith("sk-") and "your_" not in k)

    def _has_gemini_key(self) -> bool:
        k = self.gemini_key
        return bool(k and len(k) > 10 and "your_" not in k)

    def _has_any_cloud_key(self) -> bool:
        return self._has_gemini_key() or self._has_openai_key()

    def _needs_internet(self, prompt: str) -> bool:
        return any(t in prompt.lower() for t in ONLINE_TRIGGERS)

    def _use_cloud(self, prompt: str) -> bool:
        if self.mode == "offline":
            return False
        if self.mode == "online":
            return self._has_any_cloud_key()
        return (self._needs_internet(prompt)
                and self._has_any_cloud_key()
                and self._internet_ok())

    # ── Local inference (Ollama) ──────────────────────────────────────────
    def _call_local(self, prompt: str, system: str = "") -> LLMResponse:
        full = f"{system}\n\n{prompt}" if system else prompt
        t0 = time.time()
        try:
            r = requests.post(
                f"{self.ollama_url}/api/generate",
                json={"model": self.ollama_model, "prompt": full, "stream": False},
                timeout=180,
            )
            r.raise_for_status()
        except requests.exceptions.ConnectionError:
            raise RuntimeError(
                "Ollama is not running.\n"
                "Fix: Open a new terminal and run:  ollama serve"
            )
        except requests.exceptions.Timeout:
            raise RuntimeError("Ollama timed out. Model may be loading — try again.")

        data = r.json()
        return LLMResponse(
            content=data.get("response", "").strip(),
            provider=LLMProvider.LOCAL,
            model=self.ollama_model,
            tokens_used=data.get("eval_count", 0),
            latency_ms=(time.time() - t0) * 1000,
        )

    # ── Gemini inference (new google-genai SDK + REST fallback) ──────────
    def _call_gemini(self, prompt: str, system: str = "") -> LLMResponse:
        if not self._has_gemini_key():
            raise RuntimeError(
                "No Gemini API key.\n"
                "Get a free key at: https://aistudio.google.com/apikey\n"
                "Then add GEMINI_API_KEY=your_key to .env"
            )
        # Try new google-genai SDK first
        try:
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=self.gemini_key)
            t0 = time.time()
            config = types.GenerateContentConfig(
                system_instruction=system if system else None,
            )
            resp = client.models.generate_content(
                model=self.gemini_model,
                contents=prompt,
                config=config,
            )
            return LLMResponse(
                content=resp.text.strip(),
                provider=LLMProvider.GEMINI,
                model=self.gemini_model,
                latency_ms=(time.time() - t0) * 1000,
            )
        except ImportError:
            pass  # SDK not installed, try REST

        # Fallback: try old google-generativeai SDK (suppress FutureWarning)
        try:
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", FutureWarning)
                import google.generativeai as genai_old
            genai_old.configure(api_key=self.gemini_key)
            model = genai_old.GenerativeModel(
                model_name=self.gemini_model,
                system_instruction=system if system else None,
            )
            t0 = time.time()
            resp = model.generate_content(prompt)
            return LLMResponse(
                content=resp.text.strip(),
                provider=LLMProvider.GEMINI,
                model=self.gemini_model,
                latency_ms=(time.time() - t0) * 1000,
            )
        except ImportError:
            pass  # Neither SDK available, use REST

        return self._call_gemini_rest(prompt, system)

    def _call_gemini_rest(self, prompt: str, system: str = "") -> LLMResponse:
        """Call Gemini via REST API — no SDK required."""
        url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
               f"{self.gemini_model}:generateContent?key={self.gemini_key}")

        contents = []
        if system:
            contents.append({"role": "user", "parts": [{"text": system}]})
            contents.append({"role": "model", "parts": [{"text": "Understood."}]})
        contents.append({"role": "user", "parts": [{"text": prompt}]})

        t0 = time.time()
        r = requests.post(url, json={"contents": contents}, timeout=60)

        if r.status_code != 200:
            err = r.json().get("error", {})
            msg = err.get("message", r.text)
            if "API_KEY_INVALID" in msg:
                raise RuntimeError(
                    "Invalid Gemini API key.\n"
                    "Get a free key at: https://aistudio.google.com/apikey"
                )
            raise RuntimeError(f"Gemini error: {msg}")

        data = r.json()
        content = (data.get("candidates", [{}])[0]
                       .get("content", {})
                       .get("parts", [{}])[0]
                       .get("text", ""))

        return LLMResponse(
            content=content.strip(),
            provider=LLMProvider.GEMINI,
            model=self.gemini_model,
            latency_ms=(time.time() - t0) * 1000,
        )

    # ── GPT inference ─────────────────────────────────────────────────────
    def _call_gpt(self, prompt: str, system: str = "") -> LLMResponse:
        if not self._has_openai_key():
            raise RuntimeError(
                "No OpenAI API key.\n"
                "Add OPENAI_API_KEY=sk-... to .env\n"
                "Or switch to Gemini: CLOUD_PROVIDER=gemini in .env"
            )
        from openai import OpenAI
        client = OpenAI(api_key=self.openai_key)
        msgs = []
        if system:
            msgs.append({"role": "system", "content": system})
        msgs.append({"role": "user", "content": prompt})
        t0 = time.time()
        try:
            resp = client.chat.completions.create(
                model=self.openai_model, messages=msgs, max_tokens=1024)
        except Exception as e:
            err = str(e)
            if "quota" in err or "429" in err:
                raise RuntimeError(
                    "OpenAI quota exceeded.\n"
                    "Add billing at platform.openai.com\n"
                    "Or switch to Gemini (free): CLOUD_PROVIDER=gemini in .env"
                )
            raise RuntimeError(f"GPT error: {e}")
        return LLMResponse(
            content=resp.choices[0].message.content.strip(),
            provider=LLMProvider.GPT,
            model=self.openai_model,
            tokens_used=resp.usage.total_tokens,
            latency_ms=(time.time() - t0) * 1000,
        )

    # ── Cloud dispatch ────────────────────────────────────────────────────
    def _call_cloud(self, prompt: str, system: str = "") -> LLMResponse:
        if self.cloud_provider == "gemini":
            try:
                return self._call_gemini(prompt, system)
            except Exception:
                if self._has_openai_key():
                    return self._call_gpt(prompt, system)
                raise
        else:
            try:
                return self._call_gpt(prompt, system)
            except Exception:
                if self._has_gemini_key():
                    return self._call_gemini(prompt, system)
                raise

    # ── Main API ──────────────────────────────────────────────────────────
    def chat(self, prompt: str, system: str = "") -> LLMResponse:
        if self._use_cloud(prompt):
            try:
                return self._call_cloud(prompt, system)
            except Exception:
                return self._call_local(prompt, system)
        return self._call_local(prompt, system)

    def status(self) -> dict:
        return {
            "ollama_alive":     self._ollama_alive(),
            "internet":         self._internet_ok(),
            "mode":             self.mode,
            "local_model":      self.ollama_model,
            "cloud_provider":   self.cloud_provider,
            "gemini_model":     self.gemini_model,
            "openai_model":     self.openai_model,
            "has_gemini_key":   self._has_gemini_key(),
            "has_openai_key":   self._has_openai_key(),
            "available_models": self.get_available_models(),
        }
