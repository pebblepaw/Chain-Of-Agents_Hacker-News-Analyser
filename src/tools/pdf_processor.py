'''
Downloads the PDFs, extracts texts in chunks usig COA 
'''

import httpx
import tempfile
import os
from dataclasses import dataclass
from src.config import CHUNK_OVERLAP_TOKENS, CHUNK_SIZE_TOKENS

@dataclass
class PDFChunk: # any chunk of text form the PDF
    chunk_index: int
    total_chunks: int
    text: str
    page_start: int
    page_end: int

def download_arxiv_pdf(arxiv_id: str) -> bytes: 

    arxiv_id = arxiv_id.replace("arxiv:","").strip()
    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"

    response = httpx.get(pdf_url, timeout=60.0, follow_redirects = True)
    response.raise_for_status()

    return response.content

def extract_text_from_pdf(pdf_bytes: bytes) -> list[tuple[int,str]]: 

    '''
    extracts text from PDF Bytes, returning list of (page_number, text) tuples
    uses pymupdf(fitz) for extraction. 
    '''

    try: 
        import fitz # PyMuPDF
    except ImportError:
        raise ImportError("Please install PyMuPDF to extract text from PDFs: pip install pymupdf")
    

    pages = []

    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc: 
        for page_num, page in enumerate(doc, start=1): 
            text = page.get_text()
            if text.strip(): # if not empty
                pages.append((page_num, text))

    return pages


## Potentially we can improve this by chunking based on sections, 
## but definitely won't be that proportionatea cross sections/papers ***

def chunk_text(
        pages: list[tuple[int,str]],
        chunk_size: int = CHUNK_SIZE_TOKENS,
        overlap: int = CHUNK_OVERLAP_TOKENS
        ) -> list[PDFChunk]:
    

    # COmbine all pages into a single text, w boundaries
    combined_text = ""
    page_boundaries = [] # char position, page_number 

    for page_num, text in pages: 
        page_boundaries.append((len(combined_text),page_num)) # adds the current char as -> boundary
        combined_text += text + "\n\n" # separate pages

    # Chunk based on word count, so we split based on word
    # potentially improve here *** 

     # Simple word-based tokenization (approximate)
    words = combined_text.split()
    
    # Approximate tokens (words * 1.3 is a rough estimate)
    words_per_chunk = int(chunk_size / 1.3)
    words_overlap = int(overlap / 1.3)
    
    chunks = []
    start_idx = 0
    chunk_index = 0

    while start_idx < len(words):

        # chunking the words
        end_idx = min(start_idx + words_per_chunk, len(words))
        chunk_words = words[start_idx:end_idx]
        chunk_text = " ".join(chunk_words)

        # Find which pages the chunk starts/ends at
        chunk_char_start = len(" ".join(words[:start_idx]))
        chunk_char_end = chunk_char_start + len(chunk_text)

        page_start = 1
        page_end = 1
        
        # simple iteration thru the pages
        # char_pos is no. of characters up till the start of that page
        # e.g. page 1 is "0" for char_pos

        for char_pos, page_num in page_boundaries: 
            if char_pos <= chunk_char_start: 
                page_start = page_num
            if char_pos <= chunk_char_end: 
                page_end = page_num
            else: 
                break
        
        chunks.append(PDFChunk(
            chunk_index=chunk_index,
            total_chunks=-1, # placeholder, will be set after all chunks created
            text=chunk_text,
            page_start=page_start,  
            page_end=page_end
        ))

        chunk_index +=1 
        start_idx = end_idx - words_overlap  # move back by overlap

        if end_idx >= (len(words)):
            break

    # Update total_chunks for each chunk
    total_chunks = len(chunks)

    for chunk in chunks:
        chunk.total_chunks = total_chunks

    return chunks

def process_arxiv_pdf(arxiv_id: str) -> list[PDFChunk]:
    '''
    Downloads the arxiv PDF, extracts text, chunks it, and returns list of PDFChunk
    '''

    print(f"Downloading PDF for arxiv:{arxiv_id}...")
    pdf_bytes = download_arxiv_pdf(arxiv_id)
    print(f"Downloaded {len(pdf_bytes) / 1024:.1f} KB")
    
    print("Extracting text...")
    pages = extract_text_from_pdf(pdf_bytes)
    print(f"Extracted {len(pages)} pages")
    
    print("Chunking...")
    chunks = chunk_text(pages)
    print(f"Created {len(chunks)} chunks")
    
    return chunks

# Sanity test

# Quick test
if __name__ == "__main__":
    # Test with the famous "Attention Is All You Need" paper
    chunks = process_arxiv_pdf("1706.03762")
    
    print(f"\n{'='*60}")
    print(f"Total chunks: {len(chunks)}")
    
    for chunk in chunks[:2]:  # Show first 2 chunks
        print(f"\n--- Chunk {chunk.chunk_index + 1}/{chunk.total_chunks} ---")
        print(f"Pages: {chunk.page_start}-{chunk.page_end}")
        print(f"Text preview: {chunk.text[:300]}...")
