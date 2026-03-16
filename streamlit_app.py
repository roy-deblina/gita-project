#!/usr/bin/env python3
import os
import torch
import random

os.environ["CUDA_VISIBLE_DEVICES"] = ""
torch.set_default_device('cpu')

import streamlit as st
import pickle, sqlite3, time, uuid, pandas as pd, numpy as np
from pathlib import Path
from sentence_transformers import util

PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / 'data'
RETRIEVER_PKL = DATA_DIR / 'retriever_state.pkl'
ANALYTICS_DB = DATA_DIR / 'analytics.db'

st.set_page_config(
    page_title="Gita Wisdom Bot",
    page_icon="🕉️",
    layout="centered",
    initial_sidebar_state="expanded"
)

css = """
<style>
    .block-container {
        max-width: 700px;
        margin: auto;
        padding-top: 1rem;
    }
    
    body {
        background: linear-gradient(135deg, #FBF8F3 0%, #F5E6D3 100%);
        font-family: 'Lora', 'Georgia', serif;
    }
    
    h1 {
        text-align: center;
        color: #B8860B;
        font-size: 2.5rem;
        margin-bottom: 0.2rem;
    }
    
    .subtitle {
        text-align: center;
        color: #8B7355;
        font-size: 1.1rem;
        margin-bottom: 2rem;
        font-style: italic;
    }
    
    /* Glassmorphism Effect for Chat Messages */
    .stChatMessage {
        background: rgba(255, 255, 255, 0.6) !important;
        backdrop-filter: blur(10px) !important;
        border-radius: 18px !important;
        border: 1px solid rgba(224, 192, 151, 0.3) !important;
        padding: 16px !important;
        margin-bottom: 12px !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.05);
    }
    
    /* Premium Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: rgba(30, 29, 28, 0.98) !important;
        border-right: 2px solid #D4A574 !important;
    }
    
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: #E0C097 !important;
    }
    
    [data-testid="stSidebar"] p {
        color: #C9B997 !important;
    }
    
    /* Daily Verse Card */
    .daily-verse-card {
        background: linear-gradient(135deg, rgba(224, 192, 151, 0.15) 0%, rgba(212, 165, 116, 0.1) 100%);
        backdrop-filter: blur(10px);
        border: 2px solid rgba(224, 192, 151, 0.3);
        border-radius: 20px;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 8px 32px rgba(184, 134, 11, 0.1);
    }
    
    .daily-verse-text {
        font-size: 1.3rem;
        font-style: italic;
        color: #1E1D1C;
        letter-spacing: 0.5px;
        line-height: 1.8;
        margin-bottom: 16px;
    }
    
    .daily-verse-citation {
        color: #8B7355;
        font-size: 0.95rem;
        text-align: right;
    }
    
    /* Suggestion Chips */
    .suggestion-chip {
        background: linear-gradient(135deg, #E0C097 0%, #D4A574 100%);
        color: #1E1D1C;
        border: none;
        border-radius: 25px;
        padding: 12px 18px;
        font-weight: 600;
        font-size: 0.9rem;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(224, 192, 151, 0.3);
    }
    
    .suggestion-chip:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 20px rgba(224, 192, 151, 0.4);
    }
    
    /* Citation Card */
    .citation-card {
        background: linear-gradient(135deg, rgba(212, 165, 116, 0.2) 0%, rgba(224, 192, 151, 0.15) 100%);
        border-left: 4px solid #D4A574;
        border-radius: 8px;
        padding: 16px;
        margin: 16px 0;
        font-size: 0.95rem;
        font-style: italic;
        color: #1E1D1C;
    }
    
    .verse-reference {
        color: #8B7355;
        font-size: 0.85rem;
        font-weight: 600;
        margin-top: 12px;
    }
    
    .sanskrit-text {
        font-family: 'Noto Sans Devanagari', serif;
        font-size: 1.1rem;
        color: #B8860B;
        text-align: center;
        margin: 12px 0;
        letter-spacing: 1px;
    }
    
    /* Copy Button */
    .copy-btn {
        background: rgba(224, 192, 151, 0.2);
        border: 1px solid #D4A574;
        color: #1E1D1C;
        border-radius: 6px;
        padding: 8px 12px;
        font-size: 0.85rem;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .copy-btn:hover {
        background: rgba(224, 192, 151, 0.4);
        box-shadow: 0 2px 8px rgba(224, 192, 151, 0.3);
    }
    
    /* Expander styling */
    [data-testid="stExpander"] {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(224, 192, 151, 0.2);
        border-radius: 10px;
    }
    
    .footer {
        text-align: center;
        color: #8B7355;
        font-size: 0.9rem;
        margin-top: 2rem;
        padding-top: 1rem;
        border-top: 1px solid #E0C097;
        font-style: italic;
    }
    
    .social-links {
        display: flex;
        justify-content: center;
        gap: 12px;
        margin-top: 12px;
        font-size: 1.2rem;
    }
    
    .social-links a {
        color: #D4A574;
        text-decoration: none;
        transition: color 0.3s ease;
    }
    
    .social-links a:hover {
        color: #E0C097;
    }
    
    @media (max-width: 768px) {
        h1 {
            font-size: 2rem;
        }
        
        .block-container {
            max-width: 95%;
        }
        
        .daily-verse-text {
            font-size: 1.1rem;
        }
    }
</style>
"""

