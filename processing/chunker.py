"""
Chunker module to split extracted text into smaller chunks for embedding.
"""
import re
from typing import List, Dict, Any
import sys
import os

# Ensure project root is in path if needed to import config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config


def chunk_document(text: str, metadata: Dict[str, Any], chunk_size: int = None, overlap: int = None) -> List[Dict[str, Any]]:
    """
    Splits extracted text into chunks for embedding based on configured limits and overlap.
    
    Args:
        text: The extracted text to chunk.
        metadata: Metadata to include with each chunk.
        chunk_size: Maximum characters per chunk (defaults to config limit).
        overlap: Overlap characters between chunks (defaults to config limit).
        
    Returns:
        List of dictionaries containing chunk text and metadata.
    """
    if chunk_size is None:
        chunk_size = config.CHUNK_SIZE_TOKENS * config.CHARS_PER_TOKEN
    if overlap is None:
        overlap = config.CHUNK_OVERLAP_TOKENS * config.CHARS_PER_TOKEN

    def split_text(text_to_split: str, pattern: str) -> List[str]:
        parts = re.split(pattern, text_to_split)
        return [p.strip() for p in parts if p and p.strip()]

    # 1. Split on markdown headers (## or ###)
    header_pattern = r'\n(?=#{2,3}\s)'
    sections = split_text(text, header_pattern)
    
    # 2 & 3. Sub-split sections if they are too large
    fine_chunks = []
    for section in sections:
        if len(section) <= chunk_size:
            fine_chunks.append(section)
        else:
            # 2. Split on paragraphs (double newlines)
            paragraphs = split_text(section, r'\n\s*\n')
            for para in paragraphs:
                if len(para) <= chunk_size:
                    fine_chunks.append(para)
                else:
                    # 3. Split on sentence boundaries (`. ` followed by uppercase) or single newline
                    sentences = split_text(para, r'\.\s+(?=[A-Z])|\n')
                    for sent in sentences:
                        fine_chunks.append(sent)

    # 4. Merge small adjacent chunks
    merged_chunks = []
    current_chunk = ""
    
    for chunk in fine_chunks:
        if not current_chunk:
            current_chunk = chunk
        elif len(current_chunk) + len(chunk) + 1 <= chunk_size:
            # Merge if they fit within chunk_size
            current_chunk += "\n\n" + chunk
        else:
            merged_chunks.append(current_chunk)
            
            # Carry over overlap to the next chunk
            if overlap > 0 and len(current_chunk) > overlap:
                carry_over = current_chunk[-overlap:]
                # Try to snap to the nearest space for a cleaner start
                space_idx = carry_over.find(' ')
                if space_idx != -1 and space_idx < len(carry_over) // 2:
                    carry_over = carry_over[space_idx+1:]
                current_chunk = carry_over + "\n\n" + chunk
            else:
                current_chunk = chunk
                
    if current_chunk:
        merged_chunks.append(current_chunk)
        
    # Build final result
    result = []
    for i, c in enumerate(merged_chunks):
        chunk_meta = metadata.copy()
        chunk_meta['chunk_index'] = i
        result.append({
            'text': c.strip(),
            'metadata': chunk_meta
        })
        
    return result


def chunk_documents(documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Batch wrapper: chunks a list of extracted documents and returns a flat list of all chunks.
    
    Args:
        documents: List of document dictionaries from the extractor.
        
    Returns:
        Flat list of chunk dictionaries with inherited metadata.
    """
    all_chunks = []
    
    for doc in documents:
        text = doc.get('text', '')
        if not text:
            continue
            
        # Standardize metadata mapping based on source type
        source_type = doc.get('source_type', '')
        metadata = {
            'source_type': source_type,
            'doc_title': doc.get('title', '')
        }
        
        if source_type == 'html':
            metadata['source_url'] = doc.get('source_url', '')
        elif source_type == 'pdf':
            metadata['source_url'] = doc.get('source', '')
            if 'page' in doc:
                metadata['page'] = doc['page']
        else:
            # Fallback
            metadata['source_url'] = doc.get('source_url', doc.get('source', ''))
            
        chunks = chunk_document(text, metadata)
        all_chunks.extend(chunks)
        
    return all_chunks
