"""
Multi-Step Agentic Layer using LangGraph.
Implements: Planner -> Retriever -> Grader -> Answer Generator -> Self-Reflector
"""

import json
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum
import logging

from langchain.prompts import PromptTemplate
from langchain.schema import Document
from langgraph.graph import StateGraph, END
from langgraph.types import BaseModel

from config.settings import LOCAL_LLM_MODEL, LLM_TEMPERATURE, MAX_TOKENS, REFLECTION_THRESHOLD


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgentState(BaseModel):
    """State object passed through the agent pipeline."""
    question: str
    decomposed_goals: List[str] = []
    retrieved_verses: List[Dict] = []
    graded_verses: List[Dict] = []
    generated_answer: Optional[str] = None
    confidence_score: float = 0.0
    reasoning_chain: List[str] = []
    is_relevant: bool = False
    needs_refinement: bool = False
    refined_answer: Optional[str] = None


class VerseGradeEnum(str, Enum):
    RELEVANT = "relevant"
    SOMEWHAT_RELEVANT = "somewhat_relevant"
    NOT_RELEVANT = "not_relevant"


class QueryPlanner:
    """
    Step A: Decomposes complex user questions into sub-goals.
    Example: "How do I handle career stress?" 
    -> ["Find verses on attachment to results", "Find verses on duty", "Find verses on detachment"]
    """

    DECOMPOSITION_PROMPT = """You are an expert in Bhagavad Gita philosophy and interpretation.
    
The user has asked: {question}

Decompose this question into 2-4 specific, concrete sub-goals that represent different aspects of the Gita's teachings relevant to the user's question. 

Focus on:
1. Core philosophical concepts (karma, dharma, bhakti, etc.)
2. Practical applications (duty, action, attachment, results)
3. Spiritual dimensions (enlightenment, detachment, transcendence)

Output as a JSON list of strings, each representing a specific search topic.
Example: ["verses on karma and action", "verses on detachment from results", "verses on duty"]

Question: {question}

Sub-goals (JSON list):"""

    def __init__(self):
        self.prompt = PromptTemplate(
            input_variables=["question"],
            template=self.DECOMPOSITION_PROMPT
        )

    def decompose(self, question: str) -> List[str]:
        """Decompose a question into sub-goals."""
        logger.info(f"Planning: Decomposing question: {question}")

        # For now, use rule-based decomposition (can be replaced with LLM call)
        keywords = question.lower()
        goals = []

        keyword_mappings = {
            "stress|anxiety|worry": [
                "verses on equanimity and mental peace",
                "verses on detachment from results",
                "verses on duty and responsibility"
            ],
            "career|work|job": [
                "verses on karma and action",
                "verses on duty and dharma",
                "verses on performing tasks without attachment"
            ],
            "suffering|pain|struggle": [
                "verses on the nature of suffering",
                "verses on acceptance and surrender",
                "verses on spiritual liberation"
            ],
            "purpose|meaning|life": [
                "verses on dharma and duty",
                "verses on self-realization",
                "verses on the meaning of existence"
            ],
            "death|mortality|afterlife": [
                "verses on the eternal soul",
                "verses on rebirth and cycles",
                "verses on liberation and moksha"
            ],
            "meditation|spirituality|enlightenment": [
                "verses on meditation practices",
                "verses on knowledge and wisdom",
                "verses on pathways to liberation"
            ],
            "devotion|worship|faith": [
                "verses on bhakti and devotion",
                "verses on surrender to the divine",
                "verses on faith and worship"
            ]
        }

        for keywords_pattern, goal_list in keyword_mappings.items():
            if any(kw in keywords for kw in keywords_pattern.split("|")):
                goals.extend(goal_list)

        # If no matches, use generic decomposition
        if not goals:
            goals = [
                "verses relevant to the core question",
                "verses on related philosophical concepts",
                "verses on practical application",
                "verses on spiritual perspective"
            ]

        logger.info(f"Decomposed into {len(goals)} sub-goals")
        return goals[:4]  # Limit to 4 goals


class VerseRetriever:
    """
    Step B: Retrieves verses based on decomposed goals.
    Uses the hybrid retriever to fetch relevant verses.
    """

    def __init__(self, hybrid_retriever):
        self.retriever = hybrid_retriever

    def retrieve_for_goals(self, decomposed_goals: List[str], top_k: int = 5) -> Dict:
        """Retrieve verses for each decomposed goal."""
        logger.info(f"Retrieving verses for {len(decomposed_goals)} goals")

        all_retrieved = {}
        for goal in decomposed_goals:
            results = self.retriever.retrieve(goal, top_k=top_k)
            all_retrieved[goal] = results
            logger.info(f"  Retrieved {len(results)} verses for: {goal}")

        return all_retrieved


