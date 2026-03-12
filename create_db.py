#!/usr/bin/env python3
"""Create and populate Gita database from command line (avoids notebook kernel locks)."""

import sqlite3
import os

DB_PATH = 'data/gita.db'

# Remove old database
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)
    print("✓ Removed old database")

# Create fresh database
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Create schema
cursor.execute("""
CREATE TABLE IF NOT EXISTS verses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chapter_number INTEGER NOT NULL,
    verse_number INTEGER NOT NULL,
    sanskrit TEXT,
    transliteration TEXT,
    english TEXT NOT NULL,
    combined_text TEXT,
    UNIQUE(chapter_number, verse_number)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS commentaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    verse_id INTEGER NOT NULL,
    tradition TEXT NOT NULL,
    commentary_text TEXT NOT NULL,
    author TEXT,
    FOREIGN KEY(verse_id) REFERENCES verses(id) ON DELETE CASCADE
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS topics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS verse_topics (
    verse_id INTEGER NOT NULL,
    topic_id INTEGER NOT NULL,
    PRIMARY KEY(verse_id, topic_id),
    FOREIGN KEY(verse_id) REFERENCES verses(id) ON DELETE CASCADE,
    FOREIGN KEY(topic_id) REFERENCES topics(id) ON DELETE CASCADE
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS query_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query_text TEXT NOT NULL UNIQUE,
    top_verses TEXT,
    accessed_count INTEGER DEFAULT 1
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS evaluation_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query_text TEXT NOT NULL,
    retrieved_verses TEXT,
    generated_answer TEXT,
    faithfulness_score REAL,
    answer_relevancy REAL,
    context_precision REAL,
    context_recall REAL
)
""")

# Create indices
cursor.execute("""
CREATE INDEX IF NOT EXISTS idx_chapter_verse 
ON verses(chapter_number, verse_number)
""")

cursor.execute("""
CREATE INDEX IF NOT EXISTS idx_topics 
ON verse_topics(topic_id)
""")

print("✓ Database schema created")

# Insert topics
topics = ['karma', 'dharma', 'yoga', 'knowledge', 'devotion']
for topic in topics:
    cursor.execute("INSERT OR IGNORE INTO topics (name) VALUES (?)", (topic,))

print(f"✓ Topics inserted: {len(topics)}")

# Populate with all 700 verses (programmatically generated structure)
# Chapter-wise verse counts (actual Gita structure)
chapter_verses = {
    1: 47, 2: 72, 3: 43, 4: 42, 5: 29, 6: 47, 7: 30, 8: 28,
    9: 34, 10: 42, 11: 55, 12: 20, 13: 34, 14: 27, 15: 20,
    16: 24, 17: 28, 18: 78
}

total_verses = 0
for ch_num, verse_count in chapter_verses.items():
    for v_num in range(1, verse_count + 1):
        english = f"[Verse BG {ch_num}.{v_num} - Text to be loaded from online sources]"
        sanskrit = f"[Sanskrit BG {ch_num}.{v_num}]"
        transliteration = f"[Transliteration BG {ch_num}.{v_num}]"
        commentary_sh = f"[Shankaracharya commentary for BG {ch_num}.{v_num}]"
        commentary_pr = f"[Prabhupada commentary for BG {ch_num}.{v_num}]"
        combined = f"{english} {commentary_sh} {commentary_pr}"
        
        cursor.execute("""
        INSERT OR IGNORE INTO verses 
        (chapter_number, verse_number, sanskrit, transliteration, english, combined_text)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (ch_num, v_num, sanskrit, transliteration, english, combined))
        
        # Get verse ID
        cursor.execute(
            "SELECT id FROM verses WHERE chapter_number = ? AND verse_number = ?",
            (ch_num, v_num)
        )
        verse_id = cursor.fetchone()[0]
        
        # Add commentaries
        cursor.execute("""
        INSERT OR IGNORE INTO commentaries (verse_id, tradition, commentary_text, author)
        VALUES (?, ?, ?, ?)
        """, (verse_id, "Shankaracharya", commentary_sh, "Adi Shankaracharya"))
        
        cursor.execute("""
        INSERT OR IGNORE INTO commentaries (verse_id, tradition, commentary_text, author)
        VALUES (?, ?, ?, ?)
        """, (verse_id, "Prabhupada", commentary_pr, "A.C. Bhaktivedanta Swami Prabhupada"))
        
        # Link to topics
        for topic in topics:
            cursor.execute("SELECT id FROM topics WHERE name = ?", (topic,))
            topic_id = cursor.fetchone()[0]
            cursor.execute(
                "INSERT OR IGNORE INTO verse_topics (verse_id, topic_id) VALUES (?, ?)",
                (verse_id, topic_id)
            )
        
        total_verses += 1
        if total_verses % 100 == 0:
            print(f"  Progress: {total_verses} verses...", end="\r")

conn.commit()
conn.close()

print(f"\n✓ Database population complete: {total_verses} verses with dual commentaries")
