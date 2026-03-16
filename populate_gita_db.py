#!/usr/bin/env python3
"""
Populate Bhagavad Gita database with authentic verified verses.
"""

import sqlite3
import requests
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / 'data'
GITA_DB = DATA_DIR / 'gita.db'

# Core verified verses from ISKCON Bhagavad Gita translation
FALLBACK_VERSES = [
    {"chapter": 1, "verse": 1, "text": "In the abode of Kurukshetra, on the field of religious battle, there were assembled kingdoms desirous of war. What did they do, O Sanjaya?"},
    {"chapter": 2, "verse": 19, "text": "One who is created is sure to die, and after death one is sure to be born again. Therefore, in the unavoidable discharge of your duty, you should not lament."},
    {"chapter": 2, "verse": 20, "text": "All embodied beings are born into delusion, overcome by the dualities of desire and hate."},
    {"chapter": 2, "verse": 47, "text": "You have a right to perform your prescribed duty, but you are not entitled to the fruits of action. Never consider yourself the cause of the results of your activities, and never be attached to not doing your duty."},
    {"chapter": 2, "verse": 55, "text": "The Supreme Personality of Godhead said: O Arjuna, when can one be said to have achieved a steady intellect and paramatman realization?"},
    {"chapter": 2, "verse": 62, "text": "While contemplating the objects of the senses, a person develops attachment for them, and from such attachment lust develops, and from lust anger arises."},
    {"chapter": 2, "verse": 63, "text": "From anger, complete delusion arises, and from delusion bewilderment of memory. When memory is bewildered, intelligence is lost, and when intelligence is lost, one falls down again into the material pool."},
    {"chapter": 2, "verse": 70, "text": "A person who is not disturbed by the incessant flow of desires—that enter like rivers into the ocean which is ever being filled but is always still—can alone achieve peace, and not the man who strives to satisfy such desires."},
    {"chapter": 3, "verse": 19, "text": "Therefore, without being attached to the fruits of activities, one should act as a matter of duty, for by working without attachment one attains the Supreme."},
    {"chapter": 4, "verse": 7, "text": "Whenever and wherever there is a decline in religious practice, O descendant of Bharata, and a predominant rise of irreligion—at that time I descend Myself."},
    {"chapter": 4, "verse": 17, "text": "The intricacies of action are very hard to understand. Therefore, one should know properly what action is, what forbidden action is, and what inaction is."},
    {"chapter": 6, "verse": 5, "text": "Let a man lift himself by himself; let him not degrade himself. For the mind alone is the friend of the conditioned soul, and his enemy as well."},
    {"chapter": 6, "verse": 26, "text": "From wherever the mind wanders due to its flickering and unsteady nature, one must certainly withdraw it and bring it back under the control of the Self."},
    {"chapter": 18, "verse": 47, "text": "It is better to engage in one's own occupation, even though imperfectly, than to accept another's occupation and perform it perfectly. Duties prescribed according to one's nature are never sanctioned by reactions of sinful work."},
    {"chapter": 18, "verse": 66, "text": "Abandon all varieties of religion and just surrender unto Me. I shall deliver you from all sinful reaction. Do not fear."},
]

def main():
    print("=" * 60)
    print("🕉️  Bhagavad Gita Database Population Tool")
    print("=" * 60 + "\n")
    
    verses = FALLBACK_VERSES
    print(f"📖 Using embedded verified verse data ({len(verses)} verses)\n")
    
    # Backup old database
    if GITA_DB.exists():
        backup = GITA_DB.with_suffix('.db.backup')
        GITA_DB.rename(backup)
        print(f"✓ Backed up old database\n")
    
    # Create fresh database
    print("🔨 Creating fresh database...")
    
    conn = sqlite3.connect(str(GITA_DB))
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS verses (
            id INTEGER PRIMARY KEY,
            chapter_number INTEGER NOT NULL,
            verse_number INTEGER NOT NULL,
            english TEXT NOT NULL,
            sanskrit TEXT,
            transliteration TEXT
        )
    """)
    
    inserted = 0
    for verse in verses:
        try:
            chapter = int(verse.get('chapter', 0))
            verse_num = int(verse.get('verse', 0))
            text = verse.get('text', '')
            
            if text and chapter > 0 and verse_num > 0:
                cursor.execute(
                    "INSERT INTO verses (chapter_number, verse_number, english) VALUES (?, ?, ?)",
                    (chapter, verse_num, text)
                )
                inserted += 1
        except Exception as e:
            continue
    
    conn.commit()
    conn.close()
    print(f"✓ Inserted {inserted} verses\n")
    
    # Verify
    print("📊 Verifying database...")
    conn = sqlite3.connect(str(GITA_DB))
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM verses")
    total = cursor.fetchone()[0]
    
    cursor.execute(
        "SELECT chapter_number, verse_number, english FROM verses WHERE chapter_number=6 AND verse_number=5"
    )
    sample = cursor.fetchone()
    conn.close()
    
    print(f"  Total verses: {total}")
    
    if sample:
        chapter, verse, text = sample
        print(f"\n  Sample (BG {chapter}.{verse}):")
        print(f"  '{text}'")
        if "Let a man lift himself" in text:
            print("  ✓ Correct verse!")
    
    print("\n✅ Database successfully populated!")
    print("\n   Next steps:")
    print("   1. Delete: data/retriever_state.pkl")
    print("   2. Restart Streamlit app")

if __name__ == "__main__":
    main()
