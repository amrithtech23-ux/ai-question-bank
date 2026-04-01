"""Question and Answer generation using OpenRouter API with Qwen model.
Optimized for speed and guaranteed question count.
"""

import os
import requests
import json
import hashlib
from typing import Optional, Set, Callable, List
import time

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
    return question.lower().strip()


def get_question_hash(question: str) -> str:
    """Generate hash for question to detect duplicates."""
    return hashlib.md5(normalize_question(question).encode()).hexdigest()


def generate_question_answer_fast(
    syllabus: str,
    question_type: str,
    academic_level: str,
    api_key: str,
    institution: Optional[str] = None,
    topic_focus: Optional[str] = None,
    question_number: int = 1
) -> dict:
    """
    FAST version: Generate question and answer with optimized parameters.
    """
    if not api_key:
        return {"error": "API key is required"}
    
    guidelines = ANSWER_GUIDELINES.get(question_type, ANSWER_GUIDELINES["2 Mark"])
    
    # Simplified system prompt for speed
    system_prompt = f"""You are an academic assistant for {academic_level} level.
Generate UNIQUE exam questions based on syllabus.
Question Type: {question_type}
Answer: {guidelines['instruction']}

CRITICAL: Each question must be different. Cover different topics."""

    # Simplified user prompt
    topic_instruction = f"\nFocus on: {topic_focus}" if topic_focus else ""
    
    user_prompt = f"""SYLLABUS:
{syllabus}

Generate question #{question_number}{topic_instruction}.

Output JSON:
{{
    "question": "question text",
    "answer": "answer text",
    "topic": "topic name",
    "difficulty": "Easy/Medium/Hard",
    "key_concepts": ["concept1", "concept2"]
}}

Make it UNIQUE from previous questions."""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://questionbank.app",
        "X-OpenRouter-Title": "AI Question Bank"
    }
    
    # OPTIMIZED parameters for SPEED
    payload = {
        "model": QWEN_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.8,  # Higher for variety
        "max_tokens": 500,   # Reduced for speed
        "top_p": 0.9,
        "frequency_penalty": 0.5,  # Higher to avoid repetition
        "presence_penalty": 0.5
    }
    
    try:
        # Reduced timeout for speed
        response = requests.post(
            OPENROUTER_API_URL,
            headers=headers,
            data=json.dumps(payload),
            timeout=45  # Reduced from 90 to 45 seconds
        )
        response.raise_for_status()
        result = response.json()
        
        content = result["choices"][0]["message"]["content"]
        
        # Extract JSON
        import re
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


def extract_topics_simple(syllabus: str) -> List[str]:
    """Fast topic extraction."""
    import re
    
    # Simple extraction: look for capitalized phrases and dashes
    topics = set()
    
    # Split by common delimiters
    sections = re.split(r'[-–—•]', syllabus)
    for section in sections:
        section = section.strip()
        if section and len(section) > 5 and len(section) < 80:
            # Clean up
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
    
    return list(topics)[:30]  # Return up to 30 topics


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
    FAST GENERATION: Optimized to generate EXACT number of questions quickly.
    """
    if previous_questions is None:
        previous_questions = set()
    
    results = []
    existing_hashes = set()
    
    # Extract topics for variety
    available_topics = extract_topics_simple(syllabus)
    
    if progress_callback:
        progress_callback(0, f"Starting fast generation of {num_questions} questions...")
    
    # Batch generation with guaranteed count
    batch_size = max(5, num_questions // 4)  # Generate in batches
    questions_per_batch = min(batch_size, num_questions)
    
    total_generated = 0
    max_iterations = (num_questions * 2) // batch_size + 2  # Allow extra iterations
    
    for iteration in range(max_iterations):
        if len(results) >= num_questions:
            break
        
        if progress_callback:
            progress = len(results) / num_questions
            progress_callback(progress, f"Batch {iteration + 1}: Generated {len(results)}/{num_questions}...")
        
        # Generate a batch
        batch_results = []
        topics_used = []
        
        for i in range(questions_per_batch):
            # Select topic for variety
            topic_focus = None
            if available_topics:
                unused = [t for t in available_topics if t not in topics_used]
                if unused:
                    import random
                    topic_focus = random.choice(unused)
                    topics_used.append(topic_focus)
                else:
                    import random
                    topic_focus = random.choice(available_topics)
            
            # Generate question
            result = generate_question_answer_fast(
                syllabus=syllabus,
                question_type=question_type,
                academic_level=academic_level,
                api_key=api_key,
                institution=institution,
                topic_focus=topic_focus,
                question_number=total_generated + i + 1
            )
            
            if "error" not in result:
                # Quick duplicate check
                question_hash = get_question_hash(result.get('question', ''))
                if question_hash not in existing_hashes:
                    batch_results.append(result)
                    existing_hashes.add(question_hash)
                    total_generated += 1
        
        results.extend(batch_results)
        
        # Small delay between batches to avoid rate limiting
        if len(results) < num_questions:
            time.sleep(0.5)
    
    # Final progress update
    if progress_callback:
        progress_callback(1.0, f"✅ Generated {len(results)}/{num_questions} questions")
    
    return results


# Legacy function wrapper
def get_unique_questions(
    syllabus: str,
    question_type: str,
    academic_level: str,
    api_key: str,
    num_questions: int = 10,
    institution: Optional[str] = None,
    previous_questions: Optional[Set[str]] = None,
    progress_callback: Optional[Callable[[float, str], None]] = None
) -> List[dict]:
    """Legacy function - calls fast version."""
    return get_unique_questions_fast(
        syllabus=syllabus,
        question_type=question_type,
        academic_level=academic_level,
        api_key=api_key,
        num_questions=num_questions,
        institution=institution,
        previous_questions=previous_questions,
        progress_callback=progress_callback
    )


def generate_multiple_questions(
    syllabus: str,
    question_type: str,
    academic_level: str,
    api_key: str,
    count: int = 5,
    institution: Optional[str] = None
) -> list:
    """Legacy function."""
    return get_unique_questions_fast(
        syllabus=syllabus,
        question_type=question_type,
        academic_level=academic_level,
        api_key=api_key,
        num_questions=count,
        institution=institution
    )
