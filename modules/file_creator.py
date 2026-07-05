"""HELIOS - File Creator: create files with content at specific locations"""
import os
import logging
import subprocess
from pathlib import Path

log = logging.getLogger("helios.file_creator")

LOCATIONS = {
    "desktop":   Path.home() / "Desktop",
    "documents": Path.home() / "Documents",
    "downloads": Path.home() / "Downloads",
    "home":      Path.home(),
}

class FileCreator:
    def create_file(self, name: str, location: str = "desktop",
                    content: str = "", open_after: bool = True) -> str:
        log.info("create_file called: name=%s, location=%s", name, location)
        try:
            folder = LOCATIONS.get(location.lower(), Path.home() / "Desktop")
            folder.mkdir(parents=True, exist_ok=True)
            if not Path(name).suffix:
                name += ".txt"
            path = folder / name
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            result = f"File created: {path.name}\nLocation: {path}"
            if content:
                result += f"\nContent: {content[:60]}{'...' if len(content)>60 else ''}"
            if open_after:
                try:
                    os.startfile(str(path))
                    result += "\nOpened in default editor."
                except Exception as e:
                    log.warning("startfile failed: %s, falling back to notepad", e)
                    subprocess.Popen(["notepad.exe", str(path)])
            log.info("Successfully created file: %s", path)
            return result
        except Exception as exc:
            log.error("Error creating file: %s", exc, exc_info=True)
            return f"Failed to create file: {exc}"

    def create_in_notepad(self, name: str, location: str = "desktop",
                          content: str = "") -> str:
        log.info("create_in_notepad called: name=%s, location=%s", name, location)
        try:
            folder = LOCATIONS.get(location.lower(), Path.home() / "Desktop")
            folder.mkdir(parents=True, exist_ok=True)
            if not Path(name).suffix:
                name += ".txt"
            path = folder / name
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            subprocess.Popen(["notepad.exe", str(path)])
            log.info("Successfully created file and opened in notepad: %s", path)
            return (f"File '{path.name}' created on {location}.\n"
                    f"Content: {content}\nOpened in Notepad.")
        except Exception as exc:
            log.error("Error creating file in notepad: %s", exc, exc_info=True)
            return f"Failed to create file in notepad: {exc}"

    def _clean_pdf_text(self, text: str) -> str:
        """Replace common MS Word and unicode special characters to prevent encoding crashes in standard PDF fonts."""
        replacements = {
            '\u2013': '-', # en-dash
            '\u2014': '-', # em-dash
            '\u2018': "'", # left single quote
            '\u2019': "'", # right single quote
            '\u201c': '"', # left double quote
            '\u201d': '"', # right double quote
            '\u2022': '*', # bullet point
            '\u2026': '...', # ellipsis
            '\u00a0': ' ', # non-breaking space
            '\u200b': '',  # zero-width space
        }
        for k, v in replacements.items():
            text = text.replace(k, v)
        # Force conversion to latin-1 (WinAnsiEncoding compatible) to avoid reportlab font encoding failures
        return text.encode('latin1', errors='replace').decode('latin1')

    def convert_to_pdf(self, source_path: str) -> str:
        """Convert a txt or docx file to pdf using reportlab."""
        log.info("convert_to_pdf called: source_path=%s", source_path)
        try:
            import docx
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        except ImportError as err:
            msg = (
                f"Missing PDF conversion libraries.\n"
                f"Please run: pip install python-docx reportlab\n"
                f"Detail: {err}"
            )
            log.error("PDF conversion libraries not installed: %s", err)
            return msg

        src = Path(source_path)
        if not src.exists():
            log.warning("Source file not found for conversion: %s", source_path)
            return f"Error: Source file does not exist at {source_path}"
        
        pdf_path = src.with_suffix(".pdf")
        ext = src.suffix.lower()
        
        try:
            story = []
            styles = getSampleStyleSheet()
            
            body_style = ParagraphStyle(
                'PDFBody',
                parent=styles['Normal'],
                fontName='Helvetica',
                fontSize=10,
                leading=14,
                spaceAfter=6
            )
            
            title_style = ParagraphStyle(
                'PDFTitle',
                parent=styles['Heading1'],
                fontName='Helvetica-Bold',
                fontSize=18,
                leading=22,
                spaceAfter=12
            )
            
            heading_style = ParagraphStyle(
                'PDFHeading',
                parent=styles['Heading2'],
                fontName='Helvetica-Bold',
                fontSize=13,
                leading=17,
                spaceBefore=10,
                spaceAfter=6
            )
            
            if ext == ".docx":
                doc = docx.Document(str(src))
                for p in doc.paragraphs:
                    text = p.text.strip()
                    if not text:
                        continue
                    cleaned = self._clean_pdf_text(text)
                    style_name = p.style.name.lower() if (p.style and getattr(p.style, 'name', None)) else ""
                    if 'title' in style_name:
                        story.append(Paragraph(cleaned, title_style))
                    elif 'heading' in style_name:
                        story.append(Paragraph(cleaned, heading_style))
                    else:
                        story.append(Paragraph(cleaned, body_style))
            else:
                # Convert as text/txt file
                with open(src, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
                for line in lines:
                    cleaned = self._clean_pdf_text(line.strip())
                    if cleaned:
                        story.append(Paragraph(cleaned, body_style))
                    else:
                        story.append(Spacer(1, 4))
            
            if not story:
                log.warning("No text found in source file: %s", src.name)
                return f"Error: No readable text found in {src.name} to convert."
                
            doc_pdf = SimpleDocTemplate(str(pdf_path), pagesize=letter)
            doc_pdf.build(story)
            
            # Open PDF automatically
            try:
                os.startfile(str(pdf_path))
                open_msg = "\nOpened PDF file in default viewer."
            except Exception as e:
                log.warning("Could not open converted PDF automatically: %s", e)
                open_msg = ""
                
            log.info("Successfully converted file to PDF: %s", pdf_path)
            return f"Successfully converted '{src.name}' to PDF!\nSaved at: {pdf_path}{open_msg}"
            
        except Exception as e:
            log.error("Failed to convert file to PDF: %s", e, exc_info=True)
            return f"Failed to convert '{src.name}' to PDF: {e}"

