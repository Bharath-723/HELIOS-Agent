"""
ui/models_panel.py — HELIOS Model Management Panel
===================================================
Displays available models as interactive cards.
"""

from __future__ import annotations
import tkinter as tk
from .theme import C, F, S, ThemeManager
from .icon_manager import I

_MODEL_CATALOG: list[dict] = [
    {
        "id": "gemma3",
        "name": "Gemma 3",
        "provider": "Google",
        "type": "local",
        "description": "Efficient open model. Strong at reasoning and coding.",
        "context": "8K",
        "speed": "Fast",
        "reasoning": "★★★★☆",
        "privacy": "★★★★★",
        "capabilities": ["Reasoning", "Code", "QA", "Summarize"],
    },
    {
        "id": "llama3",
        "name": "Llama 3",
        "provider": "Meta",
        "type": "local",
        "description": "Open-weight model with strong instruction following.",
        "context": "8K",
        "speed": "Fast",
        "reasoning": "★★★★☆",
        "privacy": "★★★★★",
        "capabilities": ["Reasoning", "Code", "Chat"],
    },
    {
        "id": "mistral",
        "name": "Mistral 7B",
        "provider": "Mistral AI",
        "type": "local",
        "description": "Compact but powerful. Great for on-device inference.",
        "context": "8K",
        "speed": "Very Fast",
        "reasoning": "★★★☆☆",
        "privacy": "★★★★★",
        "capabilities": ["Chat", "Summarize", "Translation"],
    },
    {
        "id": "gemini-3.6-flash",
        "name": "Gemini 3.6 Flash",
        "provider": "Google Cloud",
        "type": "cloud",
        "description": "Fastest Gemini model. Multimodal. Requires API key.",
        "context": "1M",
        "speed": "Ultra Fast",
        "reasoning": "★★★★★",
        "privacy": "★★☆☆☆",
        "capabilities": ["Vision", "Code", "Reasoning", "Multimodal"],
    },
    {
        "id": "gpt-4o",
        "name": "GPT-4o",
        "provider": "OpenAI",
        "type": "cloud",
        "description": "State-of-the-art model. Multimodal. Requires API key.",
        "context": "128K",
        "speed": "Fast",
        "reasoning": "★★★★★",
        "privacy": "★★☆☆☆",
        "capabilities": ["Vision", "Code", "Reasoning", "Multimodal"],
    },
]


