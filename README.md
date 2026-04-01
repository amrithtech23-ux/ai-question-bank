# 🎓 AI-Powered Academic/Professional Question Bank

[![Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://streamlit.io)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![OpenRouter](https://img.shields.io/badge/OpenRouter-API-orange.svg)](https://openrouter.ai)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **Generate exam-ready questions & model answers from syllabus content using Qwen AI via OpenRouter API**

![Demo Screenshot](assets/demo-screenshot.png) *(Add your screenshot here)*

---

## ✨ Features

### 🎯 Core Functionality
- **Multi-Level Support**: School Student, Graduate, JobSeeker, Working Professional
- **Smart Answer Generation**: Auto-adjusts answer length based on mark type:
  | Mark Type | Format | Approx. Length |
  |-----------|--------|---------------|
  | 🔹 1 Mark | Objective/MCQ | ~15 words, 1 sentence |
  | 🔹 2 Mark | Short paragraph | ~40-60 words, 3 lines |
  | 🔹 5 Mark | Detailed explanation | ~100-150 words, 6 lines |
  | 🔹 10 Mark | Comprehensive answer | ~200-300 words, 12 lines |

### 🤖 AI Integration
- **Model**: Qwen 2.5 72B Instruct via OpenRouter
- **Context-Aware**: Generates questions aligned with syllabus, academic level & institution
- **Structured Output**: JSON-formatted responses with topic, difficulty & key concepts

### 📤 Export Options
- ✅ **Microsoft Word** (.docx) - Professionally formatted with headers, styles & footer
- ✅ **PDF Document** (.pdf) - Print-ready layout with academic styling
- ✅ **Copy to Clipboard** - Quick sharing of generated content

### 🎨 User Experience
- 🎓 Academic-themed UI with professional color palette
- 📱 Fully responsive design (desktop, tablet, mobile)
- 💡 Interactive help sections & sample format guidance
- ⚡ Real-time progress indicators during generation

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10 or higher
- OpenRouter API key ([Get one free](https://openrouter.ai))
- Internet connection

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/ai-question-bank.git
cd ai-question-bank

# 2. Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the application
streamlit run app.py
