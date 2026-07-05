import sys
from pathlib import Path

# Add project directory to path
sys.path.append(str(Path(__file__).parent))

from core.nl_router import NLRouter
from core.llm_engine import HybridLLM
from modules.file_creator import FileCreator

def test_routing():
    print("=== Testing Routing ===")
    llm = HybridLLM()
    router = NLRouter(llm)
    
    test_prompts = [
        "make a pdf of my resume",
        "convert IKS_Consolidated_Study_Guide.docx to pdf",
        "text file into a pdf fil",
        "[DOCX: IKS_Consolidated_Study_Guide.docx]\n\nIndian Knowledge Tradition (IKT) refers to...\n\nUser question: convert the file into pdf format"
    ]
    
    for prompt in test_prompts:
        result = router.parse(prompt)
        print(f"Prompt: '{prompt[:100]}...' -> {result}")

def test_conversion():
    print("\n=== Testing Conversion ===")
    creator = FileCreator()
    
    # Test real DOCX conversion
    real_docx = Path("C:/Users/bhara/Downloads/IKS_Consolidated_Study_Guide.docx")
    if real_docx.exists():
        print(f"Testing real DOCX conversion on: {real_docx.absolute()}")
        result = creator.convert_to_pdf(str(real_docx))
        print(result)
        real_pdf = real_docx.with_suffix(".pdf")
        if real_pdf.exists():
            print(f"Success! Real PDF created at: {real_pdf.absolute()} (size: {real_pdf.stat().st_size} bytes)")
    else:
        print(f"Real DOCX not found at expected path: {real_docx}")
        
    # Create a dummy text file
    dummy_txt = Path("dummy_test_file.txt")
    with open(dummy_txt, "w", encoding="utf-8") as f:
        f.write("Helios PDF Converter Test\n")
        f.write("=========================\n")
        
    print(f"Created temporary file: {dummy_txt.absolute()}")
    
    # Convert it
    result = creator.convert_to_pdf(str(dummy_txt))
    print(result)
    
    # Clean up
    pdf_path = dummy_txt.with_suffix(".pdf")
    if dummy_txt.exists():
        dummy_txt.unlink()
    if pdf_path.exists():
        pdf_path.unlink()
        print("Cleaned up temporary test files.")

if __name__ == "__main__":
    test_routing()
    test_conversion()
