"""
PDF Processing with OCR fallback for menu extraction.
Multi-layer strategy: pdfplumber → PyPDF2 → OCR (pytesseract)
"""
import os
import tempfile
from typing import List, Dict, Any, Optional
from pathlib import Path

try:
    import PyPDF2
    import pdfplumber
    import pytesseract
    import pdf2image
    from PIL import Image
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class PDFProcessor:
    """Process PDF files with multi-layer text extraction and OCR fallback."""
    
    def __init__(
        self,
        max_pages: int = 20,
        max_size_mb: int = 50,
        ocr_languages: str = "eng+deu+fra+spa"
    ):
        """
        Initialize PDF processor.
        
        Args:
            max_pages: Maximum number of pages to process
            max_size_mb: Maximum file size in MB
            ocr_languages: Languages for OCR (tesseract format)
        """
        if not PDF_SUPPORT:
            raise ImportError(
                "PDF processing requires: PyPDF2, pdfplumber, pytesseract, pdf2image, Pillow. "
                "Install with: pip install PyPDF2 pdfplumber pytesseract pdf2image Pillow"
            )
        
        self.max_pages = max_pages
        self.max_size_mb = max_size_mb
        self.ocr_languages = ocr_languages
        
        # Test if tesseract is available
        try:
            pytesseract.get_tesseract_version()
            self.ocr_available = True
            logger.info(f"Tesseract OCR available, languages: {ocr_languages}")
        except Exception as e:
            self.ocr_available = False
            logger.warning(f"Tesseract OCR not available: {e}")
    
    def validate_pdf(self, pdf_path: str) -> bool:
        """
        Validate PDF file size and readability.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            True if PDF is valid and processable
        """
        try:
            # Check file exists
            if not os.path.exists(pdf_path):
                logger.error(f"PDF file not found: {pdf_path}")
                return False
            
            # Check file size
            file_size_mb = os.path.getsize(pdf_path) / (1024 * 1024)
            if file_size_mb > self.max_size_mb:
                logger.warning(f"PDF too large: {file_size_mb:.1f}MB > {self.max_size_mb}MB")
                return False
            
            logger.info(f"PDF validated: {file_size_mb:.1f}MB")
            return True
            
        except Exception as e:
            logger.error(f"Error validating PDF: {e}")
            return False
    
    def extract_text_from_pdf(self, pdf_path: str) -> List[Dict[str, Any]]:
        """
        Extract text from PDF with page information, using multi-layer strategy.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            List of page dictionaries with text and metadata
        """
        if not self.validate_pdf(pdf_path):
            return []
        
        pages = []
        
        # Layer 1: Try pdfplumber first (best for tables and structured content)
        logger.info("Attempting extraction with pdfplumber...")
        try:
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = min(len(pdf.pages), self.max_pages)
                logger.info(f"PDF has {len(pdf.pages)} pages, processing {total_pages}")
                
                for i, page in enumerate(pdf.pages[:total_pages]):
                    text = page.extract_text()
                    if text and text.strip():
                        pages.append({
                            "page_num": i + 1,
                            "text": text.strip(),
                            "tables": page.extract_tables() or [],
                            "extraction_method": "pdfplumber"
                        })
                        logger.info(f"Page {i+1}/{total_pages} extracted with pdfplumber")
                
                if pages:
                    logger.info(f"✅ pdfplumber extracted {len(pages)} pages")
                    return pages
                    
        except Exception as e:
            logger.warning(f"pdfplumber failed: {e}")
        
        # Layer 2: Fallback to PyPDF2
        logger.info("Attempting extraction with PyPDF2...")
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                total_pages = min(len(reader.pages), self.max_pages)
                logger.info(f"PDF has {len(reader.pages)} pages, processing {total_pages}")
                
                for i, page in enumerate(reader.pages[:total_pages]):
                    text = page.extract_text()
                    if text and text.strip():
                        pages.append({
                            "page_num": i + 1,
                            "text": text.strip(),
                            "tables": [],
                            "extraction_method": "pypdf2"
                        })
                        logger.info(f"Page {i+1}/{total_pages} extracted with PyPDF2")
                
                if pages:
                    logger.info(f"✅ PyPDF2 extracted {len(pages)} pages")
                    return pages
                    
        except Exception as e:
            logger.warning(f"PyPDF2 failed: {e}")
        
        # Layer 3: OCR fallback (for scanned PDFs)
        if self.ocr_available:
            logger.info("No text extracted, attempting OCR...")
            try:
                # Convert PDF to images
                logger.info("Converting PDF to images...")
                pdf_images = pdf2image.convert_from_path(
                    pdf_path,
                    first_page=1,
                    last_page=self.max_pages
                )
                
                logger.info(f"Processing {len(pdf_images)} pages with OCR")
                for i, img in enumerate(pdf_images):
                    logger.info(f"OCR processing page {i+1}/{len(pdf_images)}...")
                    
                    # Preprocess image for better OCR
                    img = self._preprocess_image(img)
                    
                    # Run OCR
                    text = pytesseract.image_to_string(img, lang=self.ocr_languages)
                    
                    if text and text.strip():
                        pages.append({
                            "page_num": i + 1,
                            "text": text.strip(),
                            "tables": [],
                            "extraction_method": "ocr"
                        })
                        logger.info(f"✅ Page {i+1} extracted via OCR")
                    else:
                        logger.warning(f"Page {i+1} - OCR returned no text")
                
                if pages:
                    logger.info(f"✅ OCR extracted {len(pages)} pages")
                    return pages
                    
            except Exception as e:
                logger.error(f"OCR extraction failed: {e}")
                logger.error("Ensure Tesseract OCR and poppler-utils are installed")
        else:
            logger.warning("OCR not available, cannot process scanned PDFs")
        
        # All methods failed
        logger.error("All extraction methods failed")
        return []
    
    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Preprocess image for better OCR accuracy.
        
        Args:
            image: PIL Image
            
        Returns:
            Preprocessed PIL Image
        """
        try:
            # Convert to grayscale
            image = image.convert('L')
            
            # Increase contrast (optional, helps with faded scans)
            from PIL import ImageEnhance
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.5)
            
            # Resize if too small (OCR works better with larger images)
            min_width = 1200
            if image.width < min_width:
                ratio = min_width / image.width
                new_size = (int(image.width * ratio), int(image.height * ratio))
                image = image.resize(new_size, Image.Resampling.LANCZOS)
            
            return image
            
        except Exception as e:
            logger.warning(f"Image preprocessing failed: {e}")
            return image
    
    def extract_full_text(self, pdf_path: str) -> str:
        """
        Extract all text from PDF as a single string.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Combined text from all pages
        """
        pages = self.extract_text_from_pdf(pdf_path)
        
        if not pages:
            return ""
        
        # Combine all page texts
        text_parts = []
        for page in pages:
            text_parts.append(f"--- Page {page['page_num']} ---")
            text_parts.append(page['text'])
            text_parts.append("")  # Empty line between pages
        
        full_text = "\n".join(text_parts)
        
        logger.info(f"Extracted {len(pages)} pages, total {len(full_text)} characters")
        return full_text
    
    def is_menu_pdf(self, text: str) -> bool:
        """
        Simple heuristic to detect if PDF contains a menu.
        
        Args:
            text: Extracted text from PDF
            
        Returns:
            True if likely a menu PDF
        """
        text_lower = text.lower()
        
        # Menu indicators
        menu_keywords = [
            'menu', 'speisekarte', 'carte', 'menü',
            'appetizer', 'vorspeise', 'entrée',
            'main course', 'hauptgericht', 'plat principal',
            'dessert', 'nachspeise',
            'beverage', 'getränke', 'boisson', 'drinks',
            'price', 'preis', 'prix', '€', '$', '£'
        ]
        
        # Count matches
        matches = sum(1 for keyword in menu_keywords if keyword in text_lower)
        
        # If 3+ keywords found, likely a menu
        is_menu = matches >= 3
        
        logger.info(f"Menu detection: {matches} keywords found, is_menu={is_menu}")
        return is_menu


# Convenience function for quick extraction
def extract_text_from_pdf(pdf_path: str, max_pages: int = 20) -> str:
    """
    Quick function to extract text from a PDF file.
    
    Args:
        pdf_path: Path to PDF file
        max_pages: Maximum pages to process
        
    Returns:
        Extracted text
    """
    processor = PDFProcessor(max_pages=max_pages)
    return processor.extract_full_text(pdf_path)

