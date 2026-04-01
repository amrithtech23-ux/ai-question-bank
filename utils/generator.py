"""Question and Answer generation using OpenRouter API with Qwen model."""

import os
import requests
import json
import hashlib
from typing import Optional, Set, Callable, List, Tuple

# OpenRouter API Configuration
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
# Qwen model via OpenRouter - using latest stable version
QWEN_MODEL = "qwen/qwen-2.5-72b-instruct"

# Answer length guidelines based on mark type
ANSWER_GUIDELINES = {
    "1 Mark": {
        "type": "objective",
        "instruction": "Provide a concise, direct answer in 1 sentence or a single word/phrase. Maximum 15 words.",
        "lines": 1
    },
    "2 Mark": {
        "type": "short",
        "instruction": "Provide a brief explanation in approximately 3 lines (40-60 words).",
        "lines": 3
    },
    "5 Mark": {
        "type": "medium",
        "instruction": "Provide a detailed explanation in approximately 6 lines (100-150 words) with key points.",
        "lines": 6
    },
    "10 Mark": {
        "type": "long",
        "instruction": "Provide a comprehensive answer in approximately 12 lines (200-300 words) with examples, structure, and conclusion.",
        "lines": 12
    }
}


def normalize_question(question: str) -> str:
    """Normalize question text for comparison."""
    return question.lower().strip()


def get_question_hash(question: str) -> str:
    """Generate hash for question to detect duplicates."""
    return hashlib.md5(normalize_question(question).encode()).hexdigest()


def generate_question_answer(
    syllabus: str,
    question_type: str,
    academic_level: str,
    api_key: str,
    institution: Optional[str] = None,
    topic_focus: Optional[str] = None,
    question_number: int = 1,
    avoid_topics: Optional[List[str]] = None
) -> dict:
    """
    Generate question and answer using Qwen model via OpenRouter.
    
    Args:
        syllabus: The syllabus content pasted by user
        question_type: One of "1 Mark", "2 Mark", "5 Mark", "10 Mark"
        academic_level: User's academic/professional level
        api_key: OpenRouter API key
        institution: Optional institution name for context
        topic_focus: Specific topic to focus on for variety
        question_number: Question number for batch generation
        avoid_topics: Topics to avoid for diversity
        
    Returns:
        Dictionary with generated question, answer, and metadata
    """
    if not api_key:
        return {"error": "API key is required"}
    
    guidelines = ANSWER_GUIDELINES.get(question_type, ANSWER_GUIDELINES["2 Mark"])
    
    # Build variety instructions
    variety_instruction = ""
    if topic_focus:
        variety_instruction = f"\n- Focus specifically on: **{topic_focus}**"
    if avoid_topics:
        variety_instruction += f"\n- AVOID these already covered topics: {', '.join(avoid_topics)}"
    
    # Build the system prompt for academic context
    system_prompt = f"""You are an expert academic assistant specializing in creating {academic_level.lower()} level educational content.
Your task is to generate UNIQUE exam-style questions and model answers based on provided syllabus content.

Context:
- Academic Level: {academic_level}
- Institution: {institution if institution else "Not specified"}
- Question Type: {question_type} ({guidelines['type']} answer)
- Question Number: {question_number}

Answer Format Requirements:
{guidelines['instruction']}

CRITICAL REQUIREMENTS FOR UNIQUENESS:
1. Each question MUST be different from previous ones
2. Cover DIFFERENT topics and subtopics from the syllabus
3. Use different cognitive levels (remember, understand, apply, analyze)
4. Vary question formats (define, explain, compare, analyze, evaluate)
5. NEVER repeat the same question or very similar questions
{variety_instruction}

Always ensure:
1. Questions are clear, relevant to the syllabus, and appropriately challenging
2. Answers are accurate, well-structured, and match the specified length
3. Language is professional and suitable for {academic_level.lower()}
4. Include key terminology from the syllabus where appropriate
5. Each question covers a DISTINCT concept or topic"""

    # Build the user prompt with syllabus
    user_prompt = f"""SYLLABUS CONTENT:
{syllabus}

TASK:
Generate ONE unique question based on the syllabus above, along with its model answer.

{variety_instruction}

OUTPUT FORMAT (strictly follow this JSON structure):
{{
    "question": "The generated question text here",
    "answer": "The model answer following the {guidelines['lines']}-line guideline",
    "topic": "Main topic from syllabus this question covers",
    "difficulty": "Easy/Medium/Hard",
    "key_concepts": ["concept1", "concept2"]
}}

IMPORTANT: 
- This is question #{question_number} - ensure it's completely different from previous questions
- Cover a topic or angle NOT covered in earlier questions
- If topic_focus is provided, use it; otherwise select from uncovered areas

Ensure the answer strictly adheres to the length requirement for {question_type} questions."""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://questionbank.app",
        "X-OpenRouter-Title": "AI Question Bank Generator"
    }
    
    # Adjust temperature for variety
    temperature = 0.7 if question_number > 5 else 0.5  # More variety in later questions
    
    payload = {
        "model": QWEN_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": temperature,
        "max_tokens": 1024,
        "top_p": 0.9,
        "frequency_penalty": 0.3,  # Penalize repetition
        "presence_penalty": 0.3   # Encourage new topics
    }
    
    try:
        response = requests.post(
            OPENROUTER_API_URL,
            headers=headers,
            data=json.dumps(payload),
            timeout=90
        )
        response.raise_for_status()
        result = response.json()
        
        # Parse the AI response
        content = result["choices"][0]["message"]["content"]
        
        # Try to extract JSON from the response
        import re
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            qa_data = json.loads(json_match.group())
        else:
            # Fallback: create structured response from text
            qa_data = {
                "question": content.split("Answer:")[0].strip() if "Answer:" in content else content,
                "answer": content.split("Answer:")[-1].strip() if "Answer:" in content else "Answer not formatted",
                "topic": topic_focus if topic_focus else "Syllabus Topic",
                "difficulty": "Medium",
                "key_concepts": []
            }
        
        qa_data["question_type"] = question_type
        qa_data["academic_level"] = academic_level
        qa_data["question_number"] = question_number
        return qa_data
        
    except requests.exceptions.RequestException as e:
        return {"error": f"API request failed: {str(e)}"}
    except json.JSONDecodeError:
        return {"error": "Failed to parse AI response. Please try again."}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


