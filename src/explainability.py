"""
Explainability and Citation Tracking Module.
Provides detailed reasoning chains and verse citations for transparency.
Implements techniques from MufassirQAS paper for religious RAG transparency.
"""

import json
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class VerseChain:
    """Represents a single verse in the reasoning chain."""
    chapter: int
    verse: int
    english_text: str
    relevance_reason: str
    confidence: float
    tradition: Optional[str] = None
    commentary: Optional[str] = None


@dataclass
class ReasoningStep:
    """Single step in the multi-step reasoning process."""
    step_number: int
    step_name: str
    action: str
    input_data: str
    output_data: str
    verses_involved: List[VerseChain]
    intermediate_result: str


@dataclass
class ExplainableRAGResponse:
    """Complete response with full explainability."""
    question: str
    final_answer: str
    confidence_score: float
    primary_verses: List[VerseChain]
    supporting_verses: List[VerseChain]
    reasoning_steps: List[ReasoningStep]
    potential_biases: List[str]
    alternative_perspectives: List[str]


class CitationTracker:
    """
    Tracks and highlights how each verse contributes to the final answer.
    Implements citation transparency from MufassirQAS.
    """

    def __init__(self):
        self.citations = []
        self.verse_usage_map = {}

    def add_citation(
        self,
        verse_id: tuple,
        usage_context: str,
        confidence: float,
        tradition: str = None,
    ):
        """Record when and how a verse is used."""
        citation = {
            "verse_id": verse_id,
            "usage_context": usage_context,
            "confidence": confidence,
            "tradition": tradition,
            "timestamp": None,  # Would be filled during actual execution
        }
        self.citations.append(citation)

        # Track verse usage count
        if verse_id not in self.verse_usage_map:
            self.verse_usage_map[verse_id] = {"count": 0, "contexts": []}

        self.verse_usage_map[verse_id]["count"] += 1
        self.verse_usage_map[verse_id]["contexts"].append(usage_context)

    def get_verse_contribution(self, verse_id: tuple) -> Dict:
        """Get contribution metrics for a specific verse."""
        if verse_id not in self.verse_usage_map:
            return None

        return {
            "verse_id": verse_id,
            "usage_count": self.verse_usage_map[verse_id]["count"],
            "contexts": self.verse_usage_map[verse_id]["contexts"],
        }

    def generate_citation_report(self) -> str:
        """Generate a detailed citation report."""
        report = "Citation Report\n"
        report += "=" * 60 + "\n\n"

        for verse_id, usage in self.verse_usage_map.items():
            chapter, verse = verse_id
            report += f"Bhagavad Gita {chapter}.{verse}\n"
            report += f"  Usage Count: {usage['count']}\n"
            report += f"  Contexts:\n"
            for ctx in usage["contexts"]:
                report += f"    - {ctx}\n"
            report += "\n"

        return report


class ExplainabilityEngine:
    """
    Main engine for generating explainable RAG responses.
    Shows reasoning chain and verse contributions.
    """

    def __init__(self):
        self.citation_tracker = CitationTracker()

    def create_explainable_response(
        self,
        question: str,
        answer: str,
        confidence_score: float,
        primary_verses: List[Dict],
        supporting_verses: List[Dict],
        reasoning_steps: List[Dict],
        agent_output: Dict = None,
    ) -> ExplainableRAGResponse:
        """
        Create a fully explainable response with citations and reasoning.
        """
        logger.info("Creating explainable RAG response...")

        # Convert verse dicts to VerseChain objects
        primary_chains = self._convert_to_chains(primary_verses, "primary")
        supporting_chains = self._convert_to_chains(supporting_verses, "supporting")

        # Create reasoning steps with verse involvement
        explicit_steps = self._create_reasoning_steps(reasoning_steps, agent_output)

        # Identify potential biases
        biases = self._identify_potential_biases(question, answer, primary_verses)

        # Find alternative perspectives from different traditions
        alternatives = self._find_alternative_perspectives(primary_verses)

        response = ExplainableRAGResponse(
            question=question,
            final_answer=answer,
            confidence_score=confidence_score,
            primary_verses=primary_chains,
            supporting_verses=supporting_chains,
            reasoning_steps=explicit_steps,
            potential_biases=biases,
            alternative_perspectives=alternatives,
        )

        logger.info("✓ Explainable response created")
        return response

    def _convert_to_chains(self, verses: List[Dict], verse_type: str) -> List[VerseChain]:
        """Convert verse dicts to VerseChain objects with metadata."""
        chains = []

        for verse in verses:
            chain = VerseChain(
                chapter=verse["chapter"],
                verse=verse["verse"],
                english_text=verse.get("english", "")[:300],  # Limit length
                relevance_reason=f"Related to {verse_type} aspect of query",
                confidence=verse.get("relevance_score", 0.5),
            )
            chains.append(chain)
            self.citation_tracker.add_citation(
                (verse["chapter"], verse["verse"]),
                verse_type,
                chain.confidence,
            )

        return chains

    def _create_reasoning_steps(
        self, reasoning_chain: List[str], agent_output: Dict = None
    ) -> List[ReasoningStep]:
        """Create detailed reasoning steps from the agent pipeline."""
        steps = []

        step_templates = {
            0: {
                "name": "Query Decomposition",
                "action": "Break down user question into philosophical concepts",
            },
            1: {
                "name": "Semantic Search",
                "action": "Retrieve relevant verses using hybrid search",
            },
            2: {
                "name": "Relevance Filtering",
                "action": "Grade and filter verses for relevance",
            },
            3: {
                "name": "Answer Generation",
                "action": "Generate answer grounded in retrieved verses",
            },
            4: {
                "name": "Self-Reflection",
                "action": "Evaluate answer quality and confidence",
            },
        }

        for i, chain_item in enumerate(reasoning_chain):
            if i >= len(step_templates):
                break

            template = step_templates[i]
            step = ReasoningStep(
                step_number=i + 1,
                step_name=template["name"],
                action=template["action"],
                input_data=f"Query or intermediate result {i}",
                output_data=chain_item,
                verses_involved=[],
                intermediate_result=chain_item,
            )
            steps.append(step)

        return steps

    def _identify_potential_biases(
        self, question: str, answer: str, verses: List[Dict]
    ) -> List[str]:
        """
        Identify and flag potential biases or incomplete perspectives.
        Based on MufassirQAS ethical prompting strategy.
        """
        biases = []

        # Check if only one tradition represented
        traditions_represented = set()
        for verse in verses:
            if "commentary_shankaracharya" in verse:
                traditions_represented.add("Advaita")
            if "commentary_prabhupada" in verse:
                traditions_represented.add("Bhakti")

        if len(traditions_represented) == 1:
            biases.append(
                "⚠ Answer may reflect only one philosophical tradition. "
                "Consider other perspectives for complete understanding."
            )

        # Check for potential modern bias
        modern_terms = ["career", "job", "business", "stress", "anxiety", "therapy"]
        if any(term in question.lower() for term in modern_terms):
            biases.append(
                "⚠ Question uses modern terminology. Answer is interpretive "
                "application of ancient wisdom to contemporary context."
            )

        # Check if primarily from one chapter
        chapters = [v["chapter"] for v in verses]
        if chapters and max(chapters) - min(chapters) < 2:
            biases.append(
                "⚠ Verses primarily from single chapter(s). "
                "Complete teaching spans all 18 chapters."
            )

        return biases

    def _find_alternative_perspectives(self, verses: List[Dict]) -> List[str]:
        """
        Highlight alternative ways the Gita addresses the same topic.
        Shows different philosophical angles.
        """
        perspectives = []

        if not verses:
            return perspectives

        # Example alternative perspectives
        alternative_paths = {
            "action": [
                "Karma Yoga: Path of Action without attachment",
                "Jnana Yoga: Path of Knowledge and Understanding",
                "Bhakti Yoga: Path of Devotion and Surrender",
            ],
            "peace": [
                "Through understanding the nature of the self (Atman)",
                "Through surrendering to divine will",
                "Through detaching from material desires",
            ],
            "duty": [
                "Duty according to one's nature (caste/varna)",
                "Duty according to one's station in life",
                "Duty to society and dharma",
            ],
        }

        for key, alt_list in alternative_paths.items():
            if any(key in v.get("english", "").lower() for v in verses):
                perspectives.extend(alt_list)

        return perspectives[:3]  # Return top 3 perspectives


