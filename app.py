"""
AI-Powered Academic/Professional Question Bank
Streamlit Application with OpenRouter API (Qwen Model)
API Key: Configured via Streamlit Secrets
Version: 2.2 - Reset Fixed & Sample Format Added
"""

import streamlit as st
import os
from datetime import datetime
from utils.styling import inject_academic_theme
from utils.generator import get_unique_questions_fast
from utils.exporter import export_to_word, export_to_pdf

# Page configuration
st.set_page_config(
    page_title="AI Question Bank Generator",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject academic theme
inject_academic_theme()

# Session state initialization - MUST be at the top
if 'generated_qa' not in st.session_state:
    st.session_state.generated_qa = []
if 'previous_questions' not in st.session_state:
    st.session_state.previous_questions = set()
if 'syllabus_input' not in st.session_state:
    st.session_state.syllabus_input = ""
if 'academic_level' not in st.session_state:
    st.session_state.academic_level = "School Student"
if 'institution' not in st.session_state:
    st.session_state.institution = ""
if 'question_type' not in st.session_state:
    st.session_state.question_type = "2 Mark"
if 'num_questions' not in st.session_state:
    st.session_state.num_questions = 10

# Get API Key from Streamlit Secrets
def get_api_key():
    """Retrieve API key from Streamlit secrets or environment variable."""
    try:
        if hasattr(st, 'secrets') and 'OPENROUTER_API_KEY' in st.secrets:
            return st.secrets["OPENROUTER_API_KEY"]
        elif os.getenv("OPENROUTER_API_KEY"):
            return os.getenv("OPENROUTER_API_KEY")
        else:
            return None
    except Exception:
        return None

# Sidebar - App Information
with st.sidebar:
    st.header("ℹ️ App Information")
    
    st.success("✅ API Key Configured" if get_api_key() else "❌ API Key Missing")
    
    st.info("""
    **How to Use:**
    1. Select your academic level
    2. Paste syllabus content
    3. Choose question type & quantity
    4. Click Submit to generate
    
    **Performance:** 
    - Optimized for speed
    - Batch processing enabled
    - Model: Qwen 2.5 72B
    """)
    
    st.divider()
    st.caption("🎓 AI Question Bank v2.2")

# Main Header
st.markdown("""
<div class="main-header">
    <h1>🎓 AI-Powered Academic/Professional Question Bank</h1>
    <p>Fast & Efficient Question Generation - No Duplicates</p>
</div>
""", unsafe_allow_html=True)

# Check API Key
api_key = get_api_key()
if not api_key:
    st.error("""
    ### ⚠️ API Key Not Configured
    
    Please configure the `OPENROUTER_API_KEY` in Streamlit Secrets.
    """)
    st.stop()

# Sample Syllabus Format (Gray Color)
syllabus_sample_format = """Topic: Fundamentals of Financial Accounting

Financial Accounting – Meaning, Definition, Objectives, Basic Accounting Concepts and Conventions - Journal, Ledger Accounts– Subsidiary Books –– Trial Balance - Classification of Errors – Rectification of Errors – Preparation of Suspense Account – Bank Reconciliation Statement - Need and Preparation

Institution Name : Periyar University, TamilNadu, India."""

# Input Section
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown('<div class="input-card"><h3>📋 Syllabus Input</h3>', unsafe_allow_html=True)
    
    # Academic Level Dropdown
    academic_level = st.selectbox(
        "Academic/Professional Level",
        options=[
            "School Student",
            "Ongoing Graduate student", 
            "JobSeeker",
            "Working Professional"
        ],
        index=0 if st.session_state.academic_level == "School Student" else 
              1 if st.session_state.academic_level == "Ongoing Graduate student" else
              2 if st.session_state.academic_level == "JobSeeker" else 3,
        help="Select your current academic or professional level",
        key="academic_level_select"
    )
    
    # Institution Name
    institution = st.text_input(
        "Institution Name",
        value=st.session_state.institution,
        placeholder="e.g., Periyar University, TamilNadu, India",
        help="Optional: Adds institutional context to generated content",
        key="institution_input"
    )
    
    # Sample Format Display (Gray Color)
    st.markdown(
        '<div class="syllabus-sample">'
        '<strong>📄 Sample Format:</strong><br>'
        '<pre style="margin: 10px 0; padding: 10px; background: #f5f5f5; '
        'border-left: 4px solid #ccc; border-radius: 4px; '
        'font-family: monospace; font-size: 0.85em; color: #666; '
        'white-space: pre-wrap; overflow-x: auto;">' + 
        syllabus_sample_format + 
        '</pre></div>',
        unsafe_allow_html=True
    )
    
    # Syllabus Content - Using session state for proper reset
    syllabus = st.text_area(
        "Paste Unit's Syllabus Content",
        value=st.session_state.syllabus_input,
        height=250,
        placeholder="Paste your syllabus content here (follow the sample format above)...",
        label_visibility="visible",
        key="syllabus_textarea"
    )
    
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="input-card"><h3>❓ Question Settings</h3>', unsafe_allow_html=True)
    
    # Question Type Dropdown
    question_type = st.selectbox(
        "Type of Question",
        options=["1 Mark", "2 Mark", "5 Mark", "10 Mark"],
        index=1 if st.session_state.question_type == "2 Mark" else 
              0 if st.session_state.question_type == "1 Mark" else
              2 if st.session_state.question_type == "5 Mark" else 3,
        help="Select the mark value to determine answer length",
        key="question_type_select"
    )
    
    # Display answer guidelines
    guidelines = {
        "1 Mark": "📝 Objective (1 sentence, ~15 words)",
        "2 Mark": "📝 Short (~3 lines, 40-60 words)",
        "5 Mark": "📝 Detailed (~6 lines, 100-150 words)",
        "10 Mark": "📝 Comprehensive (~12 lines, 200-300 words)"
    }
    st.info(guidelines[question_type])
    
    # Number of Questions - DROPDOWN
    num_questions = st.selectbox(
        "No. of Questions Required",
        options=[10, 20, 30, 50],
        index=0 if st.session_state.num_questions == 10 else 
              1 if st.session_state.num_questions == 20 else
              2 if st.session_state.num_questions == 30 else 3,
        help="Select how many unique questions to generate",
        key="num_questions_select"
    )
    
    # Variety Enhancement Option
    ensure_variety = st.checkbox(
        "✓ Ensure Maximum Variety",
        value=True,
        help="Prevent duplicate questions and cover different topics",
        key="variety_checkbox"
    )
    
    st.markdown('</div>', unsafe_allow_html=True)

# Action Buttons
st.markdown('<div style="margin: 1.5rem 0">', unsafe_allow_html=True)
col_btn1, col_btn2, col_btn3, col_btn4 = st.columns(4)

with col_btn1:
    generate_btn = st.button("🚀 Submit", type="primary", use_container_width=True)
with col_btn2:
    reset_btn = st.button("🔄 Reset", use_container_width=True)
with col_btn3:
    export_word = st.button("📄 Export Word", use_container_width=True)
with col_btn4:
    export_pdf = st.button("📕 Export PDF", use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

# Reset functionality - FIXED: Complete reset with session state clear
if reset_btn:
    # Clear ALL session state variables
    st.session_state.generated_qa = []
    st.session_state.previous_questions = set()
    st.session_state.syllabus_input = ""
    st.session_state.academic_level = "School Student"
    st.session_state.institution = ""
    st.session_state.question_type = "2 Mark"
    st.session_state.num_questions = 10
    
    # Show success message
    st.success("✅ All fields have been reset successfully!")
    
    # Force complete reload
    st.rerun()

# Update session state with current values
st.session_state.syllabus_input = syllabus
st.session_state.academic_level = academic_level
st.session_state.institution = institution
st.session_state.question_type = question_type
st.session_state.num_questions = num_questions

# Generate Questions - OPTIMIZED FOR SPEED
if generate_btn:
    if not syllabus.strip():
        st.error("❌ Please paste syllabus content to generate questions.")
        st.stop()
    
    with st.spinner(f"⚡ Fast-generating {num_questions} unique {question_type} questions..."):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Clear previous questions if starting fresh
        if not ensure_variety:
            st.session_state.previous_questions = set()
        
        # Use FAST generator with optimized settings
        results = get_unique_questions_fast(
            syllabus=syllabus,
            question_type=question_type,
            academic_level=academic_level,
            api_key=api_key,
            num_questions=num_questions,
            institution=institution if institution else None,
            previous_questions=st.session_state.previous_questions if ensure_variety else set(),
            progress_callback=lambda p, msg: (progress_bar.progress(p), status_text.text(msg))
        )
        
        progress_bar.progress(1.0)
        status_text.text("✅ Generation complete!")
        
        if results:
            st.session_state.generated_qa = results
            # Update previous questions set
            for item in results:
                if 'question' in item:
                    st.session_state.previous_questions.add(item['question'].lower().strip())
            
            generated_count = len(results)
            st.success(f"✅ Successfully generated {generated_count}/{num_questions} unique questions!")
            
            if generated_count < num_questions:
                st.warning(f"⚠️ Generated {generated_count} instead of {num_questions}. Try again or reduce count.")
            
            # Show variety stats
            unique_count = len(set(q.get('question', '').lower() for q in results))
            if unique_count == generated_count:
                st.balloons()
                st.info(f"🎯 All {generated_count} questions are unique!")
        else:
            st.error("❌ No questions were generated. Please check your input and try again.")

# Display Results
if st.session_state.generated_qa:
    st.markdown('<div class="output-card"><h3>📚 Generated Questions & Answers</h3>', unsafe_allow_html=True)
    
    # Show summary stats
    total_q = len(st.session_state.generated_qa)
    unique_topics = len(set(q.get('topic', 'General') for q in st.session_state.generated_qa))
    
    col_stat1, col_stat2, col_stat3 = st.columns(3)
    col_stat1.metric("Total Questions", total_q)
    col_stat2.metric("Unique Topics", unique_topics)
    col_stat3.metric("Question Type", question_type)
    
    st.divider()
    
    # Display questions with numbering
    for idx, item in enumerate(st.session_state.generated_qa, 1):
        expander_label = f"❓ Q{idx}: {item.get('topic', 'General Topic')}"
        
        with st.expander(expander_label, expanded=(idx <= 3)):
            st.markdown(f"""
            <div class="answer-box">
                <div class="question">Q{idx}. {item.get('question', '')}</div>
                <div class="answer"><strong>Answer ({question_type}):</strong><br>{item.get('answer', '')}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Metadata chips
            cols = st.columns(4)
            if item.get('difficulty'):
                cols[0].metric("Difficulty", item['difficulty'])
            if item.get('key_concepts'):
                cols[1].write(f"**Concepts:** {', '.join(item['key_concepts'][:2])}")
            cols[2].write(f"**Type:** {item.get('question_type')}")
            cols[3].write(f"**Topic:** {item.get('topic', 'N/A')[:20]}...")
    
    st.markdown('</div>', unsafe_allow_html=True)

# Export Functionality
if st.session_state.generated_qa and (export_word or export_pdf):
    if export_word:
        try:
            word_bytes = export_to_word(
                st.session_state.generated_qa,
                institution or "Academic Institution",
                question_type
            )
            st.download_button(
                label="⬇️ Download Word Document",
                data=word_bytes,
                file_name=f"question_bank_{question_type.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"Word export failed: {str(e)}")
    
    if export_pdf:
        try:
            pdf_bytes = export_to_pdf(
                st.session_state.generated_qa,
                institution or "Academic Institution",
                question_type
            )
            st.download_button(
                label="⬇️ Download PDF Document",
                data=pdf_bytes,
                file_name=f"question_bank_{question_type.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"PDF export failed: {str(e)}")

# Footer
st.markdown("""
<div class="app-footer">
    <p>🎓 AI-Powered Academic Question Bank | Powered by Qwen via OpenRouter API</p>
    <p style="font-size:0.8rem;color:#999">Model: qwen/qwen-2.5-72b-instruct | Optimized v2.2</p>
</div>
""", unsafe_allow_html=True)
