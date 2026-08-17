from groq import Groq
from typing import List, Dict, Any
from app.core.config import settings
import json
client = Groq(api_key=settings.GROQ_API_KEY)

SYSTEM_PROMPT = """
You are a highly precise Loan Agreement Analyst. Your job is to answer the user's question using ONLY the provided clauses in the Context.
Strict Rules:
1. Your response must be completely grounded in the Context. If the context does not contain the answer, state: "This information is not covered in the uploaded document." Do NOT make up answers.
2. For any fact you mention, you MUST cite the specific Clause ID and Page Number in your sentence (e.g., "[Clause 3.2, Page 12]").
3. Keep your explanation objective, clear, and direct. Do not assume or extrapolate legal terms beyond what is explicitly written.
"""

def build_context_string(retrieved_clauses: List[Dict[str, Any]]) -> str:
    context_parts = []
    for idx, clause in enumerate(retrieved_clauses):
        context_parts.append(
            f"--- Context Block {idx + 1} ---\n"
            f"Clause ID: {clause['clause_id']}\n"
            f"Page Number: {clause['page']}\n"
            f"Content: {clause['text']}\n"
        )

    return "\n".join(context_parts)

def generate_answer(question: str, retrieved_clauses: List[Dict[str, Any]]) -> str:
    if not retrieved_clauses:
        return "No relevant clauses found in the document to answer the question."

    context_str = build_context_string(retrieved_clauses)

    user_content = (
        f"Context:\n{context_str}\n\n"
        f"Question: {question}\n\n"
    )

    response = client.chat.completions.create(
        model=settings.LLM_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content}
        ],
        max_tokens=800,
        temperature=0.0,
    )

    return response.choices[0].message.content 

QUERY_EXPANSION_PROMPT = """
You are a legal search assistant. Your task is to generate exactly 2 alternative search queries for a user's question about a contract.
Focus on translating plain language into standard legal and financial terminology (e.g., "missed payment" -> "default", "paying off early" -> "prepayment/foreclosure").
User Question: {question}
Rules:
- Generate exactly 2 alternative search queries.
- Output ONLY a valid JSON object in this format: {{"queries": ["query 1", "query 2"]}}
"""

def expand_query(question: str) -> List[str]:
    try:
        response = client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                {"role": "system", "content": "You output JSON ONLY. Do not wrap code blocks in markdown formatting."},
                {"role": "user", "content": QUERY_EXPANSION_PROMPT.format(question=question)}
            ],
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        data = json.loads(response.choices[0].message.content)
        return data.get("queries", [])
    except Exception:
        return []