class VerseGrader:
    """
    Step C: Grades verses for relevance to the original question.
    Uses a local small model (Llama 3.2 3B equivalent logic).
    """

    GRADING_PROMPT = """You are an expert evaluator of Bhagavad Gita verse relevance.

Original Question: {question}
Verse (Chapter {chapter}, Verse {verse}): {verse_text}

Is this verse relevant and helpful for answering the user's question?

Consider:
1. Direct relevance - does it directly address the question?
2. Conceptual relevance - does it relate to core concepts needed?
3. Practical relevance - can it inform real-world application?

Output ONLY one word: "relevant", "somewhat_relevant", or "not_relevant"
"""

    def __init__(self):
        self.prompt = PromptTemplate(
            input_variables=["question", "chapter", "verse", "verse_text"],
            template=self.GRADING_PROMPT
        )

    def grade(self, question: str, verse: Dict) -> tuple:
        """
        Grade a verse for relevance.
        Returns (grade, confidence_score)
        """
        # Simplified grading logic (replace with LLM call for production)
        verse_text = verse.get("english", "").lower()
        question_lower = question.lower()

        # Check for key concept matches
        keywords_in_verse = set(verse_text.split())
        keywords_in_question = set(question_lower.split())
        overlap = len(keywords_in_verse & keywords_in_question)

        # Score based on overlap
        score = min(overlap / (len(keywords_in_question) + 1), 1.0)

        if score > 0.3:
            grade = VerseGradeEnum.RELEVANT
        elif score > 0.15:
            grade = VerseGradeEnum.SOMEWHAT_RELEVANT
        else:
            grade = VerseGradeEnum.NOT_RELEVANT

        return grade, score

    def grade_verses(self, question: str, verses: List[Dict]) -> List[Dict]:
        """Grade all retrieved verses."""
        logger.info(f"Grading {len(verses)} verses for relevance")

        graded = []
        for verse in verses:
            grade, score = self.grade(question, verse)
            verse["relevance_grade"] = grade
            verse["relevance_score"] = score

            if grade in [VerseGradeEnum.RELEVANT, VerseGradeEnum.SOMEWHAT_RELEVANT]:
                graded.append(verse)
                logger.debug(f"  ✓ Ch{verse['chapter']}.{verse['verse']}: {grade} (score: {score:.2f})")

        logger.info(f"Graded {len(graded)} verses as relevant")
        return graded


class AnswerGenerator:
    """
    Step D: Generates contextual answers using graded verses.
    Ensures citations and maintains scriptural accuracy.
    """

    ANSWER_GENERATION_PROMPT = """You are a wise interpreter of the Bhagavad Gita, known for accuracy and accessibility.

User's Question: {question}

Relevant Verses from the Gita:
{verses_context}

Your task:
1. Provide a thoughtful answer grounded in the cited verses
2. Explain Krishna's teaching in modern context
3. Offer practical guidance for the user's situation
4. Always cite specific verses (format: Chapter.Verse)
5. Maintain the spiritual depth while being relatable

Answer:"""

    def __init__(self):
        self.prompt = PromptTemplate(
            input_variables=["question", "verses_context"],
            template=self.ANSWER_GENERATION_PROMPT
        )

    def format_verses(self, verses: List[Dict]) -> str:
        """Format verses for inclusion in prompt."""
        formatted = []
        for v in verses:
            formatted.append(
                f"**Bhagavad Gita {v['chapter']}.{v['verse']}**\n{v['english']}"
            )
        return "\n\n".join(formatted)

    def generate(self, question: str, graded_verses: List[Dict]) -> str:
        """Generate answer based on graded verses."""
        logger.info(f"Generating answer using {len(graded_verses)} verses")

        if not graded_verses:
            return "I could not find relevant verses to answer your question about this Gita topic. Please rephrase your question and try again."

        verses_text = self.format_verses(graded_verses)

        # Simulated answer generation (replace with actual LLM call)
        answer = self._generate_answer_template(question, graded_verses)
        return answer

    def _generate_answer_template(self, question: str, verses: List[Dict]) -> str:
        """Generate answer using template (demo, replace with LLM)."""
        answer = f"Based on the teachings of Krishna in the Bhagavad Gita:\n\n"

        for i, verse in enumerate(verses[:3], 1):
            answer += f"{i}. From Bhagavad Gita {verse['chapter']}.{verse['verse']}:\n"
            answer += f"   \"{verse['english']}\"\n\n"

        answer += "\nApplied to your question:\n"
        answer += "The Gita teaches that through understanding these principles and applying them with sincerity and dedication, you can navigate your challenges with wisdom and inner peace.\n"

        return answer