st.markdown(css, unsafe_allow_html=True)

st.markdown('<h1>🕉️ Gita Wisdom Bot</h1>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Timeless guidance from the Bhagavad Gita<br>Ask Krishna about life, duty, fear, and purpose</div>', unsafe_allow_html=True)

@st.cache_resource
def init_session():
    return str(uuid.uuid4())

@st.cache_resource
def load_retriever():
    if not RETRIEVER_PKL.exists():
        st.info("Building retriever from database (first run)...")
        build_retriever_from_db()
    
    import io
    
    class CPU_Unpickler(pickle.Unpickler):
        def find_class(self, module, name):
            if module == 'torch.storage' and name == '_load_from_bytes':
                return lambda b: torch.load(io.BytesIO(b), map_location='cpu')
            else:
                return super().find_class(module, name)
    
    with open(RETRIEVER_PKL, 'rb') as f:
        data = CPU_Unpickler(f).load()
    
    return data

@st.cache_resource
def build_retriever_from_db():
    from rank_bm25 import BM25Okapi
    from sentence_transformers import SentenceTransformer
    
    gita_db = DATA_DIR / 'gita.db'
    if not gita_db.exists():
        st.error(f"Error: {gita_db} not found")
        st.stop()
    
    conn = sqlite3.connect(str(gita_db))
    cursor = conn.cursor()
    cursor.execute("SELECT chapter_number, verse_number, english FROM verses ORDER BY chapter_number, verse_number")
    rows = cursor.fetchall()
    conn.close()
    
    corpus = []
    texts_for_bm25 = []
    for chapter, verse, text in rows:
        corpus.append({
            'chapter': chapter,
            'verse': verse,
            'english': text,
            'commentary': ''
        })
        texts_for_bm25.append(text.lower().split())
    
    st.write(f"Loaded {len(corpus)} verses")
    
    bm25_index = BM25Okapi(texts_for_bm25)
    st.write(f"BM25 index built")
    
    embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    english_texts = [v['english'] for v in corpus]
    corpus_embeddings = embedding_model.encode(english_texts, convert_to_tensor=True, show_progress_bar=False)
    st.write(f"Embeddings created")
    
    retriever_state = {
        'corpus': corpus,
        'bm25_index': bm25_index,
        'embedding_model': embedding_model,
        'corpus_embeddings': corpus_embeddings
    }
    
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(RETRIEVER_PKL, 'wb') as f:
        pickle.dump(retriever_state, f)
    
    st.success(f"Retriever saved successfully")

# TOPIC DETECTION AND VERSE MAPPING
TOPIC_VERSES = {
    "mind": [(6, 5), (6, 26)],
    "fear": [(2, 19), (2, 20)],
    "anger": [(2, 62), (2, 63)],
    "failure": [(2, 47)],
    "duty": [(3, 19), (18, 47)],
    "purpose": [(4, 7), (18, 66)],
    "peace": [(2, 70)],
    "karma": [(2, 47), (4, 17)],
    "action": [(3, 19), (2, 47)],
    "desire": [(2, 55), (2, 62)],
}

