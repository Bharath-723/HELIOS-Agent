"""
HELIOS v2 - Context Builder
Assembles global system states and environments for reasoning tasks.
"""
import psutil
from typing import List, Dict, Any, Optional
from core.reasoning.reasoning_models import ReasoningContext

class ContextBuilder:
    def __init__(self):
        self.conversation_history = []
        self.memory_references = []
        
    def add_history(self, role: str, content: str):
        self.conversation_history.append({"role": role, "content": content})
        
    def add_memory(self, memory_text: str):
        self.memory_references.append(memory_text)

    def build(self, internet_available: bool = True, local_model_available: bool = True) -> ReasoningContext:
        # Fetch actual system metrics safely
        cpu_percent = psutil.cpu_percent()
        ram = psutil.virtual_memory()
        ram_avail_mb = ram.available / (1024 * 1024)
        
        system_state = {
            "cpu_usage_pct": cpu_percent,
            "ram_available_mb": ram_avail_mb,
            "active_tasks_count": 0
        }
        
        hardware_specs = {
            "total_ram_gb": round(ram.total / (1024 * 1024 * 1024), 2),
            "low_ram_mode": ram_avail_mb < 4000.0
        }
        
        # Tools and models list
        available_tools = ["DesktopAgent", "NotesManager", "TaskScheduler", "WebSearch", "GmailComposer", "FileCreator"]
        available_models = ["gemma3", "mistral", "gemini-2.0-flash", "gpt-4o-mini"]

        return ReasoningContext(
            conversation_history=self.conversation_history.copy(),
            memory_references=self.memory_references.copy(),
            available_tools=available_tools,
            available_models=available_models,
            system_state=system_state,
            hardware_specs=hardware_specs,
            internet_available=internet_available,
            local_model_available=local_model_available,
            privacy_constraints_active=False
        )