class SelfReflector:
    """
    Step E: Reflects on the generated answer.
    Asks: Is retrieval necessary? Is the answer faithful to the source? Should we refine?
    """

    def __init__(self, grader: VerseGrader):
        self.grader = grader

    def evaluate_answer_quality(
        self, 
        question: str, 
        verses: List[Dict], 
        answer: str
    ) -> Dict:
        """
        Evaluate the generated answer using Self-RAG principles.
        Returns reflection results and refinement needs.
        """
        logger.info("Self-reflection: Evaluating answer quality")

        reflection_results = {
            "retrieval_necessary": True,
            "answer_grounded": False,
            "answer_complete": False,
            "needs_refinement": False,
            "confidence": 0.0
        }

        # Check 1: Is answer grounded in retrieved verses?
        verses_mentioned = 0
        for verse in verses:
            verse_cite = f"{verse['chapter']}.{verse['verse']}"
            if verse_cite in answer:
                verses_mentioned += 1

        grounding_score = verses_mentioned / max(len(verses), 1)
        reflection_results["answer_grounded"] = grounding_score > 0.5
        reflection_results["grounding_score"] = grounding_score

        logger.info(f"  Grounding score: {grounding_score:.2f}")

        # Check 2: Is answer relevant to original question?
        question_words = set(question.lower().split())
        answer_words = set(answer.lower().split())
        relevance = len(question_words & answer_words) / len(question_words)
        reflection_results["answer_complete"] = relevance > 0.3

        logger.info(f"  Relevance score: {relevance:.2f}")

        # Check 3: Calculate overall confidence
        overall_confidence = (grounding_score + relevance) / 2
        reflection_results["confidence"] = overall_confidence

        # Determine if refinement needed
        reflection_results["needs_refinement"] = overall_confidence < REFLECTION_THRESHOLD

        logger.info(f"  Overall confidence: {overall_confidence:.2f}")
        logger.info(f"  Needs refinement: {reflection_results['needs_refinement']}")

        return reflection_results


class MultiStepAgent:
    """
    Main orchestrator combining all steps: Plan -> Retrieve -> Grade -> Generate -> Reflect
    """

    def __init__(self, hybrid_retriever):
        self.planner = QueryPlanner()
        self.retriever = VerseRetriever(hybrid_retriever)
        self.grader = VerseGrader()
        self.generator = AnswerGenerator()
        self.reflector = SelfReflector(self.grader)

    def run(self, question: str, verbose: bool = True) -> Dict:
        """
        Run the complete multi-step agent pipeline.
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"Starting Multi-Step Agent Pipeline")
        logger.info(f"Question: {question}")
        logger.info(f"{'='*60}\n")

        state = AgentState(question=question)

        # Step A: Plan
        logger.info("STEP A: Planning\n")
        state.decomposed_goals = self.planner.decompose(question)
        for goal in state.decomposed_goals:
            logger.info(f"  • {goal}")
        state.reasoning_chain.append(f"Decomposed question into {len(state.decomposed_goals)} goals")

        # Step B: Retrieve
        logger.info("\nSTEP B: Retrieving Verses\n")
        all_retrieved = self.retriever.retrieve_for_goals(state.decomposed_goals, top_k=5)
        state.retrieved_verses = [v for verses in all_retrieved.values() for v in verses]
        # Deduplicate
        seen = set()
        unique_verses = []
        for v in state.retrieved_verses:
            key = (v['chapter'], v['verse'])
            if key not in seen:
                seen.add(key)
                unique_verses.append(v)
        state.retrieved_verses = unique_verses
        state.reasoning_chain.append(f"Retrieved {len(state.retrieved_verses)} total verses")

        # Step C: Grade
        logger.info("\nSTEP C: Grading Verses for Relevance\n")
        state.graded_verses = self.grader.grade_verses(question, state.retrieved_verses)
        state.reasoning_chain.append(f"Graded to {len(state.graded_verses)} relevant verses")

        # Step D: Generate
        logger.info("\nSTEP D: Generating Answer\n")
        state.generated_answer = self.generator.generate(question, state.graded_verses)
        logger.info(f"Answer generated with {len(state.graded_verses)} supporting verses\n")
        state.reasoning_chain.append("Generated answer based on graded verses")

        # Step E: Reflect
        logger.info("STEP E: Self-Reflection\n")
        reflection = self.reflector.evaluate_answer_quality(
            question, 
            state.graded_verses, 
            state.generated_answer
        )
        state.confidence_score = reflection["confidence"]
        state.is_relevant = reflection["answer_grounded"]
        state.needs_refinement = reflection["needs_refinement"]
        state.reasoning_chain.append(f"Self-reflection complete (confidence: {state.confidence_score:.2f})")

        if state.needs_refinement:
            logger.info("\n⚠ Confidence below threshold - marking for refinement\n")
            state.refined_answer = f"[REFINED - LOW CONFIDENCE] {state.generated_answer}\n\nNote: This answer has lower confidence. Consider asking a more specific question."

        logger.info(f"\n{'='*60}")
        logger.info(f"Pipeline Complete")
        logger.info(f"Final Confidence Score: {state.confidence_score:.2f}")
        logger.info(f"Verses Used: {len(state.graded_verses)}")
        logger.info(f"{'='*60}\n")

        return {
            "question": state.question,
            "decomposed_goals": state.decomposed_goals,
            "retrieved_verses_count": len(state.retrieved_verses),
            "graded_verses": state.graded_verses,
            "answer": state.generated_answer,
            "confidence_score": state.confidence_score,
            "needs_refinement": state.needs_refinement,
            "reasoning_chain": state.reasoning_chain,
        }


if __name__ == "__main__":
    # Test would require hybrid_retriever initialized
    print("Multi-Step Agent module loaded")
