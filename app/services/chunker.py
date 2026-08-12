import re
from typing import List, Dict, Any
from app.services.pdf_parser import find_page_for_char

CLAUSE_PATTERN = re.compile(
    r'(?=^\s*(?:\d+\.(?:\d+\.?)*|\([a-z]\)|\([ivxlc]+\))\s)',
    re.MULTILINE
)

def extract_clause_id(text: str) -> str:
    match = re.match(r'^\s*(?:\d+\.(?:\d+\.?)*|\([a-z]\)|\([ivxlc]+\))', text)
    if match:
        return match.group(0).strip()
    return "N/A"

def chunk_by_clause(full_text: str, page_map: Dict[int, int]) -> List[Dict[str, Any]]:
    splits = []
    last_end = 0

    for match in CLAUSE_PATTERN.finditer(full_text):
            start = match.start()
            if start > last_end:
                splits.append((last_end, start))
            last_end = match.end()

    if last_end < len(full_text):
        splits.append((last_end, len(full_text)))

    chunks = []
    for start, end in splits:
        chunk_text = full_text[start:end].strip()
        if len(chunk_text) < 20:
             continue

        clause_id = extract_clause_id(chunk_text)

        page_num = find_page_for_char(start, page_map)

        chunks.append({
             "text" : chunk_text,
             "clause_id" : clause_id,
             "page" : page_num,
             "char_offset" : start
        })

    if not chunks:
        paragraphs = full_text.split('\n\n')
        current_offset = 0
        for para in paragraphs:
            para_text = para.strip()
            if len(para_text) >= 20:
                page_num = find_page_for_char(current_offset, page_map)
                chunks.append({
                    "text": para_text,
                    "clause_id": "General",
                    "page": page_num,
                    "char_offset": current_offset
                })
            current_offset += len(para) + 2
    return chunks
            
         

    