"""Question and Answer generation - Optimized for SPEED and COMPLETENESS.
Ensures requested number of questions are generated.
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
    normalized = question.lower().strip()
    normalized = ' '.join(normalized.split())
    normalized = re.sub(r'[^\w\s]', '', normalized)
    return normalized


def get_question_hash(question: str) -> str:
    """Generate hash for question."""
    return hashlib.md5(normalize_question(question).encode()).hexdigest()


def extract_key_terms(question: str) -> Set[str]:
    """Extract key technical terms from question."""
    stop_words = {
        'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
        'may', 'might', 'must', 'shall', 'can', 'need', 'to', 'of', 'in',
        'for', 'on', 'with', 'at', 'by', 'from', 'as', 'into', 'through',
        'before', 'after', 'above', 'below', 'between', 'under', 'again',
        'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how',
        'all', 'each', 'few', 'more', 'most', 'other', 'some', 'such',
        'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too',
        'very', 'just', 'and', 'but', 'if', 'or', 'because', 'until',
        'while', 'although', 'what', 'which', 'this', 'that', 'these',
        'those', 'am', 'being', 'has', 'having'
    }
    
    words = re.findall(r'\b[a-z]{3,}\b', question.lower())
    key_terms = {word for word in words if word not in stop_words}
    return key_terms


def is_simple_duplicate(new_question: str, existing_questions: List[str]) -> bool:
    """Simple and fast duplicate check."""
    new_normalized = normalize_question(new_question)
    new_hash = get_question_hash(new_question)
    
    for existing in existing_questions:
        # Exact match
        if normalize_question(existing) == new_normalized:
            return True
        
        # Hash match
        if get_question_hash(existing) == new_hash:
            return True
    
    return False


def extract_topics_from_syllabus(syllabus: str) -> List[str]:
    """Extract topics from syllabus."""
    topics = []
    
    # Method 1: Look for Topic: header
    topic_match = re.search(r'Topic:\s*(.+?)(?=\n\n|\nInstitution)', syllabus, re.IGNORECASE)
    if topic_match:
        topics.append(topic_match.group(1).strip())
    
    # Method 2: Split by common delimiters
    sections = re.split(r'[-–—•]', syllabus)
    for section in sections:
        section = section.strip()
        if section and 15 < len(section) < 150:
            # Clean up
            section = section.strip().rstrip('.,;:')
            if section and not section.lower().startswith('institution'):
                topics.append(section)
    
    # Method 3: Use lines
    lines = syllabus.split('\n')
    for line in lines:
        line = line.strip()
        if line and len(line) > 20 and len(line) < 200:
            if not line.lower().startswith(('topic:', 'institution')):
                topics.append(line[:100])
    
    # Remove duplicates and return
    unique_topics = list(set(topics))
    return unique_topics[:50]


def generate_single_question(
    syllabus: str,
    question_type: str,
    academic_level: str,
    api_key: str,
    topic_focus: Optional[str] = None,
    question_number: int = 1,
    existing_questions: Optional[List[str]] = None
) -> Optional[dict]:
    """Generate a single question quickly."""
    if not api_key:
        return None
    
    guidelines = ANSWER_GUIDELINES.get(question_type, ANSWER_GUIDELINES["2 Mark"])
    
    # Build context
    avoid_context = ""
    if existing_questions and len(existing_questions) > 0:
        avoid_context = "\n\nAvoid repeating these topics:\n"
        for q in existing_questions[-3:]:
            avoid_context += f"- {q}\n"
    
    topic_instruction = f"\nFocus on: {topic_focus}" if topic_focus else ""
    
    system_prompt = f"""You are an academic examiner for {academic_level} level.
Create ONE unique exam question.
Type: {question_type}
Answer: {guidelines['instruction']}

Make it different from previous questions.{avoid_context}"""

    user_prompt = f"""SYLLABUS:
{syllabus}

Generate question #{question_number}{topic_instruction}.

Output JSON:
{{
    "question": "your question",
    "answer": "answer",
    "topic": "topic covered",
    "difficulty": "Easy/Medium/Hard",
    "key_concepts": ["concept1"]
}}"""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://questionbank.app",
        "X-OpenRouter-Title": "AI Question Bank"
    }
    
    payload = {
        "model": QWEN_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 400,
        "top_p": 0.9
    }
    
    try:
        response = requests.post(
            OPENROUTER_API_URL,
            headers=headers,
            data=json.dumps(payload),
            timeout=30
        )
        response.raise_for_status()
        result = response.json()
        
        content = result["choices"][0]["message"]["content"]
        
        # Extract JSON
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            qa_data = json.loads(json_match.group())
            qa_data["question_type"] = question_type
            qa_data["academic_level"] = academic_level
            return qa_data
        else:
            return None
        
    except Exception as e:
        print(f"Error generating question: {e}")
        return None


def generate_batch_questions(
    syllabus: str,
    question_type: str,
    academic_level: str,
    api_key: str,
    batch_size: int = 5,
    institution: Optional[str] = None,
    existing_questions: Optional[List[dict]] = None,
    available_topics: Optional[List[str]] = None
) -> List[dict]:
    """Generate multiple questions in ONE API call."""
    if not api_key:
        return []
    
    guidelines = ANSWER_GUIDELINES.get(question_type, ANSWER_GUIDELINES["2 Mark"])
    
    # Build context
    existing_context = ""
    if existing_questions and len(existing_questions) > 0:
        existing_context = "\n\nAlready covered (avoid these):\n"
        for i, q in enumerate(existing_questions[-5:], 1):
            existing_context += f"{i}. {q.get('question', '')}\n"
    
    # Topics context
    topics_context = ""
    if available_topics and len(available_topics) > 0:
        import random
        sample_topics = random.sample(available_topics, min(10, len(available_topics)))
        topics_context = f"\nCover different topics from: {', '.join(sample_topics)}"
    
    system_prompt = f"""You are an expert academic examiner for {academic_level} level.
