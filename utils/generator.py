"""Question and Answer generation using OpenRouter API with Qwen model.
Enhanced duplicate prevention with 90% similarity threshold.
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
    # Remove common question starters to focus on core content
    normalized = re.sub(r'^(what is|what are|explain|describe|define|discuss|list|state|why|how|when|where)\s+', '', normalized)
    return normalized


def get_question_hash(question: str) -> str:
    """Generate hash for question to detect exact duplicates."""
    return hashlib.md5(normalize_question(question).encode()).hexdigest()


def extract_key_terms(question: str) -> Set[str]:
    """Extract key technical terms from question."""
    # Remove common words
    stop_words = {
        'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
        'may', 'might', 'must', 'shall', 'can', 'need', 'dare', 'ought', 'used',
        'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from', 'as', 'into',
        'through', 'during', 'before', 'after', 'above', 'below', 'between',
        'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when',
        'where', 'why', 'how', 'all', 'each', 'few', 'more', 'most', 'other',
        'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than',
        'too', 'very', 'just', 'and', 'but', 'if', 'or', 'because', 'until',
        'while', 'although', 'though', 'after', 'before', 'about', 'against'
    }
    
    # Extract words
    words = re.findall(r'\b[a-z]{3,}\b', question.lower())
    
    # Filter out stop words and keep technical terms
    key_terms = {word for word in words if word not in stop_words}
    
    return key_terms


def calculate_similarity(question1: str, question2: str) -> float:
    """
    Calculate comprehensive similarity between two questions.
    Returns a value between 0 and 1 (1 = identical).
    """
    # Normalize both questions
    q1_norm = normalize_question(question1)
    q2_norm = normalize_question(question2)
    
    # Exact match check
    if q1_norm == q2_norm:
        return 1.0
    
    # Extract key terms
    terms1 = extract_key_terms(q1_norm)
    terms2 = extract_key_terms(q2_norm)
    
    # Check for shared technical terms (very important)
    shared_terms = terms1 & terms2
    
    # If 3+ key terms match, likely similar
    if len(shared_terms) >= 3:
        term_overlap = len(shared_terms) / min(len(terms1), len(terms2))
        if term_overlap > 0.7:
            return 0.85 + (term_overlap * 0.15)  # 85-100% similarity
    
    # Jaccard similarity on normalized text
    words1 = set(q1_norm.split())
    words2 = set(q2_norm.split())
    
    if not words1 or not words2:
        return 0.0
    
    intersection = words1 & words2
    union = words1 | words2
    jaccard = len(intersection) / len(union)
    
    # Key phrase similarity (3-5 word sequences)
    def get_ngrams(text, n=3):
        words = text.split()
        return {' '.join(words[i:i+n]) for i in range(len(words)-n+1)}
    
    trigrams1 = get_ngrams(q1_norm, 3)
    trigrams2 = get_ngrams(q2_norm, 3)
    
    if trigrams1 and trigrams2:
        trigram_overlap = len(trigrams1 & trigrams2) / max(len(trigrams1), len(trigrams2))
    else:
        trigram_overlap = 0
    
    # Check if questions share the same main topic
    # (first 3-5 words often contain the topic)
    q1_start = ' '.join(q1_norm.split()[:5])
    q2_start = ' '.join(q2_norm.split()[:5])
    start_similarity = 1.0 if q1_start == q2_start else 0.0
    
    # Combined similarity score
    # Weight: 40% word overlap, 40% phrase overlap, 20% topic start
    similarity = (0.4 * jaccard) + (0.4 * trigram_overlap) + (0.2 * start_similarity)
    
    # Boost similarity if key terms overlap significantly
    if len(shared_terms) >= 2:
        similarity = min(1.0, similarity + 0.2)
    
    return similarity


def is_duplicate(new_question: str, existing_questions: Set[str], threshold: float = 0.90) -> tuple:
    """
    Check if a question is a duplicate of any existing question.
    Uses 90% similarity threshold for strict duplicate detection.
    
    Returns:
        tuple: (is_duplicate: bool, similarity_score: float, matched_question: str)
    """
    new_normalized = normalize_question(new_question)
    
    # Track highest similarity found
    max_similarity = 0.0
    matched_question = ""
    
    # First check exact match (fast)
    if new_normalized in existing_questions:
        return True, 1.0, "Exact match found"
    
    # Check against all existing questions
    for existing in existing_questions:
        similarity = calculate_similarity(new_question, existing)
        
        if similarity > max_similarity:
            max_similarity = similarity
            matched_question = existing
        
        if similarity >= threshold:
            return True, similarity, existing
    
    return False, max_similarity, matched_question


def extract_topics_from_syllabus(syllabus: str) -> List[str]:
    """Extract detailed topics from syllabus with better granularity."""
    topics = set()
    
    # Pattern 1: Topic headers
    topic_headers = re.findall(r'Topic:\s*(.+?)(?=\n\n|\n[A-Z]|\Z)', syllabus, re.IGNORECASE)
    topics.update(topic_headers)
    
    # Pattern 2: Items separated by dashes/bullets
    sections = re.split(r'[-–—•]', syllabus)
    for section in sections:
        section = section.strip()
        if section and 10 < len(section) < 100:
            topics.add(section.strip())
    
    # Pattern 3: Lines that look like topics (capitalized, moderate length)
    lines = syllabus.split('\n')
    for line in lines:
        line = line.strip()
        if line and not line.startswith('Topic:') and not line.startswith('Institution'):
            # Check if it's a meaningful topic line
            words = line.split()
            if 3 <= len(words) <= 15 and any(word[0].isupper() for word in words[:3]):
                topics.add(line[:80])
    
    # Pattern 4: Extract compound topics (A - B - C format)
    compound_pattern = re.findall(r'([A-Z][a-zA-Z\s]+)\s*[-–—]\s*([A-Z][a-zA-Z\s]+)', syllabus)
    for match in compound_pattern:
        topics.update(match)
    
    # Clean up topics
    cleaned_topics = set()
    for topic in topics:
        topic = topic.strip().rstrip('.,;:')
        if len(topic) > 5:
            cleaned_topics.add(topic)
    
    return list(cleaned_topics)[:50]  # Return up to 50 topics


def generate_question_answer(
    syllabus: str,
    question_type: str,
    academic_level: str,
    api_key: str,
    institution: Optional[str] = None,
    topic_focus: Optional[str] = None,
    question_number: int = 1,
    existing_questions: Optional[List[dict]] = None,
    used_topics: Optional[List[str]] = None
) -> dict:
    """
    Generate question and answer with strict duplicate prevention.
    """
    if not api_key:
        return {"error": "API key is required"}
    
    guidelines = ANSWER_GUIDELINES.get(question_type, ANSWER_GUIDELINES["2 Mark"])
    
    # Build detailed context about existing questions
    existing_context = ""
    if existing_questions and len(existing_questions) > 0:
        existing_context = "\n\n🚫 DO NOT create questions similar to these (already covered):\n"
        for i, q in enumerate(existing_questions[-8:], 1):  # Last 8 questions
            existing_context += f"{i}. [{q.get('topic', 'General')}] {q.get('question', '')}\n"
    
    # Build context about used topics
    used_topics_context = ""
    if used_topics and len(used_topics) > 0:
        used_topics_context = f"\n\n📌 AVOID these topics (already covered): {', '.join(used_topics[-5:])}"
    
    # System prompt with strong emphasis on uniqueness
    system_prompt = f"""You are an expert academic examiner for {academic_level} level.