RESPONSE_TEMPLATES = {
    "mind": "True mastery comes from within. The mind is both your greatest tool and your deepest challenge. Through discipline, meditation, and unwavering focus, you can transcend the restless nature of the mind.",
    "fear": "Fear dissolves when you remember your true nature—unchanging, eternal, and divine. Act with courage grounded in duty rather than attachment to outcomes. This is the way of a warrior.",
    "anger": "Anger arises from unfulfilled desires and ego. Release attachment to outcomes, and anger loses its power. Respond with wisdom and compassion, not reaction.",
    "failure": "What you call failure is merely a step in your journey. Success and failure are two sides of the same coin. Perform your duty with excellence, and surrender the results to a higher purpose.",
    "duty": "Your sacred duty is your highest calling. Fulfill your responsibilities without attachment to reward. This righteous action purifies the soul and leads to liberation.",
    "purpose": "Every soul has a unique purpose. Discover it by following your dharma with full commitment. Your purpose unfolds through sincere action and faith.",
    "peace": "Peace is not the absence of challenge—it is the clarity of mind that comes from faith, duty, and detachment. Cultivate inner peace through meditation and wisdom.",
    "karma": "You are the architect of your destiny through your actions. Every action creates consequences. Act with wisdom, intention, and righteousness.",
    "action": "Act without clutching the fruits of your action. Do your duty fully, but release attachment to success or failure. This is the path to liberation.",
    "desire": "Desires are the root of suffering. Through wisdom and discipline, transform desires into righteous aspirations. Seek not pleasure, but purpose.",
}

def detect_topic(query):
    """Detect the emotional/spiritual topic from user query"""
    query = query.lower()
    
    topic_keywords = {
        "mind": ["mind", "focus", "discipline", "control mind", "thoughts"],
        "fear": ["fear", "anxiety", "afraid", "scared", "nervous"],
        "anger": ["anger", "angry", "rage", "furious"],
        "failure": ["failure", "fail", "losing", "lost", "defeat"],
        "duty": ["duty", "responsibility", "work", "dharma"],
        "purpose": ["purpose", "meaning", "life", "why"],
        "peace": ["peace", "stress", "calm", "anxious"],
        "karma": ["karma", "consequences", "actions"],
        "action": ["action", "act", "do", "perform"],
        "desire": ["desire", "want", "attachment", "longing"],
    }
    
    for topic, words in topic_keywords.items():
        for word in words:
            if word in query:
                return topic
    
    return "general"

def get_topic_verses(topic, corpus):
    """Get verses related to a specific topic"""
    if topic not in TOPIC_VERSES:
        return []
    
    verses = []
    for chapter, verse in TOPIC_VERSES[topic]:
        for v in corpus:
            if v["chapter"] == chapter and v["verse"] == verse:
                verses.append({
                    'chapter': v['chapter'],
                    'verse': v['verse'],
                    'text': v['english']
                })
                break
    
    return verses

def limit_words(text, limit=100):
    words = text.split()
    return " ".join(words[:limit])

def retrieve_verses(query, top_k=2):
    retriever_state = load_retriever()
    corpus = retriever_state['corpus']
    bm25_index = retriever_state['bm25_index']
    embedding_model = retriever_state['embedding_model']
    corpus_embeddings = retriever_state['corpus_embeddings']
    
    try:
        tokens = query.lower().split()
        bm25_scores = bm25_index.get_scores(tokens)
        bm25_idx = np.argsort(bm25_scores)[min(-top_k*2,-5):][::-1]
        bm25_res = [(int(i), float(bm25_scores[i])) for i in bm25_idx if bm25_scores[i] > 0]
        
        q_emb = embedding_model.encode(query, convert_to_tensor=True)
        if hasattr(q_emb, 'to'):
            q_emb = q_emb.to('cpu')
        
        corpus_embeddings_cpu = corpus_embeddings.to('cpu') if hasattr(corpus_embeddings, 'to') else corpus_embeddings
        sims = util.pytorch_cos_sim(q_emb, corpus_embeddings_cpu)[0]
        
        if hasattr(sims, 'cpu'):
            sims_np = sims.cpu().numpy()
        else:
            sims_np = np.array(sims)
        
        sem_idx = np.argsort(sims_np)[min(-top_k*2,-5):][::-1]
        sem_res = [(int(i), float(sims_np[i])) for i in sem_idx]
        
        rrf = {}
        k = 60
        for rank, (idx, _) in enumerate(bm25_res):
            rrf[idx] = rrf.get(idx, 0) + 1 / (k + rank + 1)
        for rank, (idx, _) in enumerate(sem_res):
            rrf[idx] = rrf.get(idx, 0) + 1 / (k + rank + 1)
        
        sorted_res = sorted(rrf.items(), key=lambda x: x[1], reverse=True)[:top_k]
        verses = []
        for idx, score in sorted_res:
            v = corpus[idx]
            verses.append({
                'chapter': v['chapter'],
                'verse': v['verse'],
                'text': v['english']
            })
        
        return verses
    except Exception as e:
        return []

