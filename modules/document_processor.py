"""
modules/document_processor.py — HELIOS Document Processing Pipeline
=====================================================================
Multi-format document reader and text extractor with robust fallback paths.
Supports PDF, DOCX, TXT, MD, CSV, JSON, and image files.
Dependency-aware: operates with zero crashes when external libraries are absent.
"""

import os
import re
import zipfile
import logging
from pathlib import Path

log = logging.getLogger("helios.document_processor")

class DocumentProcessor:
    """Multi-format document text extraction engine."""

    @staticmethod
    def extract_text(file_path: str) -> str:
        p = Path(file_path)
        if not p.exists():
            return f"[Error: File '{file_path}' does not exist]"

        ext = p.suffix.lower()
        log.info("Extracting text from file '%s' (type: %s)", p.name, ext)

        try:
            if ext in {".txt", ".md", ".json", ".csv", ".py", ".html", ".log", ".xml", ".yaml", ".yml"}:
                return p.read_text(encoding="utf-8", errors="ignore")

            elif ext == ".pdf":
                return DocumentProcessor._extract_pdf(p)

            elif ext == ".docx":
                return DocumentProcessor._extract_docx(p)

            elif ext in {".png", ".jpg", ".jpeg", ".bmp", ".webp"}:
                try:
                    from core.ocr_provider import OCRProvider
                    return OCRProvider().extract_text_from_file(str(p))
                except Exception:
                    return f"[Image attachment '{p.name}' received. OCR adapter unavailable]"

            else:
                return p.read_text(encoding="utf-8", errors="ignore")

        except Exception as exc:
            log.error("Failed to extract text from %s: %s", p.name, exc, exc_info=True)
            return f"[Error extracting text from '{p.name}': {exc}]"

    @staticmethod
    def _extract_pdf(p: Path) -> str:
        # 1. Try pypdf
        try:
            import pypdf
            reader = pypdf.PdfReader(str(p))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
            if text.strip():
                return text
        except ImportError:
            pass
        except Exception as e:
            log.warning("pypdf extraction failed for %s: %s", p.name, e)

        # 2. Try pdfplumber
        try:
            import pdfplumber
            with pdfplumber.open(str(p)) as pdf:
                text = "\n".join(page.extract_text() or "" for page in pdf.pages)
                if text.strip():
                    return text
        except ImportError:
            pass
        except Exception as e:
            log.warning("pdfplumber extraction failed for %s: %s", p.name, e)

        # 3. Try PyMuPDF (fitz)
        try:
            import fitz
            doc = fitz.open(str(p))
            text = "\n".join(page.get_text() or "" for page in doc)
            if text.strip():
                return text
        except ImportError:
            pass
        except Exception as e:
            log.warning("fitz extraction failed for %s: %s", p.name, e)

        # 4. Standard library raw stream text extraction fallback
        try:
            raw_bytes = p.read_bytes()
            strings = re.findall(rb'\(([^\)]+)\)\s*TJ|BT\s+([^\r\n]+)\s+ET|\(([^\)]+)\)', raw_bytes)
            extracted = []
            for match in strings:
                for grp in match:
                    if grp:
                        extracted.append(grp.decode('utf-8', errors='ignore'))
            text = " ".join(extracted)
            if text.strip():
                return text
        except Exception as e:
            log.warning("Raw PDF stream extraction failed: %s", e)

        # 5. Scanned PDF fallback via OCRProvider if text is empty
        try:
            from core.ocr_provider import OCRProvider
            ocr = OCRProvider()
            if ocr.available():
                ocr_text = ocr.extract_text_from_file(str(p))
                if ocr_text and "No text detected" not in ocr_text:
                    return ocr_text
        except Exception as e:
            log.warning("OCR fallback for PDF failed: %s", e)

        return f"[PDF Document '{p.name}' loaded. Text extraction libraries (pypdf/pdfplumber) unavailable]"

    @staticmethod
    def _extract_docx(p: Path) -> str:
        # 1. Try python-docx
        try:
            import docx
            doc = docx.Document(str(p))
            return "\n".join(para.text for para in doc.paragraphs)
        except ImportError:
            pass
        except Exception as e:
            log.warning("python-docx extraction failed for %s: %s", p.name, e)

        # 2. Zip XML extraction fallback
        try:
            with zipfile.ZipFile(str(p)) as z:
                xml_content = z.read("word/document.xml").decode("utf-8", errors="ignore")
                text = re.sub(r'<[^>]+>', ' ', xml_content)
                text = re.sub(r'\s+', ' ', text)
                return text.strip()
        except Exception as e:
            log.warning("DOCX zip XML extraction failed for %s: %s", p.name, e)

        return f"[DOCX Document '{p.name}' loaded]"
