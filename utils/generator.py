"""Question and Answer generation using OpenRouter API with Qwen model.
Enhanced duplicate prevention with semantic similarity checking.
"""

import os
import requests
import json
import hashlib
from typing import Optional, Set, Callable, List
import time
import re

# OpenRouter API Configuration
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
QWEN_MODEL = "qwen/qwen-2.5-72b-instruct"

# Answer length guidelines
ANSWER_GUIDELINES = {
    "1 Mark": {
        "type": "objective",
        "instruction": "Provide concise answer in 1 sentence. Max 15 words.",
        "lines": 1
    },
    "2 Mark": {
        "type": "short",
        "instruction": "Provide brief explanation in ~3 lines (40-60 words).",
        "lines": 3
    },
    "5 Mark": {
        "type": "medium",
        "instruction": "Provide detailed explanation in ~6 lines (100-150 words).",
        "lines": 6
    },
    "10 Mark": {
        "type": "long",
        "instruction": "Provide comprehensive answer in ~12 lines (200-300 words).",
        "lines": 12
    }
}


def normalize_question(question: str) -> str:
    """Normalize question text for comparison."""
    # Convert to lowercase and strip whitespace
    normalized = question.lower().strip()
    # Remove extra spaces
    normalized = ' '.join(normalized.split())
    # Remove punctuation for comparison
    normalized = re.sub(r'[^\w\s]', '', normalized)
    return normalized


def get_question_hash(question: str) -> str:
    """Generate hash for question to detect duplicates."""
    return hashlib.md5(normalize_question(question).encode()).hexdigest()


def calculate_similarity(question1: str, question2: str) -> float:
    """
    Calculate similarity between two questions.
    Returns a value between 0 and 1 (1 = identical).
    """
    # Normalize both questions
    q1 = normalize_question(question1)
    q2 = normalize_question(question2)
    
    # Quick check - if hashes match, they're identical
    if q1 == q2:
        return 1.0
    
    # Word-based similarity (Jaccard similarity)
    words1 = set(q1.split())
    words2 = set(q2.split())
    
    # Calculate intersection and union
    intersection = words1 & words2
    union = words1 | words2
    
    if len(union) == 0:
        return 0.0
    
    jaccard = len(intersection) / len(union)
    
    # Also check for key phrase overlap (more strict)
    # Extract key phrases (3+ consecutive words)
    def get_key_phrases(text, min_words=3):
        words = text.split()
        phrases = set()
        for i in range(len(words) - min_words + 1):
            phrase = ' '.join(words[i:i+min_words])
            if len(phrase) > 10:  # Only meaningful phrases
                phrases.add(phrase)
        return phrases
    
    phrases1 = get_key_phrases(q1)
    phrases2 = get_key_phrases(q2)
    
    if phrases1 and phrases2:
        phrase_intersection = phrases1 & phrases2
        phrase_union = phrases1 | phrases2
        phrase_similarity = len(phrase_intersection) / len(phrase_union) if phrase_union else 0
    else:
        phrase_similarity = 0
    
    # Combine both metrics (weighted average)
    # Give more weight to phrase similarity as it's more meaningful
    similarity = 0.4 * jaccard + 0.6 * phrase_similarity
    
    return similarity


def is_duplicate(new_question: str, existing_questions: Set[str], threshold: float = 0.7) -> bool:
    """
    Check if a question is a duplicate of any existing question.
    Uses both exact matching and semantic similarity.
    
    Args:
        new_question: The new question to check
        existing_questions: Set of existing questions
        threshold: Similarity threshold (0-1) above which questions are considered duplicates
    
    Returns:
        True if duplicate, False otherwise
    """
    new_normalized = normalize_question(new_question)
    
    # First check exact match (fast)
    if new_normalized in existing_questions:
        return True
    
    # Check hash match (fast)
    new_hash = get_question_hash(new_question)
    existing_hashes = {get_question_hash(q) for q in existing_questions}
    if new_hash in existing_hashes:
        return True
    
    # Check semantic similarity (slower but more accurate)
    for existing in existing_questions:
        similarity = calculate_similarity(new_question, existing)
        if similarity >= threshold:
            return True
    
    return False


def extract_topics_simple(syllabus: str) -> List[str]:
    """Fast topic extraction from syllabus."""
    topics = set()
    
    # Split by common delimiters
    sections = re.split(r'[-–—•]', syllabus)
    for section in sections:
        section = section.strip()
        if section and len(section) > 5 and len(section) < 80:
            topic = section.strip().rstrip('.')
            if topic and topic[0].isupper():
                topics.add(topic)
    
    # If not enough topics, use lines
    if len(topics) < 10:
        lines = syllabus.split('\n')
        for line in lines:
            line = line.strip()
            if line and len(line) > 10 and len(line) < 100:
                topics.add(line[:60])
    
    return list(topics)[:30]


