"""HELIOS - File Creator: create files with content at specific locations"""
import os
import subprocess
from pathlib import Path

# PDF conversion requirements
import docx
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

LOCATIONS = {
    "desktop":   Path.home() / "Desktop",
    "documents": Path.home() / "Documents",
    "downloads": Path.home() / "Downloads",
    "home":      Path.home(),
}

class FileCreator:
    def create_file(self, name: str, location: str = "desktop",
                    content: str = "", open_after: bool = True) -> str:
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
            except Exception:
                subprocess.Popen(["notepad.exe", str(path)])
        return result

    def create_in_notepad(self, name: str, location: str = "desktop",
                          content: str = "") -> str:
        folder = LOCATIONS.get(location.lower(), Path.home() / "Desktop")
        folder.mkdir(parents=True, exist_ok=True)
        if not Path(name).suffix:
            name += ".txt"
        path = folder / name
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        subprocess.Popen(["notepad.exe", str(path)])
        return (f"File '{path.name}' created on {location}.\n"
                f"Content: {content}\nOpened in Notepad.")

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
        src = Path(source_path)
        if not src.exists():
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
                return f"Error: No readable text found in {src.name} to convert."
                
            doc_pdf = SimpleDocTemplate(str(pdf_path), pagesize=letter)
            doc_pdf.build(story)
            
            # Open PDF automatically
            try:
                os.startfile(str(pdf_path))
                open_msg = "\nOpened PDF file in default viewer."
            except Exception:
                open_msg = ""
                
            return f"Successfully converted '{src.name}' to PDF!\nSaved at: {pdf_path}{open_msg}"
            
        except Exception as e:
            return f"Failed to convert '{src.name}' to PDF: {e}"

