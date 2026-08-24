"""
HELIOS v2 - Context Assembler
Aggregates dialogue history, active constraints, and ranked evidence blocks into a RetrievalContext payload.
"""
import uuid
from typing import List, Dict, Any
from core.knowledge.knowledge_models import RetrievalContext, EvidenceBlock

class ContextAssembler:
    def assemble_context(
        self,
        conversation_history: List[Dict[str, str]],
        evidence_blocks: List[EvidenceBlock],
        active_constraints: List[str]
    ) -> RetrievalContext:
        
        # Build unified context
        context_id = f"ctx-{uuid.uuid4().hex[:8]}"
        
        return RetrievalContext(
            context_id=context_id,
            conversation_history=conversation_history.copy(),
            evidence_blocks=evidence_blocks.copy(),
            constraints_active=active_constraints.copy()
        )