def generate_question_answer(
    syllabus: str,
    question_type: str,
    academic_level: str,
    api_key: str,
    institution: Optional[str] = None,
    topic_focus: Optional[str] = None,
    question_number: int = 1,
    existing_questions: Optional[List[str]] = None
) -> dict:
    """
    Generate question and answer with duplicate prevention.
    """
    if not api_key:
        return {"error": "API key is required"}
    
    guidelines = ANSWER_GUIDELINES.get(question_type, ANSWER_GUIDELINES["2 Mark"])
    
    # Build context about existing questions to avoid
    existing_context = ""
    if existing_questions and len(existing_questions) > 0:
        # Show last 5 questions to avoid
        recent = existing_questions[-5:]
        existing_context = "\n\nAVOID these already covered questions/angles:\n"
        for i, q in enumerate(recent, 1):
            existing_context += f"{i}. {q}\n"
    
    # System prompt with emphasis on uniqueness
    system_prompt = f"""You are an expert academic assistant for {academic_level} level.
Generate UNIQUE exam questions based on syllabus.
Question Type: {question_type}
Answer: {guidelines['instruction']}

CRITICAL REQUIREMENTS:
1. Each question MUST be completely different from others
2. Cover DIFFERENT topics, concepts, and angles
3. Use different cognitive levels (define, explain, compare, analyze, evaluate)
4. Vary question formats and approaches
5. NEVER repeat similar questions or rephrase existing ones
{existing_context}"""

    # User prompt with topic focus
    topic_instruction = f"\nFocus specifically on: {topic_focus}" if topic_focus else ""
    
    user_prompt = f"""SYLLABUS:
{syllabus}

Generate question #{question_number}{topic_instruction}.

Output JSON:
{{
    "question": "unique question text",
    "answer": "answer text",
    "topic": "specific topic covered",
    "difficulty": "Easy/Medium/Hard",
    "key_concepts": ["concept1", "concept2"]
}}

IMPORTANT: This question must be UNIQUE and different from all previous questions. Cover a different aspect or topic."""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://questionbank.app",
        "X-OpenRouter-Title": "AI Question Bank"
    }
    
    # Higher temperature and penalties for variety
    payload = {
        "model": QWEN_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.85,  # Higher for more variety
        "max_tokens": 500,
        "top_p": 0.9,
        "frequency_penalty": 0.7,  # Higher to avoid repetition
        "presence_penalty": 0.7    # Encourage new topics
    }
    
    try:
        response = requests.post(
            OPENROUTER_API_URL,
            headers=headers,
            data=json.dumps(payload),
            timeout=45
        )
        response.raise_for_status()
        result = response.json()
        
        content = result["choices"][0]["message"]["content"]
        
        # Extract JSON
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            qa_data = json.loads(json_match.group())
        else:
            qa_data = {
                "question": content.split("Answer:")[0].strip() if "Answer:" in content else content,
                "answer": content.split("Answer:")[-1].strip() if "Answer:" in content else "Answer",
                "topic": topic_focus if topic_focus else "General",
                "difficulty": "Medium",
                "key_concepts": []
            }
        
        qa_data["question_type"] = question_type
        qa_data["academic_level"] = academic_level
        return qa_data
        
    except Exception as e:
        return {"error": str(e)}


def get_unique_questions_fast(
    syllabus: str,
    question_type: str,
    academic_level: str,
    api_key: str,
    num_questions: int = 10,
    institution: Optional[str] = None,
    previous_questions: Optional[Set[str]] = None,
    progress_callback: Optional[Callable[[float, str], None]] = None
) -> List[dict]:
    """
    FAST GENERATION with enhanced duplicate prevention.
    """
    if previous_questions is None:
        previous_questions = set()
    
    results = []
    all_question_texts = list(previous_questions)  # Track all generated questions
    max_attempts = num_questions * 5  # More attempts for better variety
    attempts = 0
    
    # Extract topics for variety
    available_topics = extract_topics_simple(syllabus)
    topics_used = []
    
    if progress_callback:
        progress_callback(0, f"Generating {num_questions} unique questions...")
    
    while len(results) < num_questions and attempts < max_attempts:
        attempts += 1
        
        if progress_callback:
            progress = len(results) / num_questions
            progress_callback(progress, f"Generated {len(results)}/{num_questions}...")
        
        # Select topic for variety - prioritize unused topics
        topic_focus = None
        if available_topics:
            unused_topics = [t for t in available_topics if t not in topics_used]
            if unused_topics:
                import random
                topic_focus = random.choice(unused_topics)
                topics_used.append(topic_focus)
            else:
                import random
                topic_focus = random.choice(available_topics)
                # Reset used topics to allow reuse after all covered
                if len(topics_used) > len(available_topics):
                    topics_used = [topic_focus]
        
        # Generate question with context of existing questions
        result = generate_question_answer(
            syllabus=syllabus,
            question_type=question_type,
            academic_level=academic_level,
            api_key=api_key,
            institution=institution,
            topic_focus=topic_focus,
            question_number=len(results) + 1,
            existing_questions=all_question_texts[-10:] if all_question_texts else None
        )
        
        if "error" in result:
            continue
        
        question_text = result.get('question', '')
        
        # Check for duplicates using enhanced similarity checking
        if is_duplicate(question_text, set(all_question_texts), threshold=0.65):
            # Question is too similar, skip it
            continue
        
        # Question is unique, add it
        results.append(result)
        all_question_texts.append(normalize_question(question_text))
    
    # Final progress update
    if progress_callback:
        progress_callback(1.0, f"✅ Generated {len(results)}/{num_questions} unique questions")
    
    return results


# Legacy function wrappers
def generate_question_answer_fast(*args, **kwargs):
    """Alias for generate_question_answer."""
    return generate_question_answer(*args, **kwargs)


def get_unique_questions(*args, **kwargs):
    """Legacy function - calls fast version."""
    return get_unique_questions_fast(*args, **kwargs)


def generate_multiple_questions(*args, **kwargs):
    """Legacy function."""
    return get_unique_questions_fast(*args, **kwargs)
