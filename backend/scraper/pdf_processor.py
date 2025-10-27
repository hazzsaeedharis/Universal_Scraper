"""
PDF Processing with OCR fallback for menu extraction.
Multi-layer strategy: Vision API → pdfplumber → PyPDF2 → OCR (pytesseract)
"""
import os
import tempfile
import base64
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
from ..config import get_settings

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
        
        self.settings = get_settings()
        self.max_pages = max_pages
        self.max_size_mb = max_size_mb
        self.ocr_languages = ocr_languages
        self.use_vision = self.settings.use_vision_for_pdfs
        
        # Initialize Groq client for vision if enabled
        if self.use_vision:
            try:
                from ..ai.groq_client import GroqClient
                self.groq_client = GroqClient()
                logger.info(f"🔍 Vision-based PDF extraction enabled (model: {self.settings.vision_model})")
            except Exception as e:
                logger.warning(f"Failed to initialize Groq vision: {e}, falling back to OCR")
                self.use_vision = False
                self.groq_client = None
        else:
            self.groq_client = None
        
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
    
    def _pdf_to_images(self, pdf_path: str) -> List[Image.Image]:
        """
        Convert PDF pages to PIL Images.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            List of PIL Images, one per page
        """
        try:
            images = pdf2image.convert_from_path(
                pdf_path,
                dpi=200,  # Good quality for vision API
                first_page=1,
                last_page=min(self.max_pages, 100)  # Safety limit
            )
            logger.info(f"Converted PDF to {len(images)} images")
            return images
        except Exception as e:
            logger.error(f"Failed to convert PDF to images: {e}")
            return []
    
    def _image_to_base64(self, image: Image.Image) -> str:
        """
        Convert PIL Image to base64 string.
        
        Args:
            image: PIL Image
            
        Returns:
            Base64 encoded string
        """
        import io
        buffer = io.BytesIO()
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')
        # Save as JPEG (smaller than PNG)
        image.save(buffer, format='JPEG', quality=85)
        img_bytes = buffer.getvalue()
        return base64.b64encode(img_bytes).decode('utf-8')
    
    def _extract_with_vision(self, pdf_path: str) -> str:
        """
        Extract text from PDF using Groq vision API.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Extracted text from all pages
        """
        if not self.use_vision or not self.groq_client:
            return ""
        
        try:
            # Convert PDF to images
            images = self._pdf_to_images(pdf_path)
            if not images:
                logger.warning("No images extracted from PDF")
                return ""
            
            # Process each page with vision API
            all_text = []
            for i, image in enumerate(images, 1):
                logger.info(f"Processing page {i}/{len(images)} with vision API...")
                
                # Convert to base64
                base64_image = self._image_to_base64(image)
                
                # Prepare prompt for menu extraction
                prompt = """Extract ALL text from this image in a structured format. 

If this is a menu:
- List all items with names and prices
- Include sections/categories (Appetizers, Mains, Desserts, Drinks, etc.)
- Preserve the order and structure
- Note any special annotations (vegan, gluten-free, spicy, etc.)

If this is not a menu, extract all visible text accurately.

Be thorough and precise."""
                
                # Send to Groq vision API
                try:
                    from groq import Groq
                    client = Groq(api_key=self.settings.groq_api_key)
                    
                    completion = client.chat.completions.create(
                        model=self.settings.vision_model,
                        messages=[{
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{base64_image}"
                                    }
                                }
                            ]
                        }],
                        temperature=0.1,  # Low temperature for accurate extraction
                        max_tokens=2000
                    )
                    
                    page_text = completion.choices[0].message.content
                    all_text.append(f"--- Page {i} ---\n{page_text}\n")
                    logger.info(f"✅ Page {i} extracted via vision API ({len(page_text)} chars)")
                    
                except Exception as e:
                    logger.error(f"Vision API error for page {i}: {e}")
                    continue
            
            if all_text:
                combined_text = "\n".join(all_text)
                logger.info(f"🔍 Vision extraction complete: {len(combined_text)} total characters")
                return combined_text
            else:
                logger.warning("Vision extraction failed for all pages")
                return ""
                
        except Exception as e:
            logger.error(f"Vision extraction failed: {e}")
            return ""
    
    def _is_text_extraction_good(self, text: str, page_count: int) -> bool:
        """
        Check if text extraction was successful.
        
        Args:
            text: Extracted text
            page_count: Number of pages processed
            
        Returns:
            True if text extraction is good quality
        """
        if not text or len(text) < 100:
            return False
        
        # Check average characters per page
        avg_chars_per_page = len(text) / max(page_count, 1)
        
        # If less than 50 chars per page, likely scanned/poor extraction
        if avg_chars_per_page < 50:
            logger.info(f"Low text density ({avg_chars_per_page:.0f} chars/page), likely scanned PDF")
            return False
        
        # Check for gibberish (too many special characters)
        import re
        alphanumeric = len(re.findall(r'[a-zA-Z0-9]', text))
        special = len(re.findall(r'[^a-zA-Z0-9\s]', text))
        
        if special > alphanumeric * 0.5:  # More than 50% special chars
            logger.info("High special character ratio, likely poor extraction")
            return False
        
        logger.info(f"Text extraction looks good ({avg_chars_per_page:.0f} chars/page)")
        return True
    
    def _merge_extraction_results(self, vision_text: str, ocr_text: str) -> str:
        """
        Intelligently merge vision and OCR extraction results.
        
        Args:
            vision_text: Text from vision API (structured, high quality)
            ocr_text: Text from OCR (may have extra details)
            
        Returns:
            Combined text optimized for RAG
        """
        if not vision_text and not ocr_text:
            return ""
        
        if not vision_text:
            return ocr_text
        
        if not ocr_text:
            return vision_text
        
        # Combine both with clear sections
        combined = f"""=== VISION API EXTRACTION (Structured) ===
{vision_text}

=== OCR EXTRACTION (Additional Details) ===
{ocr_text}

=== COMBINED FOR RAG ===
This document was processed with both vision AI and OCR for maximum accuracy.
Vision extraction provides structured layout and formatting.
OCR extraction may contain additional text details.
"""
        
        logger.info(f"📊 Merged results: Vision={len(vision_text)} chars, OCR={len(ocr_text)} chars, Combined={len(combined)} chars")
        return combined
    
    async def _extract_parallel(self, pdf_path: str) -> tuple[str, str]:
        """
        Run vision and OCR extraction in parallel.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Tuple of (vision_text, ocr_text)
        """
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        
        async def run_vision():
            if self.use_vision:
                logger.info("🔍 Starting vision extraction...")
                return self._extract_with_vision(pdf_path)
            return ""
        
        async def run_ocr():
            logger.info("📝 Starting OCR extraction...")
            # Run OCR in thread pool (it's CPU-intensive)
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as pool:
                pages = await loop.run_in_executor(pool, self.extract_text_from_pdf, pdf_path)
                
                if pages:
                    text_parts = []
                    for page in pages:
                        text_parts.append(f"--- Page {page['page_num']} ---")
                        text_parts.append(page['text'])
                        text_parts.append("")
                    return "\n".join(text_parts)
                return ""
        
        # Run both in parallel
        logger.info("⚡ Running vision API and OCR in parallel...")
        vision_text, ocr_text = await asyncio.gather(
            run_vision(),
            run_ocr(),
            return_exceptions=True
        )
        
        # Handle exceptions
        if isinstance(vision_text, Exception):
            logger.error(f"Vision extraction error: {vision_text}")
            vision_text = ""
        
        if isinstance(ocr_text, Exception):
            logger.error(f"OCR extraction error: {ocr_text}")
            ocr_text = ""
        
        return vision_text, ocr_text
    
    def extract_full_text(self, pdf_path: str) -> str:
        """
        Extract all text from PDF using BOTH vision API and OCR in parallel.
        Combines results for maximum accuracy and detail.
        
        Strategy:
        1. Run vision API and OCR simultaneously (parallel)
        2. Merge both results intelligently
        3. Return combined text optimized for RAG
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Combined text from all extraction methods
        """
        # First try simple text extraction (pdfplumber/PyPDF2)
        logger.info("🚀 Quick check: trying pdfplumber/PyPDF2...")
        
        # Try pdfplumber first (fast check)
        try:
            with pdfplumber.open(pdf_path) as pdf:
                first_page_text = pdf.pages[0].extract_text() if pdf.pages else ""
                if first_page_text and len(first_page_text) > 200:
                    # Good text-based PDF, extract all pages
                    logger.info("✅ Text-based PDF detected, using fast extraction...")
                    pages = self.extract_text_from_pdf(pdf_path)
                    if pages:
                        text_parts = []
                        for page in pages:
                            text_parts.append(f"--- Page {page['page_num']} ---")
                            text_parts.append(page['text'])
                            text_parts.append("")
                        full_text = "\n".join(text_parts)
                        logger.info(f"✅ Fast extraction complete: {len(full_text)} chars")
                        return full_text
        except Exception as e:
            logger.warning(f"Fast extraction check failed: {e}")
        
        # Scanned or complex PDF - use parallel extraction
        logger.info("📸 Scanned/complex PDF detected, using parallel extraction...")
        
        # Need to run async extraction
        import asyncio
        try:
            # Check if we're already in an event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We're in an async context, but can't use await here
                # Fall back to sequential
                logger.warning("Already in event loop, using sequential extraction")
                vision_text = self._extract_with_vision(pdf_path) if self.use_vision else ""
                pages = self.extract_text_from_pdf(pdf_path)
                ocr_text = ""
                if pages:
                    text_parts = []
                    for page in pages:
                        text_parts.append(f"--- Page {page['page_num']} ---")
                        text_parts.append(page['text'])
                        text_parts.append("")
                    ocr_text = "\n".join(text_parts)
            else:
                # Create new event loop for parallel execution
                vision_text, ocr_text = loop.run_until_complete(self._extract_parallel(pdf_path))
        except RuntimeError:
            # No event loop, create one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                vision_text, ocr_text = loop.run_until_complete(self._extract_parallel(pdf_path))
            finally:
                loop.close()
        
        # Merge results
        combined_text = self._merge_extraction_results(vision_text, ocr_text)
        
        if combined_text:
            logger.info(f"✅ Parallel extraction complete: {len(combined_text)} total chars")
            return combined_text
        
        logger.error("❌ All extraction methods failed")
        return ""
    
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

