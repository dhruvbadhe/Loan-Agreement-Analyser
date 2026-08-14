import os
import json
import sys
import random
from typing import List, Dict, Any

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from groq import Groq
from app.core.config import settings
from app.services.retriever import query_session_collection, get_collection
from app.services.generator import generate_answer

client = Groq(api_key=settings.GROQ_API_KEY)

SESSION_ID = "131fce18"

QUESTION_GENERATION_PROMPT = """
You are an expert test creator. Based ONLY on the provided Document Chunk, generate one specific question that can be answered by it, and provide the exact ground truth answer.
Document Chunk:
{chunk}
Rules:
- The question must be direct and answerable using ONLY the chunk.
- Do not reference "according to the text" or "in this chunk" in the question.
- Output ONLY a valid JSON object in this format: {{"question": "your question", "ground_truth": "exact answer"}}
"""

FAITHFULNESS_PROMPT = """
You are an expert AI grader. Your task is to evaluate the Faithfulness (groundedness) of an Answer against the provided Context.
Context:
{context}
Generated Answer:
{answer}
Rules:
- Grade how much of the Answer is supported by the Context.
- Output ONLY a valid JSON object in this format: {{"score": float, "reason": "brief explanation"}}
- The score must be a decimal between 0.0 and 1.0.
"""

RELEVANCY_PROMPT = """
You are an expert AI grader. Your task is to evaluate the Relevancy of a Generated Answer to a User Question.
User Question:
{question}
Generated Answer:
{answer}
Rules:
- Grade if the Answer directly addresses the Question, regardless of its correctness.
- Output ONLY a valid JSON object in this format: {{"score": float, "reason": "brief explanation"}}
- The score must be a decimal between 0.0 and 1.0.
"""

def query_groq_json(prompt: str) -> Dict[str, Any]:
    try:
        response = client.chat.completions.create(
            model = settings.LLM_MODEL,
            messages = [
                {"role": "system", "content": "You output JSON ONLY. Do not wrap code blocks in markdown formatting."},
                {"role": "user", "content": prompt}
            ],
            temperature = 0.0,
            response_format = {"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        return {"error": str(e)}

def generate_synthetic_test_set(session_id: str, count: int = 5) -> List[Dict[str,str]]:
    print(f"Fetching chunks from collection 'loan_{session_id}'...")
    collection = get_collection(session_id)
    db_data = collection.get()

    documents = db_data.get("documents", [])
    if not documents:
        print("Error: No documents found in database.")
        return []

    valid_chunks = [doc for doc in documents if len(doc) > 150]
    if not valid_chunks:
        valid_chunks = documents

    sample_size = min(count, len(valid_chunks))
    selected_chunks = random.sample(valid_chunks, sample_size)

    print(f"Generating {sample_size} synthetic test cases via LLM")
    test_cases = []
    for idx, chunk in enumerate(selected_chunks):
        prompt = QUESTION_GENERATION_PROMPT.format(chunk=chunk)
        qa_pair = query_groq_json(prompt)

        if "question" in qa_pair and "ground_truth" in qa_pair:
            test_cases.append(qa_pair)
            print(f"Generated Q{idx+1}: {qa_pair['question']}")

    return test_cases

def main():
    test_cases = generate_synthetic_test_set(SESSION_ID, count=5)
    if not test_cases:
        print("Failed to generate test cases. Exiting.")
        return
    print(f"\nRunning Evaluation on {len(test_cases)} dynamic test cases...\n")

    total_faithfulness = 0.0
    total_relevancy = 0.0

    for idx, case in enumerate(test_cases):
        question = case["question"]
        print(f"Test {idx+1}: {question}")

        retrieved_chunks = query_session_collection(SESSION_ID, question, top_k=3)
        context_text = "\n\n".join([c["text"] for c in retrieved_chunks])
        generated_answer = generate_answer(question, retrieved_chunks)

        f_prompt = FAITHFULNESS_PROMPT.format(context=context_text, answer=generated_answer)
        f_eval = query_groq_json(f_prompt)

        r_prompt = RELEVANCY_PROMPT.format(question=question, answer=generated_answer)
        r_eval = query_groq_json(r_prompt)

        total_faithfulness += f_eval.get("score", 0.0)
        total_relevancy += r_eval.get("score", 0.0)

        print(f"  -> Faithfulness: {f_eval.get('score')} ({f_eval.get('reason')})")
        print(f"  -> Relevancy: {r_eval.get('score')} ({r_eval.get('reason')})\n")

    num_cases = len(test_cases)
    avg_faithfulness = total_faithfulness / num_cases
    avg_relevancy = total_relevancy / num_cases
    print("=" * 40)
    print("DYNAMIC EVALUATION SUMMARY")
    print("=" * 40)
    print(f"Average Faithfulness Score: {avg_faithfulness:.2f}")
    print(f"Average Answer Relevancy  : {avg_relevancy:.2f}")
    print("=" * 40)
if __name__ == "__main__":
    main()

