"""
Cross-Tradition Analysis Module.
Compares Shankaracharya (Advaita) and Prabhupada (Bhakti) interpretations.
Enriches project by showing philosophical traditions are complementary, not contradictory.
"""

import sqlite3
from typing import List, Dict, Optional, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TraditionAnalyzer:
    """Analyzes and compares different philosophical interpretations of Gita verses."""

    TRADITION_PROFILES = {
        "Shankaracharya": {
            "tradition_name": "Advaita Vedanta",
            "founder": "Adi Shankaracharya (8th century)",
            "key_concepts": ["Self-realization", "Non-duality", "Brahman", "Maya"],
            "emphasis": "Knowledge (Jnana) of the ultimate reality",
            "liberation_path": "Realization that individual self is identical to Brahman",
        },
        "Prabhupada": {
            "tradition_name": "Bhakti Vedanta",
            "founder": "A.C. Bhaktivedanta Swami Prabhupada (20th century)",
            "key_concepts": ["Devotion", "Bhakti", "Krishna", "Service"],
            "emphasis": "Devotional service and love for the Divine",
            "liberation_path": "Eternal loving service to Krishna",
        },
    }

    def __init__(self, db_path: str):
        self.db_path = db_path

    def get_verse_with_commentaries(self, chapter: int, verse: int) -> Optional[Dict]:
        """Retrieve a verse with both tradition commentaries."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT v.id, v.chapter_number, v.verse_number, v.english, v.sanskrit,
                   GROUP_CONCAT(CASE WHEN c.tradition = 'Shankaracharya' THEN c.commentary_text END) as shakara_commentary,
                   GROUP_CONCAT(CASE WHEN c.tradition = 'Prabhupada' THEN c.commentary_text END) as prabhupada_commentary
            FROM verses v
            LEFT JOIN commentaries c ON v.id = c.verse_id
            WHERE v.chapter_number = ? AND v.verse_number = ?
            GROUP BY v.id
        """,
            (chapter, verse),
        )

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return {
            "chapter": row["chapter_number"],
            "verse": row["verse_number"],
            "english": row["english"],
            "sanskrit": row["sanskrit"],
            "shakara_commentary": row["shakara_commentary"],
            "prabhupada_commentary": row["prabhupada_commentary"],
        }

    def analyze_verse_traditions(self, chapter: int, verse: int) -> Dict:
        """
        Comprehensive analysis of how two traditions interpret a verse.
        """
        verse_data = self.get_verse_with_commentaries(chapter, verse)

        if not verse_data:
            return None

        analysis = {
            "verse_reference": f"{chapter}.{verse}",
            "verse_text": verse_data["english"],
            "traditions_compared": [],
        }

        # Analyze Shankaracharya tradition
        if verse_data["shakara_commentary"]:
            analysis["traditions_compared"].append(
                {
                    "tradition": "Shankaracharya (Advaita)",
                    "commentary": verse_data["shakara_commentary"],
                    "profile": self.TRADITION_PROFILES["Shankaracharya"],
                    "interpretation_focus": self._extract_focus(
                        verse_data["shakara_commentary"]
                    ),
                }
            )

        # Analyze Prabhupada tradition
        if verse_data["prabhupada_commentary"]:
            analysis["traditions_compared"].append(
                {
                    "tradition": "Prabhupada (Bhakti Vedanta)",
                    "commentary": verse_data["prabhupada_commentary"],
                    "profile": self.TRADITION_PROFILES["Prabhupada"],
                    "interpretation_focus": self._extract_focus(
                        verse_data["prabhupada_commentary"]
                    ),
                }
            )

        # Find synthesis/commonalities
        if len(analysis["traditions_compared"]) == 2:
            analysis["synthesis"] = self._find_synthesis(
                analysis["traditions_compared"][0],
                analysis["traditions_compared"][1],
            )

        return analysis

    def _extract_focus(self, commentary: str) -> str:
        """Extract the main focus/theme from a commentary."""
        # Simplified extraction - in production, use NLP
        focus_keywords = {
            "self": "Self-Realization and Identity",
            "bhakti": "Devotional Service",
            "knowledge": "Knowledge and Understanding",
            "action": "Action and Duty",
            "surrender": "Surrender and Faith",
            "liberation": "Liberation and Freedom",
            "service": "Service and Duty",
            "love": "Love and Devotion",
        }

        commentary_lower = commentary.lower()
        for keyword, focus in focus_keywords.items():
            if keyword in commentary_lower:
                return focus

        return "Philosophical Interpretation"

    def _find_synthesis(self, interpretation1: Dict, interpretation2: Dict) -> str:
        """Find common ground and synthesis between two traditions."""
        return (
            f"Both {interpretation1['tradition']} and {interpretation2['tradition']} use this verse "
            f"to teach fundamental spiritual truths. While {interpretation1['tradition']} emphasizes "
            f"{interpretation1['interpretation_focus'].lower()}, and {interpretation2['tradition']} "
            f"emphasizes {interpretation2['interpretation_focus'].lower()}, they both point to the "
            "ultimate goal of spiritual realization and direct experience of truth."
        )

    @staticmethod
    def compare_philosophical_approaches() -> Dict:
        """
        Compare the two major traditions in structural terms.
        """
        return {
            "Shankaracharya (Advaita)": {
                "ultimate_reality": "Non-dual Brahman",
                "individual_self": "Maya - an illusion",
                "liberation_means": "Knowledge of Brahman-Atman identity",
                "practice": "Meditation, discrimination, self-inquiry",
                "emphasis": "Knowledge (Jnana)",
            },
            "Prabhupada (Bhakti Vedanta)": {
                "ultimate_reality": "Krishna - the Supreme Person",
                "individual_self": "Eternal individual soul with Krishna",
                "liberation_means": "Loving devotional service",
                "practice": "Chanting, singing, serving Krishna",
                "emphasis": "Devotion (Bhakti)",
            },
            "synthesis": "Both traditions acknowledge the same Vedic scriptures and aim at moksha. "
            "They represent different paths suited to different temperaments and levels of spiritual development.",
        }