Create {batch_size} UNIQUE exam questions.

Question Type: {question_type}
Answer: {guidelines['instruction']}

Requirements:
1. Each question must cover a DIFFERENT topic
2. Use different question formats
3. No repetition{topics_context}
{existing_context}"""

    user_prompt = f"""SYLLABUS:
{syllabus}

Generate {batch_size} unique questions in JSON array format:

[
    {{
        "question": "question 1",
        "answer": "answer 1",
        "topic": "topic 1",
        "difficulty": "Easy/Medium/Hard",
        "key_concepts": ["concept1", "concept2"]
    }},
    {{
        "question": "question 2",
        "answer": "answer 2",
        "topic": "topic 2",
        "difficulty": "Easy/Medium/Hard",
        "key_concepts": ["concept1"]
    }}
]

Make each question cover a different topic from the syllabus."""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://questionbank.app",
        "X-OpenRouter-Title": "AI Question Bank"
    }
    
    payload = {
        "model": QWEN_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 2500,
        "top_p": 0.9,
        "frequency_penalty": 0.3,
        "presence_penalty": 0.3
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
        
        # Extract JSON array
        json_match = re.search(r'\[[\s\S]*\]', content)
        if json_match:
            questions_array = json.loads(json_match.group())
            
            # Add metadata
            for q in questions_array:
                q["question_type"] = question_type
                q["academic_level"] = academic_level
            
            return questions_array
        else:
            return []
        
    except Exception as e:
        print(f"Batch generation error: {e}")
        return []


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
    Generate EXACT number of questions requested using hybrid approach.
    """
    if previous_questions is None:
        previous_questions = set()
    
    results = []
    all_question_texts = list(previous_questions)
    
    available_topics = extract_topics_from_syllabus(syllabus)
    
    if progress_callback:
        progress_callback(0, f"Generating {num_questions} questions...")
    
    # Strategy: Use batch generation first, then fill gaps with single generation
    batch_size = 5
    questions_generated = 0
    max_attempts = num_questions * 3  # Safety limit
    total_attempts = 0
    
    # Phase 1: Batch generation (faster)
    while questions_generated < num_questions and total_attempts < max_attempts:
        batch_num = questions_generated // batch_size + 1
        
        if progress_callback:
            progress = questions_generated / num_questions
            progress_callback(progress, f"Batch {batch_num}: {questions_generated}/{num_questions}...")
        
        # Calculate how many we need
        remaining = num_questions - questions_generated
        current_batch_size = min(batch_size, remaining)
        
        # Generate batch
        batch_questions = generate_batch_questions(
            syllabus=syllabus,
            question_type=question_type,
            academic_level=academic_level,
            api_key=api_key,
            batch_size=current_batch_size,
            institution=institution,
            existing_questions=results,
            available_topics=available_topics
        )
        
        if not batch_questions:
            # Batch failed, try single generation
            break
        
        # Add unique questions from batch
        for q in batch_questions:
            if questions_generated >= num_questions:
                break
            
            question_text = q.get('question', '')
            if not is_simple_duplicate(question_text, all_question_texts):
                results.append(q)
                all_question_texts.append(question_text)
                questions_generated += 1
        
        total_attempts += 1
        time.sleep(0.2)  # Small delay
    
    # Phase 2: Fill gaps with single generation if needed
    while questions_generated < num_questions and total_attempts < max_attempts:
        total_attempts += 1
        
        if progress_callback:
            progress = questions_generated / num_questions
            progress_callback(progress, f"Filling gap: {questions_generated}/{num_questions}...")
        
        # Select topic for variety
        topic_focus = None
        if available_topics:
            import random
            # Prioritize less used topics
            used_topics = [q.get('topic', '') for q in results]
            unused = [t for t in available_topics if t not in used_topics]
            if unused:
                topic_focus = random.choice(unused)
            else:
                topic_focus = random.choice(available_topics)
        
        # Generate single question
        question = generate_single_question(
            syllabus=syllabus,
            question_type=question_type,
            academic_level=academic_level,
            api_key=api_key,
            topic_focus=topic_focus,
            question_number=questions_generated + 1,
            existing_questions=all_question_texts
        )
        
        if question:
            question_text = question.get('question', '')
            if not is_simple_duplicate(question_text, all_question_texts):
                results.append(question)
                all_question_texts.append(question_text)
                questions_generated += 1
        
        time.sleep(0.1)
    
    # Final progress
    if progress_callback:
        progress_callback(1.0, f"✅ Generated {len(results)}/{num_questions} questions")
    
    return results


# Legacy function wrappers
def generate_question_answer_fast(*args, **kwargs):
    """Alias."""
    return get_unique_questions_fast(*args, **kwargs)


def get_unique_questions(*args, **kwargs):
    """Legacy function."""
    return get_unique_questions_fast(*args, **kwargs)


def generate_multiple_questions(*args, **kwargs):
    """Legacy function."""
    return get_unique_questions_fast(*args, **kwargs)