class ModelsPanel:
    """Interactive model card gallery separated into collapsible Local and Cloud sections."""

    def __init__(self, parent: tk.Widget, on_select: callable) -> None:
        self._parent       = parent
        self._on_select    = on_select
        self._active_id    = "gemma3"
        self._cards:       dict[str, tk.Frame] = {}
        
        self._local_expanded = True
        self._cloud_expanded = True

        self.frame = tk.Frame(parent, bg=C.BG_S)
        self._build()

        ThemeManager.add_listener(self._on_theme_changed)

    def _build(self) -> None:
        # Header
        self.hdr = tk.Frame(self.frame, bg=C.GLASS_2, height=52)
        self.hdr.pack(fill="x")
        self.hdr.pack_propagate(False)

        self.lbl_title = tk.Label(self.hdr,
                                   text=f"  {I.MODELS}  Model Management",
                                   font=(F._PRIMARY, F.LG, "bold"),
                                   bg=C.GLASS_2, fg=C.FG_1)
        self.lbl_title.pack(side="left", pady=14)

        # Scrollable canvas setup
        self.cv  = tk.Canvas(self.frame, bg=C.BG_S, highlightthickness=0)
        self.vsb = tk.Scrollbar(self.frame, orient="vertical", command=self.cv.yview)
        self.cv.configure(yscrollcommand=self.vsb.set)
        self.cv.pack(side="left", fill="both", expand=True)
        self.vsb.pack(side="right", fill="y")

        self.inner = tk.Frame(self.cv, bg=C.BG_S)
        self.wid = self.cv.create_window((0, 0), window=self.inner, anchor="nw")
        self.inner.bind("<Configure>", lambda e: self._update_scroll_region())
        self.cv.bind("<Configure>", lambda e: self.cv.itemconfig(self.wid, width=e.width))

        self.lbl_legend = tk.Label(self.inner,
                                   text="  Select the active AI model. Local models run on-device; cloud models require API credentials.",
                                   font=(F._FALLBACK, F.XS),
                                   bg=C.BG_S, fg=C.FG_3, pady=8)
        self.lbl_legend.pack(fill="x")

        self.sep = tk.Frame(self.inner, bg=C.GLASS_BD_2, height=1)
        self.sep.pack(fill="x", padx=8, pady=(0, 8))

        self._render_sections()

    def _bind_mousewheel(self, widget: tk.Widget) -> None:
        def _on_wheel(e):
            self.cv.yview_scroll(int(-1 * (e.delta / 120)), "units")
        widget.bind("<MouseWheel>", _on_wheel)
        for child in widget.winfo_children():
            self._bind_mousewheel(child)

    def _update_scroll_region(self) -> None:
        self.cv.configure(scrollregion=self.cv.bbox("all"))
        self._bind_mousewheel(self.inner)

    def _render_sections(self) -> None:
        for w in list(self.inner.winfo_children()):
            if w not in (self.lbl_legend, self.sep):
                w.destroy()

        from core.system import environment_manager, dependency_checker
        import requests

        # Query installed Ollama models
        installed_ollama = set()
        try:
            r = requests.get("http://localhost:11434/api/tags", timeout=2)
            if r.status_code == 200:
                installed_ollama = {item["name"].split(":")[0].lower() for item in r.json().get("models", [])}
        except Exception:
            pass

        # Check cloud API keys
        gemini_key = environment_manager.get("GEMINI_API_KEY", "")
        has_gemini = bool(gemini_key and len(gemini_key) > 10 and not gemini_key.startswith("your_"))
        
        openai_key = environment_manager.get("OPENAI_API_KEY", "")
        has_openai = bool(openai_key and openai_key.startswith("sk-") and not openai_key.startswith("your_"))

        local_catalog = [m for m in _MODEL_CATALOG if m["type"] == "local"]
        cloud_catalog = [m for m in _MODEL_CATALOG if m["type"] == "cloud"]

        # ── 1. LOCAL MODELS SECTION ─────────────────────────────────────────
        self._render_accordion_header(
            self.inner,
            title="🖥  Local Models (On-Device Inference)",
            count=len(local_catalog),
            is_expanded=self._local_expanded,
            on_toggle=self._toggle_local
        )

        if self._local_expanded:
            local_container = tk.Frame(self.inner, bg=C.BG_S)
            local_container.pack(fill="x", padx=8, pady=(4, 12))
            
            any_local_available = False
            for m in local_catalog:
                is_avail = (m["id"].lower() in installed_ollama) or ("gemma3" in installed_ollama and m["id"] == "gemma3")
                if is_avail:
                    any_local_available = True
                self._model_card(local_container, m, is_available=is_avail, is_cloud=False)

            if not any_local_available and not installed_ollama:
                self._empty_notice(
                    local_container,
                    f"{I.ERR_ICON}  No local models installed in Ollama.\nRun: ollama pull gemma3 to download an on-device model."
                )

        # ── 2. CLOUD MODELS SECTION ─────────────────────────────────────────
        self._render_accordion_header(
            self.inner,
            title="☁  Cloud Models (API Key Powered)",
            count=len(cloud_catalog),
            is_expanded=self._cloud_expanded,
            on_toggle=self._toggle_cloud
        )

        if self._cloud_expanded:
            cloud_container = tk.Frame(self.inner, bg=C.BG_S)
            cloud_container.pack(fill="x", padx=8, pady=(4, 12))
            
            for m in cloud_catalog:
                if m["id"].startswith("gemini"):
                    is_avail = has_gemini
                elif m["id"].startswith("gpt"):
                    is_avail = has_openai
                else:
                    is_avail = False
                self._model_card(cloud_container, m, is_available=is_avail, is_cloud=True)

            if not (has_gemini or has_openai):
                self._empty_notice(
                    cloud_container,
                    f"{I.ERR_ICON}  No cloud API key connected.\nAdd your Gemini or OpenAI API key in .env or Settings."
                )

        self.root = self.frame.winfo_toplevel()
        self.frame.after(50, self._update_scroll_region)

    def _toggle_local(self) -> None:
        self._local_expanded = not self._local_expanded
        self._render_sections()

    def _toggle_cloud(self) -> None:
        self._cloud_expanded = not self._cloud_expanded
        self._render_sections()

    def _render_accordion_header(self, parent: tk.Widget, title: str, count: int,
                                 is_expanded: bool, on_toggle: callable) -> None:
        hdr_frame = tk.Frame(parent, bg=C.GLASS_3,
                             highlightthickness=1,
                             highlightbackground=C.GLASS_BD_3,
                             cursor="hand2")
        hdr_frame.pack(fill="x", padx=8, pady=4)

        arrow = I.CHEVRON_D if is_expanded else I.CHEVRON_R
        lbl_a = tk.Label(hdr_frame, text=f" {arrow} ",
                          font=(F._FALLBACK, F.SM, "bold"),
                          bg=C.GLASS_3, fg=C.BLUE)
        lbl_a.pack(side="left", pady=8)

        lbl_t = tk.Label(hdr_frame, text=title,
                          font=(F._PRIMARY, F.MD, "bold"),
                          bg=C.GLASS_3, fg=C.FG_1)
        lbl_t.pack(side="left", padx=4)

        lbl_c = tk.Label(hdr_frame,
                          text=f"{count} models",
                          font=(F._FALLBACK, F.XS),
                          bg=C.CHIP_BG, fg=C.CHIP_FG,
                          padx=8, pady=2)
        lbl_c.pack(side="right", padx=10)

        def _enter(e):
            hdr_frame.configure(highlightbackground=C.BLUE)
        def _leave(e):
            hdr_frame.configure(highlightbackground=C.GLASS_BD_3)

        for w in (hdr_frame, lbl_a, lbl_t, lbl_c):
            w.bind("<ButtonRelease-1>", lambda e: on_toggle())
            w.bind("<Enter>", _enter)
            w.bind("<Leave>", _leave)

    def _empty_notice(self, parent: tk.Widget, message: str) -> None:
        box = tk.Frame(parent, bg=C.GLASS_3,
                        highlightthickness=1,
                        highlightbackground=C.GLASS_BD_3,
                        padx=14, pady=12)
        box.pack(fill="x", pady=4)
        tk.Label(box, text=message,
                  font=(F._FALLBACK, F.SM),
                  bg=C.GLASS_3, fg=C.FG_2,
                  justify="left").pack(anchor="w")

    def _model_card(self, parent: tk.Widget, m: dict, is_available: bool = True, is_cloud: bool = False) -> None:
        is_active = (m["id"] == self._active_id)
        card_bg = C.GLASS_3

        card = tk.Frame(parent, bg=card_bg,
                        highlightthickness=1,
                        highlightbackground=C.BLUE if is_active else C.GLASS_BD_3,
                        cursor="hand2" if is_available else "arrow")
        card.pack(fill="x", pady=4)
        self._cards[m["id"]] = card

        # Left accent strip
        acc_color = C.BLUE if is_active else (C.GLASS_BD_3 if is_available else C.BG_S)
        acc = tk.Frame(card, bg=acc_color, width=4)
        acc.pack(side="left", fill="y")

        body = tk.Frame(card, bg=card_bg)
        body.pack(side="left", fill="both", expand=True, padx=12, pady=10)

        # Top row: name + badge
        top = tk.Frame(body, bg=card_bg)
        top.pack(fill="x")

        lbl_n = tk.Label(top, text=m["name"],
                          font=(F._PRIMARY, F.LG, "bold"),
                          bg=card_bg, fg=C.FG_1 if is_available else C.FG_3)
        lbl_n.pack(side="left")

        # Type badge chip
        chip_bg = C.CHIP_BG if m["type"] == "local" else C.BG_ACTIVE
        lbl_b = tk.Label(top,
                          text=f"  {m['type'].upper()}  ",
                          font=(F._FALLBACK, F.XS),
                          bg=chip_bg, fg=C.CHIP_FG, padx=2)
        lbl_b.pack(side="left", padx=6)

        if is_active:
            lbl_a = tk.Label(top, text=f"{I.MODEL_ACTIVE} Active",
                              font=(F._FALLBACK, F.XS, "bold"),
                              bg=C.OK_D, fg=C.OK_L, padx=6)
            lbl_a.pack(side="right")
        elif not is_available:
            status_text = "No API Key" if is_cloud else "Not Downloaded"
            lbl_a = tk.Label(top, text=f"{I.ERR_ICON} {status_text}",
                              font=(F._FALLBACK, F.XS),
                              bg=C.BG_C2, fg=C.FG_3, padx=6)
            lbl_a.pack(side="right")
        else:
            status_text = "API Connected" if is_cloud else "Installed"
            lbl_a = tk.Label(top, text=f"✓ {status_text}",
                              font=(F._FALLBACK, F.XS),
                              bg=C.OK_D, fg=C.OK_L, padx=6)
            lbl_a.pack(side="right")

        # Provider
        lbl_p = tk.Label(body, text=m["provider"],
                          font=(F._FALLBACK, F.XS),
                          bg=card_bg, fg=C.FG_3)
        lbl_p.pack(anchor="w")

        # Description
        lbl_d = tk.Label(body, text=m["description"],
                          font=(F._FALLBACK, F.SM),
                          bg=card_bg, fg=C.FG_2 if is_available else C.FG_3,
                          wraplength=300, justify="left")
        lbl_d.pack(anchor="w", pady=(4, 0))

        # Stats row
        stats = tk.Frame(body, bg=card_bg)
        stats.pack(fill="x", pady=(8, 0))

        for label, value in [
            ("Context", m["context"]),
            ("Speed",   m["speed"]),
            ("Reason",  m["reasoning"]),
            ("Privacy", m["privacy"]),
        ]:
            col = tk.Frame(stats, bg=card_bg)
            col.pack(side="left", padx=(0, 14))
            tk.Label(col, text=label,
                      font=(F._FALLBACK, F.XS - 1),
                      bg=card_bg, fg=C.FG_3).pack()
            tk.Label(col, text=value,
                      font=(F._FALLBACK, F.XS),
                      bg=card_bg, fg=C.FG_1 if is_available else C.FG_3).pack()

        # Capability chips
        cap_row = tk.Frame(body, bg=card_bg)
        cap_row.pack(fill="x", pady=(6, 0))
        for cap in m.get("capabilities", []):
            tk.Label(cap_row, text=f"  {cap}  ",
                      font=(F._FALLBACK, F.XS),
                      bg=C.CHIP_BG, fg=C.CHIP_FG if is_available else C.FG_3,
                      padx=2, pady=1).pack(side="left", padx=(0, 4))

        # Hover + click
        mid_ref = m["id"]
        def enter(e, c=card):
            if is_available:
                c.configure(highlightbackground=C.BLUE_L)
        def leave(e, c=card, mid=mid_ref):
            is_a = (mid == self._active_id)
            c.configure(highlightbackground=C.BLUE if is_a else C.GLASS_BD_3)
        def click(e, mid=mid_ref):
            if is_available:
                self._select(mid)

        for w in self._all_children(card):
            w.bind("<Enter>", enter)
            w.bind("<Leave>", leave)
            w.bind("<ButtonRelease-1>", click)

    def _all_children(self, w: tk.Widget) -> list:
        result = [w]
        for child in w.winfo_children():
            result.extend(self._all_children(child))
        return result

    def _select(self, model_id: str) -> None:
        self._active_id = model_id
        self._on_select(model_id)
        self._render_sections()

    def set_active(self, model_id: str) -> None:
        self._active_id = model_id
        self._render_sections()

    # ─────────────────────────────────────────────────────────────────────────
    def _on_theme_changed(self) -> None:
        self.frame.configure(bg=C.BG_S)
        self.hdr.configure(bg=C.GLASS_2)
        self.lbl_title.configure(bg=C.GLASS_2, fg=C.FG_1)
        self.cv.configure(bg=C.BG_S)
        self.inner.configure(bg=C.BG_S)
        self.lbl_legend.configure(bg=C.BG_S, fg=C.FG_3)
        self.sep.configure(bg=C.GLASS_BD_2)
        self._render_sections()