Your task is to create UNIQUE, NON-REPETITIVE exam questions.

Question Type: {question_type}
Answer Format: {guidelines['instruction']}

⚠️ CRITICAL UNIQUENESS REQUIREMENTS:
1. Each question MUST cover a DIFFERENT topic/concept
2. NEVER ask about the same concept twice, even with different wording
3. Use DIFFERENT cognitive levels: define, explain, compare, analyze, evaluate, apply
4. Vary question formats and approaches
5. If a topic has been covered, move to a COMPLETELY different topic
6. Check the list of already covered questions and topics carefully
{used_topics_context}
{existing_context}

Think: "Has this concept been asked before?" If YES, choose a different concept."""

    # User prompt
    topic_instruction = f"\n📍 Focus on this specific topic: {topic_focus}" if topic_focus else ""
    
    user_prompt = f"""SYLLABUS CONTENT:
{syllabus}

TASK: Generate question #{question_number}{topic_instruction}

🎯 REQUIREMENTS:
- Must be UNIQUE and different from all previous questions
- Cover a topic/concept NOT yet covered
- Use a different question format/approach
- Match the {question_type} answer length

Output JSON:
{{
    "question": "your unique question here",
    "answer": "answer following the guidelines",
    "topic": "specific topic from syllabus",
    "difficulty": "Easy/Medium/Hard",
    "key_concepts": ["concept1", "concept2"]
}}

