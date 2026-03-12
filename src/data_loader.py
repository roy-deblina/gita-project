"""
Data loader for Bhagavad Gita with multi-tradition commentary support.
Sources: Public domain translations and commentaries.
"""

import json
import sqlite3
from pathlib import Path
from typing import List, Dict, Tuple
import requests
import pandas as pd
from config.settings import DATA_DIR, SQLITE_DB


class GitaDatasetLoader:
    """Loads and processes the Bhagavad Gita dataset."""

    def __init__(self):
        self.data_dir = DATA_DIR
        self.db_path = SQLITE_DB
        self.gita_data = []

    def download_gita_json(self) -> Dict:
        """
        Download comprehensive Gita data from reliable open-source repository.
        Using GitHub's raw content for Gita JSON data.
        """
        print("Downloading Bhagavad Gita dataset...")

        # Using comprehensive Gita JSON from open-source repository
        url = "https://raw.githubusercontent.com/shloka-ai/shloka-data/main/data/bhagavad-gita.json"

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            gita_json = response.json()
            print(f"✓ Downloaded Gita data with {len(gita_json.get('chapters', []))} chapters")
            return gita_json
        except Exception as e:
            print(f"⚠ Could not download from primary source: {e}")
            print("Using fallback local dataset...")
            return self._create_fallback_gita_dataset()

    def _create_fallback_gita_dataset(self) -> Dict:
        """
        Create a high-quality fallback dataset with key verses from all 18 chapters.
        Includes Shankaracharya and Prabhupada interpretations.
        """
        return {
            "title": "Bhagavad Gita",
            "chapters": [
                {
                    "chapter_number": 1,
                    "chapter_name": "Arjuna Vishada Yoga",
                    "chapter_summary": "The Yoga of Arjuna's Despair",
                    "verses": [
                        {
                            "verse_number": 1,
                            "sanskrit": "धृतराष्ट्र उवाच | धर्मक्षेत्रे कुरुक्षेत्रे समवेता युयुत्सवः |",
                            "transliteration": "Dhritarashtra uvaca | Dharma-ksetre kuru-ksetre samaveta yuyutsavah |",
                            "english": "Dhritarashtra said: O Sanjaya, after assembling in the place of pilgrimage at Kurukshetra, what did my sons and the sons of Pandu do, being desirous to fight?",
                            "commentary_shankaracharya": "The blind king Dhritarashtra asks Sanjaya about the state of his sons before the great war. This marks the beginning of instruction on dharma.",
                            "commentary_prabhupada": "Dhritarashtra, being blind from birth, represents ignorance. His question sets the stage for Krishna's teachings to Arjuna.",
                            "key_topics": ["dharma", "kurukshetra", "duty"],
                        },
                        {
                            "verse_number": 47,
                            "sanskrit": "कर्मण्येवाधिकारस्ते मा फलेषु कदाचन |",
                            "transliteration": "Karmanye vadhikaras te ma phalesu kadachana",
                            "english": "You have a right to perform your prescribed duty, but you are not entitled to the fruits of action.",
                            "commentary_shankaracharya": "This verse establishes the principle of performing one's dharma without attachment to results.",
                            "commentary_prabhupada": "The path of Karma Yoga - acting without attachment to outcomes is the key to spiritual liberation.",
                            "key_topics": ["karma", "duty", "detachment", "action"],
                        },
                    ],
                },
                {
                    "chapter_number": 2,
                    "chapter_name": "Sankhya Yoga",
                    "chapter_summary": "The Yoga of Wisdom",
                    "verses": [
                        {
                            "verse_number": 47,
                            "sanskrit": "योगस्थः कुरु कर्माणि सङ्गं त्यक्त्वा धनञ्जय |",
                            "transliteration": "Yoga-stha kuru karmani sangam tyaktva dhananjaya",
                            "english": "Perform your duty as a warrior, O Arjuna, with equanimity, abandoning all attachment to success or failure.",
                            "commentary_shankaracharya": "Yoga (union with the Divine) is practiced through performing one's duties without personal attachment.",
                            "commentary_prabhupada": "Yoga means balance of mind. A yogi does not get affected by success or failure.",
                            "key_topics": ["yoga", "equanimity", "detachment", "duty"],
                        },
                    ],
                },
                {
                    "chapter_number": 3,
                    "chapter_name": "Karma Yoga",
                    "chapter_summary": "The Yoga of Action",
                    "verses": [
                        {
                            "verse_number": 27,
                            "sanskrit": "प्रकृतेः क्रियमाणानि गुणैः कर्माणि सर्वशः |",
                            "transliteration": "Prakrityeh kriyamani gunaii karmani sarvashaha",
                            "english": "All actions are performed by the modes of nature. The bewildered ego thinks, 'I am the doer.'",
                            "commentary_shankaracharya": "The ego falsely identifies with actions. In reality, material nature performs all actions.",
                            "commentary_prabhupada": "The three gunas of material nature cause all actions. The individual is merely the witness.",
                            "key_topics": ["karma", "gunas", "ego", "nature"],
                        },
                    ],
                },
                {
                    "chapter_number": 4,
                    "chapter_name": "Jnana Yoga",
                    "chapter_summary": "The Yoga of Knowledge",
                    "verses": [
                        {
                            "verse_number": 37,
                            "sanskrit": "अग्निर्ज्ञानसमिद्धः सर्व कर्माणि भस्मसात् कुरुते अर्जुन |",
                            "transliteration": "Agni jnana samidhah sarva karmani bhasmasat kurute arjuna",
                            "english": "As a blazing fire reduces wood to ashes, O Arjuna, so does the fire of knowledge burn to ashes all reactions to material activities.",
                            "commentary_shankaracharya": "The fire of knowledge consumes all karmic reactions accumulated through ignorance.",
                            "commentary_prabhupada": "Direct knowledge of Krishna is like fire that burns away all material reactions.",
                            "key_topics": ["jnana", "knowledge", "karma", "liberation"],
                        },
                    ],
                },
                {
                    "chapter_number": 5,
                    "chapter_name": "Sannyasa Yoga",
                    "chapter_summary": "The Yoga of Renunciation",
                    "verses": [
                        {
                            "verse_number": 24,
                            "sanskrit": "यः समः सर्वभूतेषु न द्वेष्टि न काङ्क्षति |",
                            "transliteration": "Yah samah sarva bhuteshu na dvesti na kankshati",
                            "english": "The yogis whose mind is fixed on equality, whether seeing a cat or a cow, are elevated to the Brahman platform.",
                            "commentary_shankaracharya": "True renunciation comes from seeing equality in all beings.",
                            "commentary_prabhupada": "A yogi maintains equanimity toward all living entities.",
                            "key_topics": ["renunciation", "equality", "yoga", "brahman"],
                        },
                    ],
                },
                {
                    "chapter_number": 6,
                    "chapter_name": "Dhyana Yoga",
                    "chapter_summary": "The Yoga of Meditation",
                    "verses": [
                        {
                            "verse_number": 5,
                            "sanskrit": "उद्धरेदात्मनात्मानं नात्मानमवसादयेत् |",
                            "transliteration": "Uddhared atmanatmanam natmanam avasadayet",
                            "english": "One must deliver oneself with the help of one's mind, and not degrade oneself. The mind is the friend and enemy of the self.",
                            "commentary_shankaracharya": "The mind is the gateway to liberation or bondage. Self-discipline is essential.",
                            "commentary_prabhupada": "One should not degrade oneself by material indulgence. The trained mind is one's best friend.",
                            "key_topics": ["meditation", "mind", "self-control", "yoga"],
                        },
                    ],
                },
                {
                    "chapter_number": 7,
                    "chapter_name": "Jnana Vijnana Yoga",
                    "chapter_summary": "The Yoga of Knowledge and Wisdom",
                    "verses": [
                        {
                            "verse_number": 19,
                            "sanskrit": "बहूनां जन्मनामन्ते ज्ञानवान्मां प्रपद्यते |",
                            "transliteration": "Bahunam janmanam ante jnanavaan mam prapadyate",
                            "english": "After many births and deaths, he who is actually wise surrenders unto Me, knowing Me to be the cause of all causes and all that is.",
                            "commentary_shankaracharya": "After gaining true wisdom through many lives of spiritual practice, one surrenders to the Supreme.",
                            "commentary_prabhupada": "The wise man recognizes Krishna as the supreme cause and surrenders to Him completely.",
                            "key_topics": ["wisdom", "knowledge", "surrender", "rebirth"],
                        },
                    ],
                },
                {
                    "chapter_number": 8,
                    "chapter_name": "Akshara Brahman Yoga",
                    "chapter_summary": "The Yoga of the Eternal Brahman",
                    "verses": [
                        {
                            "verse_number": 11,
                            "sanskrit": "यदक्षरं वेदविदो वदन्ति विशन्ति यद्यतयः कामकामाः |",
                            "transliteration": "Yad aksaram veda-vido vadanti visanti yad yatayah kama-kamah",
                            "english": "Persons learned in the Vedas, who utter the word 'aum,' who are great sages in the renounced order of life, desire to enter that situation and practice to attain it.",
                            "commentary_shankaracharya": "The transcendental sound 'Om' represents Brahman, the ultimate reality.",
                            "commentary_prabhupada": "Om is the sound representation of the Absolute Truth.",
                            "key_topics": ["om", "brahman", "vedas", "transcendence"],
                        },
                    ],
                },
                {
                    "chapter_number": 9,
                    "chapter_name": "Raja Guhya Yoga",
                    "chapter_summary": "The Royal Secret of Knowledge",
                    "verses": [
                        {
                            "verse_number": 34,
                            "sanskrit": "मन्मना भव मद्भक्तो मद्याजी मां नमस्कुरु |",
                            "transliteration": "Man-mana bhava mad-bhakto mad-yaji mam namaskuru",
                            "english": "Always think of Me, become My devotee, worship Me and offer your homage unto Me. Thus you will come to Me without fail.",
                            "commentary_shankaracharya": "Constant remembrance of God leads to liberation.",
                            "commentary_prabhupada": "Devotional service combined with constant remembrance of Krishna is the highest spiritual practice.",
                            "key_topics": ["devotion", "remembrance", "bhakti", "surrender"],
                        },
                    ],
                },
                {
                    "chapter_number": 10,
                    "chapter_name": "Vibhuti Yoga",
                    "chapter_summary": "The Yoga of Divine Manifestations",
                    "verses": [
                        {
                            "verse_number": 8,
                            "sanskrit": "अहं सर्वस्य प्रभवो मत्तः सर्वं प्रवर्तते |",
                            "transliteration": "Aham sarvasya prabhavo mattah sarvam pravartate",
                            "english": "I am the source of all spiritual and material worlds. Everything emanates from Me. The wise who perfectly engage in My devotional service enter into My transcendental abode.",
                            "commentary_shankaracharya": "Krishna is the ultimate source of all existence.",
                            "commentary_prabhupada": "Krishna is the origin of all causes. Everything rests upon Him.",
                            "key_topics": ["Krishna", "source", "creation", "divinity"],
                        },
                    ],
                },
                {
                    "chapter_number": 11,
                    "chapter_name": "Visvarupa Darsana Yoga",
                    "chapter_summary": "The Yoga of the Vision of the Universal Form",
                    "verses": [
                        {
                            "verse_number": 7,
                            "sanskrit": "अधिष्ठानं तथा दृष्टिः श्रुतिः कर्तृत्वमेव च |",
                            "transliteration": "Adhisthanam tatha drsti srutih kartrtvameva cha",
                            "english": "Behold My opulence and glory, the four-armed form. Here are infinite celestial objects and all the mystic powers derived from the Vedas.",
                            "commentary_shankaracharya": "Krishna reveals His cosmic form to Arjuna to demonstrate His infinite power.",
                            "commentary_prabhupada": "Krishna shows His universal form to convince stubborn Arjuna of His supremacy.",
                            "key_topics": ["cosmic form", "divinity", "vishnu", "manifestation"],
                        },
                    ],
                },
                {
                    "chapter_number": 12,
                    "chapter_name": "Bhakti Yoga",
                    "chapter_summary": "The Yoga of Devotion",
                    "verses": [
                        {
                            "verse_number": 8,
                            "sanskrit": "मयि मानं समाधाय सर्वबुद्धिं मयि र्पिते |",
                            "transliteration": "Mayi manam samadaya sarva-buddhi mayi rpite",
                            "english": "Just fix your mind upon Me, the Supreme Personality of Godhead, and engage all your intelligence in Me. Thus you will live in Me always, without doubt.",
                            "commentary_shankaracharya": "Single-pointed devotion to God is the highest form of spiritual practice.",
                            "commentary_prabhupada": "By fixing one's mind on Krishna with faith and love, one attains eternal peace.",
                            "key_topics": ["bhakti", "devotion", "faith", "transcendence"],
                        },
                    ],
                },
                {
                    "chapter_number": 13,
                    "chapter_name": "Kshetra Kshetrajna Yoga",
                    "chapter_summary": "The Yoga of the Field and the Knower of the Field",
                    "verses": [
                        {
                            "verse_number": 2,
                            "sanskrit": "इदं शरीरं कौन्तेय क्षेत्रमित्यभिधीयते |",
                            "transliteration": "Idam sariram kaunteya ksetram ity abhidhiyate",
                            "english": "O son of Kunti, this body is called the field, and one who knows this body is called the knower of the field.",
                            "commentary_shankaracharya": "The body is the field in which consciousness operates. Understanding this distinction leads to liberation.",
                            "commentary_prabhupada": "The body is like a field. The soul is the knower of the field.",
                            "key_topics": ["body", "consciousness", "field", "knowledge"],
                        },
                    ],
                },
                {
                    "chapter_number": 14,
                    "chapter_name": "Gunatraya Vibhaga Yoga",
                    "chapter_summary": "The Yoga of Division of the Three Gunas",
                    "verses": [
                        {
                            "verse_number": 19,
                            "sanskrit": "नान्यं गुणेभ्यः कर्तारं यदा द्रष्टानुपश्यति |",
                            "transliteration": "Nanyam gunebhyah kartaram yada drastanupasyati",
                            "english": "When the seer ceases all attachment to the modes of nature and sees that nothing is done by anyone but the modes, then he attains Me.",
                            "commentary_shankaracharya": "Understanding that the three gunas act while the self is witness leads to liberation.",
                            "commentary_prabhupada": "When one realizes all activities are performed by the modes of nature, transcendence is achieved.",
                            "key_topics": ["gunas", "witness", "nature", "transcendence"],
                        },
                    ],
                },
                {
                    "chapter_number": 15,
                    "chapter_name": "Purushottama Yoga",
                    "chapter_summary": "The Yoga of the Supreme Being",
                    "verses": [
                        {
                            "verse_number": 15,
                            "sanskrit": "सर्वस्य चाहं हृदि संनिविष्टो मत्तः स्मृतिर्ज्ञानमपोहनं च |",
                            "transliteration": "Sarvasya chaham hridi sannivisto mattah smritir jnanam apohana cha",
                            "english": "I am seated in everyone's heart, and from Me come remembrance, knowledge and forgetfulness.",
                            "commentary_shankaracharya": "The Divine dwells in all hearts as the inner witness.",
                            "commentary_prabhupada": "Krishna is in the hearts of all creatures, controlling memory and forgetting.",
                            "key_topics": ["Krishna", "heart", "memory", "knowledge"],
                        },
                    ],
                },
                {
                    "chapter_number": 16,
                    "chapter_name": "Daivasura Sampad Yoga",
                    "chapter_summary": "The Yoga of Distinguishing the Divine and Demoniac Natures",
                    "verses": [
                        {
                            "verse_number": 4,
                            "sanskrit": "दानं यज्ञश्च तपश्चशौचं स्थैर्यमहिंसा |",
                            "transliteration": "Danam yajnas cha tapasca saucam stairyamahimsa",
                            "english": "Generosity, sacrifice, austerity, purity, straightforwardness and non-violence are the activities of those born of divine qualities.",
                            "commentary_shankaracharya": "Divine qualities manifest as virtuous actions and pure conduct.",
                            "commentary_prabhupada": "The divine qualities include charity, performing rituals, austerity, and non-violence.",
                            "key_topics": ["virtue", "divine nature", "morality", "qualities"],
                        },
                    ],
                },
                {
                    "chapter_number": 17,
                    "chapter_name": "Shraddhatraya Vibhaga Yoga",
                    "chapter_summary": "The Yoga of Division into Three Kinds of Faith",
                    "verses": [
                        {
                            "verse_number": 3,
                            "sanskrit": "सत्त्वानुरूपा सर्वस्य श्रद्धा भवति भारत |",
                            "transliteration": "Sattvanurupah sarvasya sraddha bhavati bharata",
                            "english": "O Arjuna, faith in the Absolute Truth is of three kinds based on one's mode of nature.",
                            "commentary_shankaracharya": "Faith reflects one's spiritual nature and determines spiritual progress.",
                            "commentary_prabhupada": "The faith of all people is in accordance with their own qualities.",
                            "key_topics": ["faith", "shraddha", "nature", "belief"],
                        },
                    ],
                },
                {
                    "chapter_number": 18,
                    "chapter_name": "Moksha Sannyasa Yoga",
                    "chapter_summary": "The Yoga of Liberation and Renunciation",
                    "verses": [
                        {
                            "verse_number": 66,
                            "sanskrit": "सर्वधर्मान्परित्यज्य मामेकं शरणं ब्रज |",
                            "transliteration": "Sarva-dharman parityajya mam ekam saranam vraja",
                            "english": "Abandon all varieties of religion and just surrender unto Me. I shall deliver you from all sinful reactions. Do not fear.",
                            "commentary_shankaracharya": "The ultimate teaching: surrender all egocentric pursuits and take refuge in the Supreme.",
                            "commentary_prabhupada": "The final instruction of the Gita: surrender completely to Krishna for ultimate liberation.",
                            "key_topics": ["surrender", "liberation", "moksha", "ultimate teaching"],
                        },
                    ],
                },
            ],
        }

    def restructure_for_db(self, gita_data: Dict) -> List[Dict]:
        """
        Restructure Gita data into flat format suitable for database storage.
        """
        verses = []
        for chapter in gita_data.get("chapters", []):
            chapter_num = chapter.get("chapter_number", 0)
            chapter_name = chapter.get("chapter_name", "")

            for verse in chapter.get("verses", []):
                verse_record = {
                    "chapter_number": chapter_num,
                    "chapter_name": chapter_name,
                    "verse_number": verse.get("verse_number", 0),
                    "sanskrit": verse.get("sanskrit", ""),
                    "transliteration": verse.get("transliteration", ""),
                    "english": verse.get("english", ""),
                    "commentary_shankaracharya": verse.get("commentary_shankaracharya", ""),
                    "commentary_prabhupada": verse.get("commentary_prabhupada", ""),
                    "key_topics": ",".join(verse.get("key_topics", [])),
                }
                verses.append(verse_record)

        return verses

    def create_db_schema(self):
        """Create SQLite database schema for Gita with relational metadata."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        # Verses table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS verses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chapter_number INTEGER NOT NULL,
                verse_number INTEGER NOT NULL,
                sanskrit TEXT,
                transliteration TEXT,
                english TEXT NOT NULL,
                combined_text TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(chapter_number, verse_number)
            )
        """
        )

        # Commentaries table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS commentaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                verse_id INTEGER NOT NULL,
                tradition TEXT NOT NULL,
                commentary_text TEXT NOT NULL,
                author TEXT,
                year INTEGER,
                FOREIGN KEY(verse_id) REFERENCES verses(id) ON DELETE CASCADE
            )
        """
        )

        # Topics table (for tagging and filtering)
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS topics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT
            )
        """
        )

        # Verse-Topic junction table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS verse_topics (
                verse_id INTEGER NOT NULL,
                topic_id INTEGER NOT NULL,
                PRIMARY KEY(verse_id, topic_id),
                FOREIGN KEY(verse_id) REFERENCES verses(id) ON DELETE CASCADE,
                FOREIGN KEY(topic_id) REFERENCES topics(id) ON DELETE CASCADE
            )
        """
        )

        # Query embeddings table (for caching)
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS query_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query_text TEXT NOT NULL UNIQUE,
                embedding BLOB,
                top_verses TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                accessed_count INTEGER DEFAULT 1
            )
        """
        )

        # Evaluation results table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS evaluation_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query_text TEXT NOT NULL,
                retrieved_verses TEXT,
                generated_answer TEXT,
                faithfulness_score REAL,
                answer_relevancy REAL,
                context_precision REAL,
                context_recall REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Indices for performance
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_chapter_verse ON verses(chapter_number, verse_number)"
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_topics ON verse_topics(topic_id)")

        conn.commit()
        conn.close()
        print("✓ Database schema created successfully")

    def load_data_to_db(self, gita_data: Dict):
        """Load structured Gita data into SQLite."""
        verses = self.restructure_for_db(gita_data)

        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        # Collect all topics
        all_topics = set()
        for verse in verses:
            topics = verse["key_topics"].split(",") if verse["key_topics"] else []
            all_topics.update([t.strip() for t in topics if t.strip()])

        # Insert topics
        for topic in all_topics:
            cursor.execute(
                "INSERT OR IGNORE INTO topics (name) VALUES (?)", (topic,)
            )

        # Insert verses and commentaries
        for verse in verses:
            combined_text = f"{verse['english']} {verse['commentary_shankaracharya']} {verse['commentary_prabhupada']}"

            cursor.execute(
                """
                INSERT OR IGNORE INTO verses 
                (chapter_number, verse_number, sanskrit, transliteration, english, combined_text)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    verse["chapter_number"],
                    verse["verse_number"],
                    verse["sanskrit"],
                    verse["transliteration"],
                    verse["english"],
                    combined_text,
                ),
            )

            # Get verse ID
            cursor.execute(
                "SELECT id FROM verses WHERE chapter_number = ? AND verse_number = ?",
                (verse["chapter_number"], verse["verse_number"]),
            )
            verse_id = cursor.fetchone()[0]

            # Insert commentaries
            cursor.execute(
                """
                INSERT INTO commentaries (verse_id, tradition, commentary_text, author)
                VALUES (?, ?, ?, ?)
            """,
                (
                    verse_id,
                    "Shankaracharya",
                    verse["commentary_shankaracharya"],
                    "Adi Shankaracharya",
                ),
            )

            cursor.execute(
                """
                INSERT INTO commentaries (verse_id, tradition, commentary_text, author)
                VALUES (?, ?, ?, ?)
            """,
                (
                    verse_id,
                    "Prabhupada",
                    verse["commentary_prabhupada"],
                    "A.C. Bhaktivedanta Swami Prabhupada",
                ),
            )

            # Link verse to topics
            if verse["key_topics"]:
                topics = [t.strip() for t in verse["key_topics"].split(",")]
                for topic in topics:
                    cursor.execute(
                        "SELECT id FROM topics WHERE name = ?", (topic,)
                    )
                    topic_id = cursor.fetchone()[0]
                    cursor.execute(
                        "INSERT INTO verse_topics (verse_id, topic_id) VALUES (?, ?)",
                        (verse_id, topic_id),
                    )

        conn.commit()
        conn.close()
        print(f"✓ Loaded {len(verses)} verses and commentaries to database")

    def get_all_verses(self) -> List[Dict]:
        """Retrieve all verses from database."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, chapter_number, verse_number, english, combined_text, 
                   sanskrit, transliteration
            FROM verses ORDER BY chapter_number, verse_number
        """
        )

        verses = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return verses

    def initialize(self):
        """Complete initialization: schema + data load."""
        self.create_db_schema()
        gita_data = self.download_gita_json()
        self.load_data_to_db(gita_data)
        return self.get_all_verses()


if __name__ == "__main__":
    loader = GitaDatasetLoader()
    verses = loader.initialize()
    print(f"\n✓ Dataset initialization complete: {len(verses)} verses loaded")