def generate_response(query, verses, word_limit=100):
    """Generate Krishna-style response from retrieved verses and templates"""
    
    # Detect topic first
    topic = detect_topic(query)
    
    # Try to get topic-specific verses
    retriever_state = load_retriever()
    corpus = retriever_state['corpus']
    topic_verses = get_topic_verses(topic, corpus)
    
    # Use topic verses if found, otherwise use retrieved verses
    if topic_verses:
        verses = topic_verses[:2]
    
    # Build verse context
    verse_text = ""
    if verses:
        for v in verses:
            verse_text += f'"{v["text"]}"\n\n— Bhagavad Gita {v["chapter"]}.{v["verse"]}\n\n'
    
    # Generate response using template + verse
    template_response = RESPONSE_TEMPLATES.get(topic, "Krishna teaches through the eternal wisdom of the Gita. Reflect on this verse and discover your truth.")
    
    # Combine template with verse
    if verses:
        response = f"{template_response}\n\nThe Gita teaches:\n\n{verses[0]['text']}\n\n— Bhagavad Gita {verses[0]['chapter']}.{verses[0]['verse']}"
    else:
        response = template_response
    
    # Apply word limit
    response = limit_words(response, word_limit)
    
    return response

@st.cache_resource
def init_analytics():
    from analytics_functions import AnalyticsManager, init_analytics_db
    init_analytics_db(ANALYTICS_DB)
    return AnalyticsManager(str(ANALYTICS_DB))

session_id = init_session()
try:
    analytics = init_analytics()
except:
    analytics = None

if "messages" not in st.session_state:
    st.session_state.messages = []

if "word_limit" not in st.session_state:
    st.session_state.word_limit = 100

# Utility function to render copy button
def render_copy_button(verse_text, chapter, verse_num):
    """Render a copy button for verse sharing"""
    copy_text = f'"{verse_text}"\n\n— Bhagavad Gita {chapter}.{verse_num}'
    col1, col2 = st.columns([4, 1])
    with col2:
        if st.button("📋 Copy", key=f"copy_{chapter}_{verse_num}", help="Copy to clipboard"):
            st.toast("Verse copied to clipboard! 🎉", icon="✅")

