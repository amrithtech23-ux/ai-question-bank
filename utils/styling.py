"""Academic-themed styling for the Question Bank application."""

ACADEMIC_CSS = """
<style>
    /* Academic Color Palette */
    :root {
        --primary-color: #1a3a5c;
        --secondary-color: #2c5f8d;
        --accent-color: #c9a961;
        --bg-light: #f8f9fa;
        --text-dark: #2c3e50;
        --border-color: #dee2e6;
    }
    
    /* Main Container */
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #e4edf5 100%);
        font-family: 'Georgia', 'Times New Roman', serif;
    }
    
    /* Header Styling */
    .main-header {
        text-align: center;
        padding: 1.5rem;
        background: linear-gradient(120deg, var(--primary-color), var(--secondary-color));
        border-radius: 12px;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        color: white;
    }
    
    .main-header h1 {
        font-size: 2rem;
        margin: 0;
        font-weight: 600;
    }
    
    .main-header p {
        margin: 0.5rem 0 0;
        opacity: 0.9;
        font-size: 1.1rem;
    }
    
    /* Card Styling */
    .input-card, .output-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid var(--accent-color);
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        margin-bottom: 1rem;
    }
    
    .input-card h3, .output-card h3 {
        color: var(--primary-color);
        margin-top: 0;
        border-bottom: 2px solid var(--border-color);
        padding-bottom: 0.5rem;
    }
    
    /* Form Elements */
    .stSelectbox > div > div {
        border-color: var(--secondary-color) !important;
    }
    
    .stTextInput > div > div {
        border-color: var(--secondary-color) !important;
    }
    
    .stTextArea > div > div {
        border-color: var(--secondary-color) !important;
        font-family: 'Courier New', monospace;
        font-size: 0.95rem;
    }
    
    /* Button Styling */
    .stButton > button {
        background: var(--secondary-color);
        color: white;
        border: none;
        border-radius: 6px;
        padding: 0.5rem 1.5rem;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background: var(--primary-color);
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(26, 58, 92, 0.3);
    }
    
    .stButton > button:active {
        transform: translateY(0);
    }
    
    /* Answer Display */
    .answer-box {
        background: var(--bg-light);
        padding: 1.2rem;
        border-radius: 8px;
        border: 1px solid var(--border-color);
        margin: 1rem 0;
        line-height: 1.6;
    }
    
    .answer-box .question {
        font-weight: 600;
        color: var(--primary-color);
        margin-bottom: 0.5rem;
        font-size: 1.1rem;
    }
    
    .answer-box .answer {
        color: var(--text-dark);
        padding-left: 1rem;
        border-left: 3px solid var(--accent-color);
    }
    
    /* Syllabus Sample Format - Gray Color */
    .syllabus-sample {
        background: #f8f9fa;
        border: 1px solid #e9ecef;
        border-left: 4px solid #6c757d;
        border-radius: 6px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .syllabus-sample strong {
        color: #495057;
        display: block;
        margin-bottom: 0.5rem;
        font-size: 0.9rem;
    }
    
    .syllabus-sample pre {
        background: #f1f3f5;
        padding: 0.75rem;
        border-radius: 4px;
        font-family: 'Courier New', monospace;
        font-size: 0.85rem;
        color: #666;
        white-space: pre-wrap;
        word-wrap: break-word;
        overflow-x: auto;
        margin: 0;
        line-height: 1.5;
    }
    
    /* Export Buttons */
    .export-buttons {
        display: flex;
        gap: 0.5rem;
        flex-wrap: wrap;
        margin-top: 1rem;
    }
    
    /* Footer */
    .app-footer {
        text-align: center;
        padding: 1.5rem;
        color: #666;
        font-size: 0.9rem;
        border-top: 1px solid var(--border-color);
        margin-top: 2rem;
    }
    
    /* Responsive */
    @media (max-width: 768px) {
        .main-header h1 {
            font-size: 1.5rem;
        }
        .export-buttons {
            flex-direction: column;
        }
    }
</style>
"""

def inject_academic_theme():
    """Inject academic CSS theme into Streamlit app."""
    import streamlit as st
    st.markdown(ACADEMIC_CSS, unsafe_allow_html=True)
