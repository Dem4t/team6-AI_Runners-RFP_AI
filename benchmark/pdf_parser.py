import logging
from pathlib import Path
from typing import Dict
from pypdf import PdfReader
from pypdf.errors import PdfReadError

# Configure logging for parsing warnings/errors
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def extract_text(pdf_path: Path) -> str:
    """
    Safely extracts text from a PDF file.
    Returns an empty string if the file is unreadable or encrypted.
    """
    try:
        reader = PdfReader(pdf_path)
        
        # Check if the PDF is password protected
        if reader.is_encrypted:
            logger.warning(f"Skipping '{pdf_path.name}': Document is encrypted/password-protected.")
            return ""

        pages = []
        for i, page in enumerate(reader.pages):
            try:
                text = page.extract_text(extraction_mode="layout")
                if text and text.strip():
                    pages.append(text.strip())
            except Exception as page_err:
                logger.warning(f"Failed to read page {i+1} in '{pdf_path.name}': {page_err}")
                continue

        full_text = "\n\n".join(pages)

        # Warn if the document yielded no text (likely a scanned image)
        if not full_text.strip():
            logger.warning(f"No text extracted from '{pdf_path.name}'. It may be a scanned image.")
            
        return full_text

    except PdfReadError as e:
        logger.error(f"PDF read error on '{pdf_path.name}': {e}")
        return ""
    except Exception as e:
        logger.error(f"Unexpected error processing '{pdf_path.name}': {e}")
        return ""


def extract_all_rfps(rfp_directory: str) -> Dict[str, str]:
    """
    Iterates through a directory, safely extracting text from all PDF files.
    """
    directory = Path(rfp_directory)
    
    if not directory.exists() or not directory.is_dir():
        logger.error(f"Directory not found: {directory.absolute()}")
        return {}

    pdf_files = sorted(directory.glob("*.pdf"))
    rfps = {}

    for pdf_file in pdf_files:
        print(f"Reading: {pdf_file.name}")
        text = extract_text(pdf_file)
        if text:
            rfps[pdf_file.name] = text

    return rfps


if __name__ == "__main__":
    rfps = extract_all_rfps("data/rfps")
    print(f"\nFound {len(rfps)} RFPs\n")