import re
from typing import List, Dict, Any
from app.services.pdf_parser import find_page_for_char

CLAUSE_PATTERN = re.compile(
    r'(?=^\s*(?:Section\s+\d+\.\d+|ARTICLE\s+\d+|\d+\.(?:\d+\.?)*|\([a-z]\)|\([ivxlc]+\))\s)',
    re.MULTILINE | re.IGNORECASE
)

def extract_clause_id(text: str) -> str:
    match = re.match(r'^\s*(?:Section\s+\d+\.\d+|ARTICLE\s+\d+|\d+\.(?:\d+\.?)*|\([a-z]\)|\([ivxlc]+\))', text, re.IGNORECASE)
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

    raw_chunks = []
    for start, end in splits:
        chunk_text = full_text[start:end].strip()
        if len(chunk_text) < 20:
             continue
        raw_chunks.append((chunk_text, start))

    if not raw_chunks:
        paragraphs = full_text.split('\n')
        current_offset = 0
        for para in paragraphs:
            para_text = para.strip()
            if len(para_text) >= 20:
                raw_chunks.append((para_text, current_offset))
            current_offset += len(para) + 1

    final_chunks = []
    max_size = 2000
    overlap = 200

    for text_block, offset in raw_chunks:
        if len(text_block) <= max_size:
            clause_id = extract_clause_id(text_block)
            page_num = find_page_for_char(offset, page_map)
            final_chunks.append({
                 "text": text_block,
                 "clause_id": clause_id,
                 "page": page_num,
                 "char_offset": offset
            })
        else:
            start_pos = 0
            while start_pos < len(text_block):
                end_pos = start_pos + max_size
                sub_text = text_block[start_pos:end_pos].strip()
                clause_id = extract_clause_id(text_block) + " (Cont.)"
                page_num = find_page_for_char(offset + start_pos, page_map)
                final_chunks.append({
                     "text": sub_text,
                     "clause_id": clause_id,
                     "page": page_num,
                     "char_offset": offset + start_pos
                })
                start_pos += (max_size - overlap)

    return final_chunks