# Daily Wisdom Feature with Premium Styling
try:
    daily_verse = random.choice(load_retriever()['corpus'])
    st.markdown("""
    <div class="daily-verse-card">
        <div style="text-align: center; margin-bottom: 12px;">
            <span style="font-size: 2rem;">🌼</span>
            <h3 style="color: #B8860B; margin: 8px 0;">Krishna's Wisdom for Today</h3>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([5, 1])
    with col1:
        st.markdown(f"""
        <div class="daily-verse-text">
        "{daily_verse['english']}"
        </div>
        <div class="daily-verse-citation">
        — Bhagavad Gita {daily_verse['chapter']}.{daily_verse['verse']}
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        if st.button("📋", key="copy_daily", help="Copy verse"):
            st.toast("Verse copied! ✨", icon="✅")
        if st.button("📤", key="share_daily", help="Share verse"):
            st.toast("Share on social media! 🙏", icon="✨")
except:
    pass

with st.sidebar:
    st.markdown("---")
    st.markdown("<h2 style='text-align: center; color: #E0C097;'>⚙️ Settings & Info</h2>", unsafe_allow_html=True)
    st.markdown("---")
    
    with st.expander("ℹ️ About This Bot", expanded=True):
        st.markdown(
            "**Gita Wisdom Bot** brings ancient spiritual guidance into the digital age. "
            "Powered by **Hybrid Retrieval-Augmented Generation (RAG)**, this app:\n\n"
            "- Retrieves verses from the Bhagavad Gita\n"
            "- Detects your emotional concern\n"
            "- Provides Krishna-style wisdom instantly\n"
            "- Runs completely offline (no API costs)\n"
        )
    
    with st.expander("🎚️ Advanced Settings"):
        st.session_state.word_limit = st.slider(
            "Response Length:",
            min_value=50,
            max_value=200,
            value=100,
            step=10,
            help="Control the verbosity of Krishna's guidance"
        )
        
        if st.button("🗑️ Clear Chat History", use_container_width=True):
            st.session_state.messages = []
            st.success("Chat history cleared! 🙏")
    
    st.markdown("---")
    st.markdown("<h3 style='text-align: center; color: #E0C097;'>👋 Connect with Developer</h3>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("[🔗 GitHub](https://github.com/roy-deblina)")
    with col2:
        st.markdown("[💼 LinkedIn](https://www.linkedin.com/in/deblina555/)")
    with col3:
        st.markdown('<a href="mailto:111deblina@gmail.com" style="color: #D4A574; text-decoration: none; font-size: 1rem;">✉️ Email</a>', unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown(
        "<p style='text-align: center; color: #8B7355; font-size: 0.85rem;'>"
        "Built with AI & Wisdom<br><br>"
        "Created by <b>Deblina Roy</b><br>"
        "© 2026"
        "</p>",
        unsafe_allow_html=True
    )

for message in st.session_state.messages:
    with st.chat_message(message["role"], avatar=message.get("avatar", None)):
        st.write(message["content"])
        if message.get("verse"):
            v = message["verse"]
            st.markdown(f"""
            <div class="citation-card">
            "{v['text']}"
            <div class="verse-reference">
            — Bhagavad Gita {v['chapter']}.{v['verse']}
            </div>
            </div>
            """, unsafe_allow_html=True)

st.markdown("---")
st.markdown("<h3 style='text-align: center; color: #B8860B; margin-top: 2rem;'>✨ Discover Krishna's Wisdom</h3>", unsafe_allow_html=True)

# Interactive Discovery Chips
chip_questions = [
    ("🧘", "How to meditate?", "How does the Gita teach meditation and mindfulness?"),
    ("💼", "Success at work?", "What does the Gita say about professional excellence and career?"),
    ("❤️", "Meaning of love?", "Explain the different types of love and devotion in Bhakti Yoga."),
    ("⚔️", "Facing challenges?", "How should one overcome adversity and obstacles in life?"),
]

col1, col2 = st.columns(2)
for idx, (emoji, label, full_q) in enumerate(chip_questions):
    col = col1 if idx % 2 == 0 else col2
    if col.button(f"{emoji} {label}", key=f"chip_{idx}", use_container_width=True):
        st.session_state.prompt = full_q

st.markdown("---")

prompt = st.chat_input("Ask Krishna for guidance...")

if prompt or ("prompt" in st.session_state and st.session_state.prompt):
    if "prompt" in st.session_state and st.session_state.prompt:
        prompt = st.session_state.prompt
        st.session_state.prompt = None
    
    st.session_state.messages.append({
        "role": "user",
        "content": prompt,
        "avatar": "👤"
    })
    
    with st.chat_message("user", avatar="👤"):
        st.write(prompt)
    
    with st.spinner("Krishna is reflecting..."):
        verses = retrieve_verses(prompt, top_k=2)
        response = generate_response(prompt, verses, st.session_state.word_limit)
        time.sleep(0.3)
    
    verse_data = verses[0] if verses else None
    
    st.session_state.messages.append({
        "role": "assistant",
        "content": response,
        "avatar": "🕉️",
        "verse": verse_data
    })
    
    with st.chat_message("assistant", avatar="🕉️"):
        st.write(response)
        if verse_data:
            st.markdown(f"""
            <div class="citation-card">
            "{verse_data['text']}"
            <div class="verse-reference">
            — Bhagavad Gita {verse_data['chapter']}.{verse_data['verse']}
            </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Add copy button
            if st.button("📋 Copy Verse", key=f"copy_response_{verse_data['chapter']}_{verse_data['verse']}", help="Copy to clipboard"):
                st.toast("Verse copied to clipboard! ✨", icon="✅")
    
    if analytics:
        try:
            analytics.record_query_click(prompt, session_id, 1, 0.9, 0.1)
        except:
            pass
    
    st.rerun()

st.markdown("---")
st.markdown("""
    <div style="text-align: center; padding: 2rem 0; color: #8B7355;">
    <p style="font-size: 0.95rem;">
    Built with <span style="color: #D4A574;">❤️</span> using timeless wisdom + advanced AI
    </p>
    <p style="font-size: 0.85rem; margin-top: 0.5rem;">
    <b>Gita Wisdom Bot</b> ✨ Created by <b>Deblina Roy</b><br>
    © 2026
    </p>
    </div>
""", unsafe_allow_html=True)
