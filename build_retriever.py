#!/usr/bin/env python3
"""Build retriever state for FastAPI server."""

import sqlite3
import pickle
import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

print("Building retriever state...")

# Load corpus from SQLite
conn = sqlite3.connect('data/gita.db')
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

print(f"✓ Loaded {len(corpus)} verses")

# Build BM25 index
print("Building BM25 index...")
bm25_index = BM25Okapi(texts_for_bm25)
print(f"✓ BM25 index built with {bm25_index.corpus_size} documents")

# Load embedding model and create embeddings
print("Loading embedding model and creating corpus embeddings...")
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
english_texts = [v['english'] for v in corpus]
corpus_embeddings = embedding_model.encode(english_texts, convert_to_tensor=True, show_progress_bar=True)
print(f"✓ Embeddings created: {corpus_embeddings.shape}")

# Save state
retriever_state = {
    'corpus': corpus,
    'bm25_index': bm25_index,
    'embedding_model': embedding_model,
    'corpus_embeddings': corpus_embeddings
}

with open('data/retriever_state.pkl', 'wb') as f:
    pickle.dump(retriever_state, f)

print("✓ Retriever state saved to data/retriever_state.pkl")
print("\nReady to start FastAPI server!")