def extract_topics_from_syllabus(syllabus: str) -> List[str]:
    """Extract potential topics from syllabus content."""
    import re
    
    # Common topic indicators
    topic_patterns = [
        r'Topic:\s*(.+?)(?=\n\n|\n[A-Z]|\Z)',
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)(?:\s*[-–—]\s*)',
        r'(\b[A-Z][a-zA-Z]+(?:\s+[a-zA-Z]+)*\b)\s*[–—-]'
    ]
    
    topics = set()
    
    for pattern in topic_patterns:
        matches = re.findall(pattern, syllabus, re.IGNORECASE | re.MULTILINE)
        for match in matches:
            if isinstance(match, tuple):
                match = match[0]
            topic = match.strip()
            if len(topic) > 3 and len(topic) < 100:  # Filter reasonable length
                topics.add(topic)
    
    # If no topics found, create broad categories
    if not topics:
        lines = syllabus.split('\n')
        for line in lines:
            line = line.strip()
            if line and not line.startswith('Topic:') and len(line) > 10:
                # Take first few words as topic
                words = line.split()[:5]
                topics.add(' '.join(words))
    
    return list(topics)[:20]  # Return top 20 topics


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
    """
    Generate multiple unique questions with duplicate prevention.
    
    Args:
        syllabus: The syllabus content
        question_type: Type of question
        academic_level: Academic level
        api_key: OpenRouter API key
        num_questions: Number of questions to generate
        institution: Institution name
        previous_questions: Set of previously generated questions (normalized)
        progress_callback: Optional callback for progress updates
        
    Returns:
        List of unique question-answer dictionaries
    """
    if previous_questions is None:
        previous_questions = set()
    
    results = []
    max_attempts = num_questions * 3  # Allow retries for duplicates
    attempts = 0
    
    # Extract topics for variety
    available_topics = extract_topics_from_syllabus(syllabus)
    used_topics = []
    
    if progress_callback:
        progress_callback(0, f"Starting generation of {num_questions} questions...")
    
    while len(results) < num_questions and attempts < max_attempts:
        attempts += 1
        
        # Select topic for variety
        topic_focus = None
        if available_topics:
            # Prioritize unused topics
            unused_topics = [t for t in available_topics if t not in used_topics]
            if unused_topics:
                import random
                topic_focus = random.choice(unused_topics)
                used_topics.append(topic_focus)
            else:
                import random
                topic_focus = random.choice(available_topics)
        
        # Generate question
        result = generate_question_answer(
            syllabus=syllabus,
            question_type=question_type,
            academic_level=academic_level,
            api_key=api_key,
            institution=institution,
            topic_focus=topic_focus,
            question_number=len(results) + 1,
            avoid_topics=used_topics[-3:] if len(used_topics) > 3 else None
        )
        
        if "error" in result:
            continue
        
        # Check for duplicates
        question_text = normalize_question(result.get('question', ''))
        question_hash = get_question_hash(result.get('question', ''))
        
        # Check against previous questions and already generated in this batch
        existing_questions = previous_questions | set(normalize_question(q.get('question', '')) for q in results)
        
        is_duplicate = False
        
        # Check exact match
        if question_text in existing_questions:
            is_duplicate = True
        
        # Check similarity (simple word overlap)
        if not is_duplicate and results:
            question_words = set(question_text.split())
            for existing in existing_questions:
                existing_words = set(existing.split())
                if question_words and existing_words:
                    overlap = len(question_words & existing_words) / max(len(question_words), len(existing_words))
                    if overlap > 0.85:  # 85% similar = duplicate
                        is_duplicate = True
                        break
        
        if not is_duplicate:
            results.append(result)
            previous_questions.add(question_text)
            
            if progress_callback:
                progress = len(results) / num_questions
                msg = f"Generated {len(results)}/{num_questions} unique questions..."
                progress_callback(progress, msg)
    
    return results


def generate_multiple_questions(
    syllabus: str,
    question_type: str,
    academic_level: str,
    api_key: str,
    count: int = 5,
    institution: Optional[str] = None
) -> list:
    """
    Legacy function - now uses get_unique_questions for better duplicate prevention.
    
    Generate multiple questions of the same type.
    """
    return get_unique_questions(
        syllabus=syllabus,
        question_type=question_type,
        academic_level=academic_level,
        api_key=api_key,
        num_questions=count,
        institution=institution
    )
