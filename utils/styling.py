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
        border: 3px solid var(--secondary-color) !important;
        border-radius: 6px !important;
        font-family: 'Courier New', monospace;
        font-size: 0.95rem;
        transition: all 0.3s ease;
    }
    
    .stTextArea > div > div:focus-within {
        border-color: var(--primary-color) !important;
        box-shadow: 0 0 0 3px rgba(26, 58, 92, 0.1);
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
    
    /* Syllabus Sample Format - GRAY COLOR BOX */
    .syllabus-sample-box {
        background: linear-gradient(135deg, #e8e8e8 0%, #d5d5d5 100%);
        border: 2px solid #999;
        border-left: 6px solid #666;
        border-radius: 8px;
        padding: 1.2rem;
        margin: 1.2rem 0;
        box-shadow: 0 2px 6px rgba(0,0,0,0.1);
    }
    
    .syllabus-sample-box .sample-header {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-bottom: 0.8rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid #aaa;
    }
    
    .syllabus-sample-box .sample-icon {
        font-size: 1.2rem;
    }
    
    .syllabus-sample-box .sample-header strong {
        color: #444;
        font-size: 1rem;
        font-weight: 600;
    }
    
    .syllabus-sample-box .sample-content {
        background: #f0f0f0;
        padding: 1rem;
        border-radius: 4px;
        font-family: 'Courier New', monospace;
        font-size: 0.85rem;
        color: #555;
        white-space: pre-wrap;
        word-wrap: break-word;
        line-height: 1.6;
        border: 1px solid #bbb;
    }
    
    /* BOLD LABEL for Syllabus Text Area */
    .syllabus-label {
        margin: 1rem 0 0.5rem 0;
        font-size: 1rem;
        color: var(--primary-color);
        font-weight: 700;
    }
    
    .syllabus-label strong {
        font-weight: 700;
        color: var(--text-dark);
        font-size: 1.05rem;
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
