"""
HELIOS - Hybrid LLM Engine v4
Local: Mistral / Gemma / Llama via Ollama
Cloud: GPT-4o-mini (OpenAI) OR Gemini (Google) — your choice
Uses google-genai (new SDK) instead of deprecated google-generativeai
"""

import os
import time
import logging
import requests
from enum import Enum
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

log = logging.getLogger("helios.llm")


class LLMProvider(Enum):
    LOCAL  = "local"
    GPT    = "gpt"
    GEMINI = "gemini"
    GROQ   = "groq"


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


from core.system import environment_manager


class HybridLLM:
    def __init__(self):
        self.ollama_url   = environment_manager.get("OLLAMA_BASE_URL", "http://localhost:11434")
        self.ollama_model = environment_manager.get("OLLAMA_MODEL", "gemma3")
        self.mode         = environment_manager.get("LLM_MODE", "offline").lower()

        # OpenAI
        self.openai_key   = environment_manager.get("OPENAI_API_KEY", "")
        self.openai_model = environment_manager.get("OPENAI_MODEL", "gpt-4o-mini")

        # Google Gemini
        self.gemini_key   = environment_manager.get("GEMINI_API_KEY", "")
        self.gemini_model = environment_manager.get("GEMINI_MODEL", "gemini-3.6-flash")

        # Groq Cloud
        self.groq_key     = environment_manager.get("GROQ_API_KEY", "")
        self.groq_model   = environment_manager.get("GROQ_MODEL", "groq/compound-mini")

        # Which cloud to use: "gemini", "groq", or "gpt"
        self.cloud_provider = environment_manager.get("CLOUD_PROVIDER", "gemini").lower()

    # ── Runtime control ───────────────────────────────────────────────────
    def set_model(self, model: str):
        m = model.lower()
        if m.startswith("gemini"):
            self.gemini_model = model
            self.cloud_provider = "gemini"
            self.active_cloud_model = model
        elif m.startswith("groq"):
            self.groq_model = model
            self.cloud_provider = "groq"
            self.active_cloud_model = model
        elif m.startswith("gpt"):
            self.openai_model = model
            self.cloud_provider = "gpt"
            self.active_cloud_model = model
        else:
            self.ollama_model = model
            self.active_cloud_model = None

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
        if self._has_gemini_key() and self._test_gemini_working():
            cloud += ["gemini-3.6-flash"]
        if self._has_groq_key() and self._test_groq_working():
            cloud += ["groq/compound-mini"]
        if self._has_openai_key() and self._test_openai_working():
            cloud += ["gpt-4o-mini"]
        return local + cloud

    def _test_gemini_working(self) -> bool:
        if not self._has_gemini_key():
            return False
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={self.gemini_key}"
            r = requests.post(url, json={"contents": [{"role": "user", "parts": [{"text": "ping"}]}]}, timeout=4)
            return r.status_code == 200
        except Exception:
            return False

    def _test_groq_working(self) -> bool:
        if not self._has_groq_key():
            return False
        try:
            r = requests.get("https://api.groq.com/openai/v1/models",
                             headers={"Authorization": f"Bearer {self.groq_key}"}, timeout=4)
            return r.status_code == 200
        except Exception:
            return False

    def _test_openai_working(self) -> bool:
        if not self._has_openai_key():
            return False
        try:
            r = requests.get("https://api.openai.com/v1/models",
                             headers={"Authorization": f"Bearer {self.openai_key}"}, timeout=4)
            return r.status_code == 200
        except Exception:
            return False

    def _has_groq_key(self) -> bool:
        k = self.groq_key
        return bool(k and k.startswith("gsk_") and len(k) > 15)

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
        if getattr(self, "active_cloud_model", None):
            return self._has_any_cloud_key()
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
        
        payload = {"model": self.ollama_model, "prompt": full, "stream": False}
        max_attempts = 2
        
        for attempt in range(1, max_attempts + 1):
            try:
                r = requests.post(
                    f"{self.ollama_url}/api/generate",
                    json=payload,
                    timeout=180,
                )
                r.raise_for_status()
                data = r.json()
                return LLMResponse(
                    content=data.get("response", "").strip(),
                    provider=LLMProvider.LOCAL,
                    model=self.ollama_model,
                    tokens_used=data.get("eval_count", 0),
                    latency_ms=(time.time() - t0) * 1000,
                )
            except (requests.exceptions.ConnectionError, ConnectionResetError) as exc:
                log.warning("[Attempt %d/%d] Ollama connection error: %s", attempt, max_attempts, exc)
                if attempt < max_attempts:
                    time.sleep(1.0)
                    continue
                raise RuntimeError(
                    f"Ollama is not running or connection refused.\n"
                    f"Details: {exc}\n"
                    f"Fix: Open a new terminal and run:  ollama serve"
                )
            except (requests.exceptions.Timeout, requests.exceptions.ReadTimeout) as exc:
                log.warning("[Attempt %d/%d] Ollama timeout error: %s", attempt, max_attempts, exc)
                if attempt < max_attempts:
                    time.sleep(1.0)
                    continue
                raise RuntimeError(
                    f"Ollama local model request timed out (attempt {attempt}).\n"
                    f"Details: {exc}"
                )
            except requests.exceptions.HTTPError as exc:
                status_code = exc.response.status_code if exc.response is not None else 500
                response_text = exc.response.text if exc.response is not None else str(exc)
                log.warning("[Attempt %d/%d] Ollama HTTP error %d: %s", attempt, max_attempts, status_code, response_text)
                
                # Retry only on 5xx errors (500, 502, 503, 504)
                if status_code in (500, 502, 503, 504):
                    if attempt < max_attempts:
                        time.sleep(1.0)
                        continue
                
                raise RuntimeError(
                    f"Ollama request failed (HTTP {status_code}).\n"
                    f"Response: {response_text.strip()}"
                )
            except Exception as exc:
                log.error("[Attempt %d/%d] Unexpected Ollama error: %s", attempt, max_attempts, exc, exc_info=True)
                raise RuntimeError(f"Ollama unexpected error: {exc}")

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
            pass  # google-genai SDK not installed, fallback to REST

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

    # ── Groq inference ───────────────────────────────────────────────────
    def _call_groq(self, prompt: str, system: str = "") -> LLMResponse:
        if not self._has_groq_key():
            raise RuntimeError("No Groq API key configured.")
        t0 = time.time()
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.groq_key}", "Content-Type": "application/json"}
        msgs = []
        if system:
            msgs.append({"role": "system", "content": system})
        msgs.append({"role": "user", "content": prompt})

        payload = {"model": self.groq_model, "messages": msgs}
        r = requests.post(url, headers=headers, json=payload, timeout=30)
        if r.status_code != 200:
            raise RuntimeError(f"Groq API error ({r.status_code}): {r.text}")
        data = r.json()
        content = data["choices"][0]["message"]["content"]
        return LLMResponse(
            content=content.strip(),
            provider=LLMProvider.GROQ,
            model=self.groq_model,
            tokens_used=data.get("usage", {}).get("total_tokens", 0),
            latency_ms=(time.time() - t0) * 1000,
        )

    # ── Cloud dispatch ────────────────────────────────────────────────────
    def _call_cloud(self, prompt: str, system: str = "") -> LLMResponse:
        if self.cloud_provider == "groq":
            try:
                return self._call_groq(prompt, system)
            except Exception:
                if self._has_gemini_key():
                    return self._call_gemini(prompt, system)
                raise
        elif self.cloud_provider == "gemini":
            try:
                return self._call_gemini(prompt, system)
            except Exception:
                if self._has_groq_key():
                    return self._call_groq(prompt, system)
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

    def generate(self, prompt: str, system: str = "") -> str:
        """Alias returning raw content string for agent controllers."""
        res = self.chat(prompt, system=system)
        return res.content

    def query(self, prompt: str, system: str = "") -> str:
        """Alias returning raw content string for agent controllers."""
        res = self.chat(prompt, system=system)
        return res.content

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