class TransparencyReportGenerator:
    """
    Generates detailed transparency reports for stakeholder understanding.
    Ensures interpretability of RAG decisions.
    """

    @staticmethod
    def generate_markdown_report(response: ExplainableRAGResponse) -> str:
        """Generate a detailed markdown report of the response."""
        report = f"# Answer to: \"{response.question}\"\n\n"

        # Main answer
        report += "## Answer\n\n"
        report += f"{response.final_answer}\n\n"

        # Confidence and metrics
        report += "## Confidence & Metrics\n\n"
        report += f"- **Confidence Score**: {response.confidence_score:.2%}\n"

        # Primary verses
        report += "## Primary Reference Verses\n\n"
        for i, verse in enumerate(response.primary_verses, 1):
            report += f"### {i}. Bhagavad Gita {verse.chapter}.{verse.verse}\n\n"
            report += f"**Text**: {verse.english_text}\n\n"
            report += f"**Why referenced**: {verse.relevance_reason}\n\n"

        # Supporting verses
        if response.supporting_verses:
            report += "## Supporting Verses\n\n"
            for i, verse in enumerate(response.supporting_verses, 1):
                report += f"- **Bhagavad Gita {verse.chapter}.{verse.verse}**: {verse.confidence:.0%} relevance\n"
            report += "\n"

        # Reasoning chain
        report += "## Reasoning Process\n\n"
        for step in response.reasoning_steps:
            report += f"### Step {step.step_number}: {step.step_name}\n\n"
            report += f"- **Action**: {step.action}\n"
            report += f"- **Result**: {step.intermediate_result}\n\n"

        # Potential biases
        if response.potential_biases:
            report += "## Important Notes\n\n"
            report += "⚠ **Important Considerations**:\n\n"
            for bias in response.potential_biases:
                report += f"- {bias}\n"
            report += "\n"

        # Alternative perspectives
        if response.alternative_perspectives:
            report += "## Alternative Perspectives\n\n"
            report += "The Gita explores similar topics through multiple lenses:\n\n"
            for i, perspective in enumerate(response.alternative_perspectives, 1):
                report += f"{i}. {perspective}\n"

        return report

    @staticmethod
    def generate_json_report(response: ExplainableRAGResponse) -> str:
        """Generate a machine-readable JSON report."""
        data = {
            "question": response.question,
            "answer": response.final_answer,
            "confidence_score": response.confidence_score,
            "primary_verses": [asdict(v) for v in response.primary_verses],
            "supporting_verses": [asdict(v) for v in response.supporting_verses],
            "reasoning_steps": [asdict(s) for s in response.reasoning_steps],
            "potential_biases": response.potential_biases,
            "alternative_perspectives": response.alternative_perspectives,
        }
        return json.dumps(data, indent=2, default=str)


if __name__ == "__main__":
    engine = ExplainabilityEngine()
    print("Explainability engine module loaded")
