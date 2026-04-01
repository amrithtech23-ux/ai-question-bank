"""Question and Answer generation using OpenRouter API with Qwen model."""

import os
import requests
import json
from typing import Optional

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

def generate_question_answer(
    syllabus: str,
    question_type: str,
    academic_level: str,
    api_key: str,
    institution: Optional[str] = None
) -> dict:
    """
    Generate question and answer using Qwen model via OpenRouter.
    
    Args:
        syllabus: The syllabus content pasted by user
        question_type: One of "1 Mark", "2 Mark", "5 Mark", "10 Mark"
        academic_level: User's academic/professional level
        api_key: OpenRouter API key
        institution: Optional institution name for context
        
    Returns:
        Dictionary with generated question, answer, and metadata
    """
    if not api_key:
        return {"error": "API key is required"}
    
    guidelines = ANSWER_GUIDELINES.get(question_type, ANSWER_GUIDELINES["2 Mark"])
    
    # Build the system prompt for academic context
    system_prompt = f"""You are an expert academic assistant specializing in creating {academic_level.lower()} level educational content.
Your task is to generate exam-style questions and model answers based on provided syllabus content.

Context:
- Academic Level: {academic_level}
- Institution: {institution if institution else "Not specified"}
- Question Type: {question_type} ({guidelines['type']} answer)

Answer Format Requirements:
{guidelines['instruction']}

Always ensure:
1. Questions are clear, relevant to the syllabus, and appropriately challenging
2. Answers are accurate, well-structured, and match the specified length
3. Language is professional and suitable for {academic_level.lower()}
4. Include key terminology from the syllabus where appropriate"""

    # Build the user prompt with syllabus
    user_prompt = f"""SYLLABUS CONTENT:
{syllabus}

TASK:
Generate ONE high-quality question based on the syllabus above, along with its model answer.

OUTPUT FORMAT (strictly follow this JSON structure):
{{
    "question": "The generated question text here",
    "answer": "The model answer following the {guidelines['lines']}-line guideline",
    "topic": "Main topic from syllabus this question covers",
    "difficulty": "Easy/Medium/Hard",
    "key_concepts": ["concept1", "concept2"]
}}

Ensure the answer strictly adheres to the length requirement for {question_type} questions."""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://questionbank.app",  # For OpenRouter rankings
        "X-OpenRouter-Title": "AI Question Bank Generator"
    }
    
    payload = {
        "model": QWEN_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.3,  # Lower temperature for more consistent academic output
        "max_tokens": 1024
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
                "topic": "Syllabus Topic",
                "difficulty": "Medium",
                "key_concepts": []
            }
        
        qa_data["question_type"] = question_type
        qa_data["academic_level"] = academic_level
        return qa_data
        
    except requests.exceptions.RequestException as e:
        return {"error": f"API request failed: {str(e)}"}
    except json.JSONDecodeError:
        return {"error": "Failed to parse AI response. Please try again."}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


def generate_multiple_questions(
    syllabus: str,
    question_type: str,
    academic_level: str,
    api_key: str,
    count: int = 5,
    institution: Optional[str] = None
) -> list:
    """Generate multiple questions of the same type."""
    results = []
    for i in range(count):
        result = generate_question_answer(
            syllabus=syllabus,
            question_type=question_type,
            academic_level=academic_level,
            api_key=api_key,
            institution=institution
        )
        if "error" not in result:
            results.append(result)
    return results
