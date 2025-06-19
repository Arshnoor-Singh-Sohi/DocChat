import streamlit as st
import time
import os
from dotenv import load_dotenv
import json
from datetime import datetime

# Load environment variables FIRST
load_dotenv()

# Check if API key is loaded
if not os.getenv("OPENAI_API_KEY"):
    st.error("❌ OPENAI_API_KEY not found! Please add it to your .env file")
    st.stop()

from backend.rag import DocumentationRAG
from backend.scraper import DocumentationScraper
import re
import hashlib

# Page configuration with dark theme
st.set_page_config(
    page_title="DocChat AI - Chat with Any Documentation",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/yourusername/docchat-ai',
        'Report a bug': "https://github.com/yourusername/docchat-ai/issues",
        'About': "# DocChat AI\nChat with any documentation using AI!"
    }
)

# Enhanced CSS with dark mode support and modern design
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Fira+Code:wght@400;500&display=swap');
    
    /* Global Styles */
    .stApp {
        font-family: 'Inter', sans-serif;
    }
    
    /* Dark mode detection and styles */
    @media (prefers-color-scheme: dark) {
        :root {
            --bg-primary: #0e1117;
            --bg-secondary: #1a1d24;
            --bg-tertiary: #262730;
            --text-primary: #fafafa;
            --text-secondary: #b8bcc8;
            --accent: #00d4ff;
            --accent-hover: #00a8cc;
            --success: #00c851;
            --error: #ff4444;
            --warning: #ffbb33;
            --border: #2d3139;
        }
    }
    
    @media (prefers-color-scheme: light) {
        :root {
            --bg-primary: #ffffff;
            --bg-secondary: #f8f9fa;
            --bg-tertiary: #e9ecef;
            --text-primary: #1a1d24;
            --text-secondary: #6c757d;
            --accent: #0066cc;
            --accent-hover: #0052a3;
            --success: #28a745;
            --error: #dc3545;
            --warning: #ffc107;
            --border: #dee2e6;
        }
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background: var(--bg-secondary);
        border-right: 1px solid var(--border);
    }
    
    section[data-testid="stSidebar"] .stButton > button {
        background: var(--bg-tertiary);
        color: var(--text-primary);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 500;
        transition: all 0.3s ease;
        width: 100%;
        margin-bottom: 0.5rem;
    }
    
    section[data-testid="stSidebar"] .stButton > button:hover {
        background: var(--accent);
        color: white;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 212, 255, 0.3);
    }
    
    /* Logo and Header */
    .logo-container {
        background: linear-gradient(135deg, var(--accent) 0%, var(--accent-hover) 100%);
        border-radius: 16px;
        padding: 2rem;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 8px 24px rgba(0, 212, 255, 0.2);
    }
    
    .logo-text {
        color: white;
        font-size: 2rem;
        font-weight: 700;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
    }
    
    .logo-subtitle {
        color: rgba(255, 255, 255, 0.9);
        font-size: 1rem;
        margin-top: 0.5rem;
    }
    
    /* Chat Messages */
    .chat-message {
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        animation: fadeIn 0.3s ease;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .user-message {
        background: linear-gradient(135deg, var(--accent) 0%, var(--accent-hover) 100%);
        color: white;
        margin-left: 20%;
    }
    
    .assistant-message {
        background: var(--bg-secondary);
        color: var(--text-primary);
        margin-right: 20%;
        border: 1px solid var(--border);
    }
    
    /* Code Blocks - Enhanced for Streamlit native code blocks */
    .stCodeBlock {
        margin: 1rem 0 !important;
    }
    
    /* Style the code block container */
    div[data-testid="stCode"] {
        background-color: #1e1e1e !important;
        border-radius: 8px !important;
        border: 1px solid #3e3e3e !important;
        overflow: hidden !important;
        margin: 1rem 0 !important;
    }
    
    /* Style the code area */
    div[data-testid="stCode"] pre {
        background-color: #1e1e1e !important;
        color: #d4d4d4 !important;
        padding: 1rem !important;
        margin: 0 !important;
        font-size: 0.875rem !important;
        line-height: 1.6 !important;
        font-family: 'Fira Code', 'Consolas', 'Monaco', 'Courier New', monospace !important;
        border: none !important;
        overflow-x: auto !important;
    }
    
    /* Style the copy button */
    div[data-testid="stCode"] button[title="Copy to clipboard"] {
        background-color: #0066cc !important;
        color: white !important;
        border: none !important;
        padding: 0.4rem 0.8rem !important;
        border-radius: 4px !important;
        font-size: 0.85rem !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
        position: absolute !important;
        top: 0.5rem !important;
        right: 0.5rem !important;
    }
    
    div[data-testid="stCode"] button[title="Copy to clipboard"]:hover {
        background-color: #0052a3 !important;
        transform: scale(1.05) !important;
    }
    
    /* Success state for copy button */
    div[data-testid="stCode"] button[title="Copied!"] {
        background-color: #28a745 !important;
    }
    
    /* Style the code toolbar */
    div[data-testid="stCode"] > div:first-child {
        background-color: #2d2d2d !important;
        border-bottom: 1px solid #3e3e3e !important;
        padding: 0.5rem 1rem !important;
        display: flex !important;
        justify-content: space-between !important;
        align-items: center !important;
    }
    
    /* Language label */
    div[data-testid="stCode"] .st-emotion-cache-1whk732 {
        color: #888 !important;
        font-size: 0.85rem !important;
        font-weight: 500 !important;
        text-transform: lowercase !important;
    }
    
    /* Line numbers styling */
    div[data-testid="stCode"] .line-numbers {
        color: #858585 !important;
        padding-right: 1rem !important;
        user-select: none !important;
        border-right: 1px solid #3e3e3e !important;
        margin-right: 1rem !important;
    }
    
    /* Syntax highlighting improvements */
    div[data-testid="stCode"] .hljs-keyword,
    div[data-testid="stCode"] .hljs-selector-tag,
    div[data-testid="stCode"] .hljs-literal,
    div[data-testid="stCode"] .hljs-section,
    div[data-testid="stCode"] .hljs-link {
        color: #569cd6 !important;
    }
    
    div[data-testid="stCode"] .hljs-string,
    div[data-testid="stCode"] .hljs-meta-string,
    div[data-testid="stCode"] .hljs-code,
    div[data-testid="stCode"] .hljs-addition {
        color: #ce9178 !important;
    }
    
    div[data-testid="stCode"] .hljs-comment,
    div[data-testid="stCode"] .hljs-quote,
    div[data-testid="stCode"] .hljs-deletion {
        color: #6a9955 !important;
        font-style: italic !important;
    }
    
    div[data-testid="stCode"] .hljs-function,
    div[data-testid="stCode"] .hljs-name,
    div[data-testid="stCode"] .hljs-selector-id,
    div[data-testid="stCode"] .hljs-selector-class {
        color: #dcdcaa !important;
    }
    
    div[data-testid="stCode"] .hljs-number,
    div[data-testid="stCode"] .hljs-meta,
    div[data-testid="stCode"] .hljs-built_in,
    div[data-testid="stCode"] .hljs-builtin-name,
    div[data-testid="stCode"] .hljs-type {
        color: #b5cea8 !important;
    }
    
    div[data-testid="stCode"] .hljs-attribute,
    div[data-testid="stCode"] .hljs-variable,
    div[data-testid="stCode"] .hljs-template-variable {
        color: #9cdcfe !important;
    }
    
    /* Inline code */
    .inline-code {
        background: #2d2d2d;
        color: #e06c75;
        padding: 0.2rem 0.4rem;
        border-radius: 3px;
        font-family: 'Fira Code', 'Consolas', 'Monaco', 'Courier New', monospace;
        font-size: 0.875em;
        border: 1px solid #3e3e3e;
        white-space: nowrap;
    }
    
    /* Code in light mode */
    @media (prefers-color-scheme: light) {
        div[data-testid="stCode"] {
            background-color: #f6f8fa !important;
            border: 1px solid #d1d5da !important;
        }
        
        div[data-testid="stCode"] pre {
            background-color: #f6f8fa !important;
            color: #24292e !important;
        }
        
        div[data-testid="stCode"] > div:first-child {
            background-color: #f1f3f5 !important;
            border-bottom: 1px solid #d1d5da !important;
        }
        
        .inline-code {
            background: #f3f4f6;
            color: #e01e5a;
            border: 1px solid #e1e4e8;
        }
    }
    
    /* Progress Indicators */
    .progress-container {
        background: var(--bg-secondary);
        border-radius: 12px;
        padding: 2rem;
        margin: 1rem 0;
        border: 1px solid var(--border);
    }
    
    .progress-title {
        font-size: 1.25rem;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 1rem;
    }
    
    .progress-step {
        display: flex;
        align-items: center;
        margin-bottom: 1rem;
        padding: 0.75rem;
        background: var(--bg-tertiary);
        border-radius: 8px;
        transition: all 0.3s ease;
    }
    
    .progress-step.active {
        background: var(--accent);
        color: white;
        transform: translateX(10px);
    }
    
    .progress-step.completed {
        opacity: 0.7;
    }
    
    .progress-icon {
        font-size: 1.5rem;
        margin-right: 1rem;
    }
    
    .progress-text {
        font-weight: 500;
    }
    
    /* Input Area */
    .input-container {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: var(--bg-primary);
        border-top: 1px solid var(--border);
        padding: 1rem;
        backdrop-filter: blur(10px);
        z-index: 100;
    }
    
    /* Status Badges */
    .status-badge {
        display: inline-block;
        padding: 0.35rem 1rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
    
    .status-ready {
        background: var(--success);
        color: white;
    }
    
    .status-processing {
        background: var(--warning);
        color: white;
    }
    
    .status-error {
        background: var(--error);
        color: white;
    }
    
    /* Feature Cards */
    .feature-card {
        background: var(--bg-secondary);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 1.5rem;
        height: 100%;
        transition: all 0.3s ease;
        text-align: center;
    }
    
    .feature-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
        border-color: var(--accent);
    }
    
    .feature-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
    }
    
    .feature-title {
        font-size: 1.25rem;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 0.5rem;
    }
    
    .feature-description {
        color: var(--text-secondary);
        line-height: 1.6;
    }
    
    /* Responsive Design */
    @media (max-width: 768px) {
        .user-message, .assistant-message {
            margin-left: 0;
            margin-right: 0;
        }
        
        .logo-container {
            padding: 1.5rem;
        }
        
        .logo-text {
            font-size: 1.5rem;
        }
        
        .feature-card {
            margin-bottom: 1rem;
        }
        
        .chat-message {
            padding: 1rem;
        }
    }
    
    /* Custom Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--bg-secondary);
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--accent);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: var(--accent-hover);
    }
    
    /* Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Input styling */
    .stTextInput > div > div > input {
        background: var(--bg-secondary);
        color: var(--text-primary);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 0.75rem;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: var(--accent);
        box-shadow: 0 0 0 2px rgba(0, 212, 255, 0.2);
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'rag_systems' not in st.session_state:
    st.session_state.rag_systems = {}
if 'current_doc' not in st.session_state:
    st.session_state.current_doc = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'processing' not in st.session_state:
    st.session_state.processing = False
if 'input_key' not in st.session_state:
    st.session_state.input_key = 0
if 'progress_info' not in st.session_state:
    st.session_state.progress_info = {"step": "", "progress": 0}

def get_collection_name(url):
    """Generate a unique collection name from URL"""
    return f"doc_{hashlib.md5(url.encode()).hexdigest()[:8]}"

# Progress callback for scraping
def update_progress_callback(current, total, message):
    st.session_state.progress_info = {
        "step": message,
        "progress": current / total,
        "current": current,
        "total": total
    }

# Sidebar
with st.sidebar:
    # Logo
    st.markdown("""
    <div class="logo-container">
        <h1 class="logo-text">🤖 DocChat AI</h1>
        <p class="logo-subtitle">Chat with any documentation</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 📚 Documentation Sources")
    
    # Add new documentation
    with st.expander("➕ Add New Documentation", expanded=True):
        with st.form("add_doc_form"):
            doc_url = st.text_input(
                "Documentation URL",
                placeholder="https://docs.python.org/3/",
                help="Enter the base URL of the documentation site"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                max_pages = st.number_input(
                    "Max pages",
                    min_value=10,
                    max_value=100,
                    value=30,
                    step=10,
                    help="More pages = better coverage"
                )
            
            with col2:
                st.markdown("<br>", unsafe_allow_html=True)
                submitted = st.form_submit_button("🚀 Process", use_container_width=True)
            
            if submitted and doc_url:
                if doc_url not in st.session_state.rag_systems:
                    st.session_state.processing = True
                    st.session_state.current_doc = doc_url
    
    # List existing documentation
    if st.session_state.rag_systems:
        st.markdown("### 📋 Available Sources")
        for url, rag in st.session_state.rag_systems.items():
            col1, col2 = st.columns([4, 1])
            with col1:
                domain = url.split('//')[1].split('/')[0]
                if st.button(f"📖 {domain}", key=url, use_container_width=True):
                    st.session_state.current_doc = url
                    st.session_state.input_key += 1  # Reset input
            with col2:
                if st.button("🗑️", key=f"del_{url}", help="Remove"):
                    del st.session_state.rag_systems[url]
                    if st.session_state.current_doc == url:
                        st.session_state.current_doc = None
                    st.rerun()
    
    # Quick start examples
    with st.expander("🚀 Quick Start Examples"):
        examples = {
            "Python 🐍": "https://docs.python.org/3/",
            "React ⚛️": "https://react.dev/learn",
            "FastAPI ⚡": "https://fastapi.tiangolo.com/",
            "Django 🎸": "https://docs.djangoproject.com/"
        }
        
        for name, url in examples.items():
            if st.button(f"{name}", key=f"ex_{name}", use_container_width=True):
                if url not in st.session_state.rag_systems:
                    st.session_state.processing = True
                    st.session_state.current_doc = url
                    doc_url = url
                    max_pages = 30

# Main content area
if st.session_state.processing and doc_url:
    # Processing screen with detailed progress
    st.markdown("""
    <div class="progress-container">
        <h2 class="progress-title">🔄 Processing Documentation</h2>
    </div>
    """, unsafe_allow_html=True)
    
    progress_placeholder = st.empty()
    
    # Progress steps
    steps = [
        {"icon": "🌐", "text": "Connecting to website", "status": "pending"},
        {"icon": "🕷️", "text": "Crawling documentation pages", "status": "pending"},
        {"icon": "📄", "text": "Extracting content", "status": "pending"},
        {"icon": "✂️", "text": "Chunking documents", "status": "pending"},
        {"icon": "🧮", "text": "Creating embeddings", "status": "pending"},
        {"icon": "💾", "text": "Storing in vector database", "status": "pending"}
    ]
    
    try:
        # Initialize RAG system
        collection_name = get_collection_name(doc_url)
        rag = DocumentationRAG(collection_name)
        
        # Set progress callback
        scraper = DocumentationScraper(doc_url, max_pages)
        scraper.set_progress_callback(update_progress_callback)
        
        # Create vector store with visual progress
        with st.spinner(""):
            # Create containers for each step
            step_containers = []
            for step in steps:
                step_containers.append(st.empty())
            
            progress_container = st.empty()
            
            # Simulate progress for each step
            for i, step in enumerate(steps):
                # Update each step status
                for j, s in enumerate(steps):
                    if j < i:
                        step_containers[j].success(f"✅ {s['text']}")
                    elif j == i:
                        step_containers[j].info(f"{s['icon']} {s['text']} (In Progress)")
                    else:
                        step_containers[j].write(f"{s['icon']} {s['text']}")
                
                # Add current progress if crawling
                if i == 1 and st.session_state.progress_info["progress"] > 0:
                    current = st.session_state.progress_info.get('current', 0)
                    total = st.session_state.progress_info.get('total', max_pages)
                    progress = st.session_state.progress_info['progress']
                    
                    with progress_container.container():
                        st.write(f"Crawling page {current} of {total}")
                        st.progress(progress)
                
                if i == 1:
                    # Actually create the vector store during crawling step
                    rag.create_vector_store(doc_url, max_pages=max_pages)
                else:
                    time.sleep(0.5)  # Brief pause for other steps
        
        # Store the RAG system
        st.session_state.rag_systems[doc_url] = rag
        st.session_state.processing = False
        
        # Success message
        st.success("✅ Documentation processed successfully!")
        time.sleep(1)
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        st.session_state.processing = False

elif st.session_state.current_doc:
    # Chat interface
    doc_domain = st.session_state.current_doc.split('//')[1].split('/')[0]
    
    # Header with status
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown(f"# 💬 Chat with **{doc_domain}**")
    with col2:
        st.markdown('<span class="status-badge status-ready">● Connected</span>', unsafe_allow_html=True)
    
    # Chat messages container with padding for fixed input
    chat_container = st.container()
    st.markdown('<div style="height: 100px;"></div>', unsafe_allow_html=True)  # Spacer for fixed input
    
    # Display chat history
    with chat_container:
        for message in st.session_state.chat_history:
            if message["role"] == "user":
                st.markdown(f"""
                <div class="chat-message user-message">
                    <div style="display: flex; align-items: flex-start; gap: 0.5rem;">
                        <span style="font-size: 1.2rem;">👤</span>
                        <div style="flex: 1;">{message["content"]}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                # Assistant message with potential code blocks
                with st.container():
                    # Check if message contains code blocks
                    if '```' in message["content"]:
                        # Split by code blocks
                        parts = re.split(r'(```[\s\S]*?```)', message["content"])
                        
                        st.markdown('<div class="chat-message assistant-message">', unsafe_allow_html=True)
                        st.markdown('<div style="display: flex; align-items: flex-start; gap: 0.5rem;"><span style="font-size: 1.2rem;">🤖</span><div style="flex: 1; width: 100%;">', unsafe_allow_html=True)
                        
                        for part in parts:
                            if part.startswith('```') and part.endswith('```'):
                                # Extract code block
                                code_content = part[3:-3].strip()
                                
                                # Extract language if specified
                                lines = code_content.split('\n', 1)
                                if len(lines) > 0 and lines[0].strip() and not ' ' in lines[0].strip() and lines[0].strip().isalpha():
                                    language = lines[0].strip().lower()
                                    code = lines[1] if len(lines) > 1 else ''
                                else:
                                    language = 'python'
                                    code = code_content
                                
                                # Display code
                                if code.strip():
                                    st.code(code.strip(), language=language, line_numbers=True)
                            else:
                                # Regular text
                                if part.strip():
                                    # Process inline code
                                    part = re.sub(r'`([^`]+)`', r'<code class="inline-code">\1</code>', part)
                                    st.markdown(part, unsafe_allow_html=True)
                        
                        st.markdown('</div></div></div>', unsafe_allow_html=True)
                    else:
                        # No code blocks, just regular text
                        content = re.sub(r'`([^`]+)`', r'<code class="inline-code">\1</code>', message["content"])
                        st.markdown(f"""
                        <div class="chat-message assistant-message">
                            <div style="display: flex; align-items: flex-start; gap: 0.5rem;">
                                <span style="font-size: 1.2rem;">🤖</span>
                                <div style="flex: 1;">{content}</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
    
    # Fixed input area at bottom
    with st.container():
        col1, col2 = st.columns([5, 1])
        with col1:
            user_input = st.text_input(
                "Ask a question",
                placeholder="How do I create a list in Python?",
                key=f"user_input_{st.session_state.input_key}",
                label_visibility="collapsed"
            )
        with col2:
            send_clicked = st.button("📤 Send", use_container_width=True)
    
    # Process input
    if user_input and (send_clicked or st.session_state.get('enter_pressed')):
        # Add user message
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        
        # Get RAG system
        rag = st.session_state.rag_systems[st.session_state.current_doc]
        
        # Get response with loading animation
        with st.spinner("🤔 Thinking..."):
            response = rag.query(user_input)
        
        # Add assistant response
        st.session_state.chat_history.append({"role": "assistant", "content": response})
        
        # Clear input by incrementing key
        st.session_state.input_key += 1
        st.rerun()
    
    # Clear chat button
    if st.session_state.chat_history:
        if st.button("🗑️ Clear Chat"):
            st.session_state.chat_history = []
            st.rerun()

else:
    # Welcome screen with feature cards
    st.markdown("""
    # 🎉 Welcome to **DocChat AI**!
    ### Your AI-powered documentation assistant
    """)
    
    # Feature cards
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">🎯</div>
            <h3 class="feature-title">Accurate Answers</h3>
            <p class="feature-description">Powered by GPT-4 and semantic search for precise, contextual responses</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">⚡</div>
            <h3 class="feature-title">Lightning Fast</h3>
            <p class="feature-description">Vector search provides instant access to relevant documentation</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">🔐</div>
            <h3 class="feature-title">Private & Secure</h3>
            <p class="feature-description">Your documentation stays in your own vector database</p>
        </div>
        """, unsafe_allow_html=True)
    
    # How it works
    st.markdown("---")
    st.markdown("## 🚀 How It Works")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        ### 1️⃣ Add Documentation
        Enter any documentation URL in the sidebar
        """)
    
    with col2:
        st.markdown("""
        ### 2️⃣ AI Processing
        We crawl, chunk, and index the documentation
        """)
    
    with col3:
        st.markdown("""
        ### 3️⃣ Start Chatting
        Ask questions and get instant answers with code
        """)
    
    st.info("👈 **Get started** by adding a documentation URL in the sidebar!")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: var(--text-secondary); padding: 2rem 0;">
    <p>Built with ❤️ using Streamlit, LangChain, and Qdrant</p>
    <p style="font-size: 0.85rem; opacity: 0.7;">DocChat AI © 2025 | Powered by OpenAI GPT-4</p>
</div>
""", unsafe_allow_html=True)
