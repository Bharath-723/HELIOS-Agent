"""
core/local_rag.py — HELIOS Modular Local RAG Connector
======================================================
Local-first document indexing and retrieval engine over local notes and documents.
Provides grounded context, source attribution, and relevance scores without cloud data leakage.
"""

import os
import re
import math
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

from core.system import paths_manager

log = logging.getLogger("helios.local_rag")

class LocalRAGDocument:
    def __init__(self, file_path: str, content: str):
        self.file_path = file_path
        self.filename = Path(file_path).name
        self.content = content
        self.chunks = self._chunk_text(content)

    def _chunk_text(self, text: str, chunk_size: int = 400, overlap: int = 50) -> List[str]:
        words = text.split()
        if not words:
            return []
        chunks = []
        for i in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[i:i + chunk_size])
            chunks.append(chunk)
        return chunks


class LocalRAGConnector:
    """Local RAG retrieval engine."""

    def __init__(self, documents_dir: Optional[str] = None):
        self.docs_dir = Path(documents_dir) if documents_dir else paths_manager.notes_dir
        self.index: List[Dict[str, Any]] = []
        self._build_index()

    def index_file(self, file_path: str) -> None:
        p = Path(file_path)
        if not p.exists():
            return
        try:
            from modules.document_processor import DocumentProcessor
            text = DocumentProcessor.extract_text(str(p))
            if text and not text.startswith("[Error"):
                doc = LocalRAGDocument(str(p), text)
                for chunk in doc.chunks:
                    self.index.append({
                        "file_path": str(p),
                        "filename": p.name,
                        "chunk": chunk,
                        "words": set(re.findall(r'\w+', chunk.lower()))
                    })
                log.info("Indexed file '%s' (%d chunks).", p.name, len(doc.chunks))
        except Exception as exc:
            log.warning("Could not index file %s: %s", p.name, exc)

    def _build_index(self) -> None:
        log.info("Building Local RAG index from %s", self.docs_dir)
        self.index.clear()
        if not self.docs_dir.exists():
            return

        for p in list(self.docs_dir.glob("*.md")) + list(self.docs_dir.glob("*.docx")) + list(self.docs_dir.glob("*.txt")) + list(self.docs_dir.glob("*.pdf")):
            self.index_file(str(p))
        log.info("Local RAG indexed %d document chunks.", len(self.index))

    def available(self) -> bool:
        return len(self.index) > 0

    def retrieve(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        if not self.index:
            self._build_index()

        q_words = set(re.findall(r'\w+', query.lower()))
        if not q_words:
            return []

        results = []
        for item in self.index:
            overlap = item["words"].intersection(q_words)
            if overlap:
                score = len(overlap) / float(len(q_words))
                results.append({
                    "filename": item["filename"],
                    "file_path": item["file_path"],
                    "chunk": item["chunk"],
                    "relevance_score": score
                })

        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        return results[:top_k]

    def query(self, user_query: str) -> str:
        hits = self.retrieve(user_query, top_k=3)
        if not hits:
            return "[Local RAG: No relevant local documents found for query]"

        lines = [f"• Grounded Local Knowledge ({len(hits)} source matches):\n"]
        for i, hit in enumerate(hits, 1):
            lines.append(f"Source {i}: {hit['filename']} (Relevance: {hit['relevance_score']:.2f})")
            lines.append(f"Content: \"{hit['chunk'][:300]}...\"\n")
        return "\n".join(lines)