⚡ IMPORTANT: Before finalizing, ask yourself:
1. Is this asking about something already covered?
2. Am I using different words but same concept?
3. Is this truly a NEW angle/topic?

If ANY answer is YES, choose a different topic!"""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://questionbank.app",
        "X-OpenRouter-Title": "AI Question Bank"
    }
    
    # Optimized parameters for variety
    payload = {
        "model": QWEN_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.9,  # Very high for maximum variety
        "max_tokens": 600,
        "top_p": 0.95,
        "frequency_penalty": 0.9,  # Very high to prevent repetition
        "presence_penalty": 0.9,    # Very high to encourage new topics
        "top_k": 40  # Sample from more diverse options
    }
    
    try:
        response = requests.post(
            OPENROUTER_API_URL,
            headers=headers,
            data=json.dumps(payload),
            timeout=60
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
    Generate questions with 90% duplicate detection accuracy.
    """
    if previous_questions is None:
        previous_questions = set()
    
    results = []
    all_question_texts = list(previous_questions)
    used_topics = []
    
    # Extract all available topics
    available_topics = extract_topics_from_syllabus(syllabus)
    
    if progress_callback:
        progress_callback(0, f"Generating {num_questions} unique questions (90% accuracy)...")
    
    max_attempts = num_questions * 8  # More attempts for strict uniqueness
    attempts = 0
    consecutive_failures = 0
    
    while len(results) < num_questions and attempts < max_attempts:
        attempts += 1
        
        if progress_callback:
            progress = len(results) / num_questions
            progress_callback(progress, f"Generated {len(results)}/{num_questions} (attempt {attempts})...")
        
        # Smart topic selection - prioritize unused topics
        topic_focus = None
        if available_topics:
            unused = [t for t in available_topics if t not in used_topics]
            if unused:
                import random
                topic_focus = random.choice(unused)
                used_topics.append(topic_focus)
            else:
                # All topics used, allow reuse but with different angle
                import random
                topic_focus = random.choice(available_topics)
        
        # Generate question with full context
        result = generate_question_answer(
            syllabus=syllabus,
            question_type=question_type,
            academic_level=academic_level,
            api_key=api_key,
            institution=institution,
            topic_focus=topic_focus,
            question_number=len(results) + 1,
            existing_questions=results,
            used_topics=used_topics
        )
        
        if "error" in result:
            consecutive_failures += 1
            if consecutive_failures > 10:
                break
            continue
        
        question_text = result.get('question', '')
        
        # Strict duplicate check with 90% threshold
        is_dup, similarity, matched = is_duplicate(question_text, set(all_question_texts), threshold=0.90)
        
        if is_dup:
            # Too similar, skip and try again
            consecutive_failures = 0
            continue
        
        # Question is unique enough, add it
        results.append(result)
        all_question_texts.append(normalize_question(question_text))
        consecutive_failures = 0
    
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