class CrossTraditionComparator:
    """Directly compares how different traditions answer the same question."""

    def __init__(self, db_path: str):
        self.analyzer = TraditionAnalyzer(db_path)

    def compare_answers_by_tradition(
        self, question: str, retrieved_verses: List[Dict]
    ) -> Dict:
        """
        Show how different traditions would answer the same question.
        """
        logger.info(f"Comparing traditions for: {question}")

        traditions_responses = {
            "Shankaracharya": self._generate_tradition_response(
                question, retrieved_verses, "Shankaracharya"
            ),
            "Prabhupada": self._generate_tradition_response(
                question, retrieved_verses, "Prabhupada"
            ),
        }

        return {
            "question": question,
            "traditions_compared": traditions_responses,
            "common_ground": self._find_common_ground(traditions_responses),
            "key_differences": self._identify_differences(traditions_responses),
        }

    def _generate_tradition_response(
        self, question: str, verses: List[Dict], tradition: str
    ) -> Dict:
        """Generate an answer emphasizing one tradition's approach."""
        return {
            "tradition": tradition,
            "approach_focus": self.analyzer.TRADITION_PROFILES[tradition]["emphasis"],
            "key_verses": [
                f"Bhagavad Gita {v['chapter']}.{v['verse']}" for v in verses[:3]
            ],
            "philosophical_lens": self.analyzer.TRADITION_PROFILES[tradition][
                "key_concepts"
            ],
        }

    def _find_common_ground(self, traditions_responses: Dict) -> List[str]:
        """Identify what both traditions agree on."""
        commonalities = [
            "Both recognize Bhagavad Gita as authoritative source",
            "Both aim at spiritual liberation and direct realization of truth",
            "Both emphasize transformation of the individual",
            "Both recognize Krishna/Brahman as ultimate reality",
        ]
        return commonalities

    def _identify_differences(self, traditions_responses: Dict) -> List[str]:
        """Highlight key philosophical differences."""
        return [
            "Advaita: Emphasizes non-duality and knowledge of Brahman-Atman identity",
            "Bhakti: Emphasizes eternal distinction between soul and Krishna with loving service",
            "Advaita: Uses logic and discrimination as primary tools",
            "Bhakti: Uses devotion and faith as primary tools",
        ]


class TraditionIntegrator:
    """
    Integrates insights from multiple traditions into a holistic answer.
    This is the "Northwestern academic" approach - scholarly and balanced.
    """

    def __init__(self, analyzer: TraditionAnalyzer):
        self.analyzer = analyzer

    def create_balanced_response(
        self,
        question: str,
        base_answer: str,
        relevant_verses: List[Dict],
    ) -> str:
        """
        Create a response that acknowledges and integrates multiple perspectives.
        """
        response = base_answer + "\n\n"

        if not relevant_verses:
            return response

        # Add tradition context
        response += "---\n\n"
        response += "**Scholarly Note on Traditions:**\n\n"

        # Analyze the primary verses
        primary_verse = relevant_verses[0] if relevant_verses else None
        if primary_verse:
            analysis = self.analyzer.analyze_verse_traditions(
                primary_verse["chapter"], primary_verse["verse"]
            )

            if analysis and analysis.get("synthesis"):
                response += f"The Gita's teaching here is understood through different spiritual traditions:\n\n"
                for trad in analysis.get("traditions_compared", []):
                    response += f"- **{trad['tradition']}**: Emphasizes {trad['interpretation_focus']}\n"
                response += f"\n{analysis['synthesis']}\n\n"

        # Add integration summary
        response += (
            "**Integration**: These traditions represent complementary paths suited to different "
            "temperaments. Modern practitioners often integrate insights from both approaches for a "
            "complete understanding.\n"
        )

        return response


if __name__ == "__main__":
    print("Cross-tradition analysis module loaded")
