"""
Extractor module to extract clean text from HTML and PDF documents.
"""
import logging
from typing import List, Dict, Any
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

def extract_html(raw_html: str, source_url: str) -> Dict[str, Any]:
    """
    Extracts clean text and title from raw HTML content.
    
    Args:
        raw_html: The raw HTML string.
        source_url: The URL the HTML was fetched from.
        
    Returns:
        Dictionary with extracted text, title, source_url, and source_type.
    """
    try:
        import trafilatura
        # Try trafilatura first
        text = trafilatura.extract(
            raw_html,
            output_format='markdown',
            include_tables=True,
            include_links=False,
            favor_precision=True
        )
        
        # Try to extract title
        try:
            bare_ext = trafilatura.bare_extraction(raw_html)
            title = bare_ext.get('title', '') if bare_ext else ''
        except Exception:
            title = ''
            
        if not title:
            # Fallback for title
            soup = BeautifulSoup(raw_html, 'html.parser')
            if soup.title:
                title = soup.title.string.strip() if soup.title.string else ''

        if not text or not text.strip():
            # Fallback to BeautifulSoup if trafilatura fails to extract text
            soup = BeautifulSoup(raw_html, 'html.parser')
            for script in soup(["script", "style"]):
                script.extract()
            text = soup.get_text(separator='\n')
            # Clean up multiple newlines
            lines = (line.strip() for line in text.splitlines())
            text = '\n'.join(line for line in lines if line)
            
        return {
            'text': text or '',
            'title': title or '',
            'source_url': source_url,
            'source_type': 'html'
        }
    except Exception as e:
        logger.warning(f"Failed to extract HTML for {source_url}: {e}")
        return {
            'text': '',
            'title': '',
            'source_url': source_url,
            'source_type': 'html'
        }


def extract_pdf(pdf_bytes: bytes, filename: str) -> List[Dict[str, Any]]:
    """
    Extracts text from PDF bytes.
    
    Args:
        pdf_bytes: The raw bytes of the PDF.
        filename: The filename or source identifier of the PDF.
        
    Returns:
        List of dictionaries containing extracted page text and metadata.
    """
    try:
        import pymupdf
        import pymupdf4llm
        
        # pymupdf4llm requires a Document object for byte streams
        doc = pymupdf.Document(stream=pdf_bytes, filetype='pdf')
        
        # Extract markdown chunks (page_chunks=True returns a list of dictionaries)
        md_chunks = pymupdf4llm.to_markdown(doc, page_chunks=True)
        
        result = []
        for chunk in md_chunks:
            page_text = chunk.get('text', '')
            if page_text and page_text.strip():
                result.append({
                    'text': page_text.strip(),
                    'page': chunk.get('metadata', {}).get('page', chunk.get('page', 0)),
                    'source': filename,
                    'source_type': 'pdf'
                })
                
        return result
    except Exception as e:
        print(f"Warning: Failed to extract PDF {filename}: {e}")
        return []


def extract_document(doc: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Dispatcher to extract text from a document based on its content_type.
    
    Args:
        doc: Dictionary containing document data ('content_type', 'content', 'url' or 'filename').
        
    Returns:
        List of extracted text chunks with metadata.
    """
    content_type = doc.get('content_type', '').lower()
    
    if content_type == 'html':
        raw_html = doc.get('content', '')
        source_url = doc.get('url', doc.get('source_url', ''))
        extracted = extract_html(raw_html, source_url)
        if extracted.get('text'):
            return [extracted]
        return []
        
    elif content_type == 'pdf':
        pdf_bytes = doc.get('content', b'')
        filename = doc.get('filename', doc.get('url', doc.get('source_url', '')))
        return extract_pdf(pdf_bytes, filename)
        
    else:
        # Unknown or unsupported content type
        return []
