import fitz
from typing import Tuple, Dict

def parse_pdf(file_path: str) -> Tuple[str, Dict[int, str]]:
    doc = fitz.open(file_path)
    full_text = ""
    page_map = {}

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        page_text = page.get_text("text")
        current_start_index = len(full_text)
        page_map[current_start_index] = page_num + 1
        full_text += page_text

    doc.close()
    return full_text, page_map

def find_page_for_char(char_index: int, page_map: Dict[int, int]) -> int:
    sorted_starts = sorted(page_map.keys())

    assigned_page = 1
    for start in sorted_starts:
        if char_index >= start:
            assigned_page = page_map[start]
        else:
            break
    return assigned_page