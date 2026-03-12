"""
RAGAS Evaluation Framework for the Gita RAG System.
Evaluates: Faithfulness, Answer Relevancy, Context Precision, Context Recall.
"""

import json
from typing import List, Dict, Tuple
import sqlite3
import logging
from datetime import datetime
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer, util

from config.settings import EVALUATION_DIR, SQLITE_DB, EMBEDDING_MODEL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RAGASEvaluator:
    """Implements RAGAS metrics for RAG evaluation."""

    def __init__(self, embedding_model_name: str = EMBEDDING_MODEL):
        self.embedding_model = SentenceTransformer(embedding_model_name)
        self.db_path = SQLITE_DB
        self.eval_dir = EVALUATION_DIR

    def faithfulness(
        self, 
        question: str,
        answer: str, 
        context_verses: List[Dict]
    ) -> float:
        """
        Faithfulness: Does the answer stay faithful to the context?
        Range: 0-1 (higher is better)
        
        Checks if the answer's claims are supported by the retrieved verses.
        """
        if not context_verses:
            return 0.0

        # Combine all context
        context_texts = [v.get("english", "") for v in context_verses]
        full_context = " ".join(context_texts)

        # Encode question, answer, and context
        q_embedding = self.embedding_model.encode(question, convert_to_tensor=True)
        a_embedding = self.embedding_model.encode(answer, convert_to_tensor=True)
        c_embedding = self.embedding_model.encode(full_context, convert_to_tensor=True)

        # Calculate similarity between answer and context
        answer_context_sim = util.pytorch_cos_sim(a_embedding, c_embedding)[0][0].item()

        # Calculate similarity between answer and question (should be high)
        answer_question_sim = util.pytorch_cos_sim(a_embedding, q_embedding)[0][0].item()

        # Faithfulness score combines both
        # Answer should be similar to context (faithful) and to question (relevant)
        faithfulness_score = (answer_context_sim + answer_question_sim) / 2

        return float(max(0.0, min(1.0, faithfulness_score)))

    def answer_relevancy(self, question: str, answer: str) -> float:
        """
        Answer Relevancy: How well does the answer address the question?
        Range: 0-1 (higher is better)
        
        Uses semantic similarity between question and answer.
        """
        q_embedding = self.embedding_model.encode(question, convert_to_tensor=True)
        a_embedding = self.embedding_model.encode(answer, convert_to_tensor=True)

        relevancy = util.pytorch_cos_sim(q_embedding, a_embedding)[0][0].item()
        return float(max(0.0, min(1.0, relevancy)))

    def context_precision(
        self, 
        question: str,
        context_verses: List[Dict]
    ) -> float:
        """
        Context Precision: Is the retrieved context actually relevant?
        Range: 0-1 (higher is better)
        
        Checks what fraction of context is relevant to the question.
        """
        if not context_verses:
            return 0.0

        q_embedding = self.embedding_model.encode(question, convert_to_tensor=True)

        relevance_scores = []
        for verse in context_verses:
            verse_text = verse.get("english", "")
            v_embedding = self.embedding_model.encode(verse_text, convert_to_tensor=True)
            sim = util.pytorch_cos_sim(q_embedding, v_embedding)[0][0].item()
            relevance_scores.append(sim)

        # Context precision = fraction of relevant context (threshold 0.3)
        threshold = 0.3
        relevant_count = sum(1 for s in relevance_scores if s > threshold)
        precision = relevant_count / len(relevance_scores) if relevance_scores else 0.0

        return float(max(0.0, min(1.0, precision)))

    def context_recall(
        self, 
        question: str,
        context_verses: List[Dict],
        oracle_verses: List[Dict] = None
    ) -> float:
        """
        Context Recall: What fraction of relevant verses were retrieved?
        Range: 0-1 (higher is better)
        
        Requires oracle ground truth (ideal retrieved verses).
        """
        if oracle_verses is None:
            # Approximate with semantic relevance
            return self.context_precision(question, context_verses)

        # If we have oracle, calculate recall
        q_embedding = self.embedding_model.encode(question, convert_to_tensor=True)

        # Calculate if each oracle verse was retrieved
        recalled_count = 0
        for oracle_verse in oracle_verses:
            oracle_text = oracle_verse.get("english", "")
            oracle_embedding = self.embedding_model.encode(oracle_text, convert_to_tensor=True)

            # Check if this oracle verse (or similar) is in retrieved
            found = False
            for retrieved_verse in context_verses:
                r_text = retrieved_verse.get("english", "")
                r_embedding = self.embedding_model.encode(r_text, convert_to_tensor=True)

                sim = util.pytorch_cos_sim(oracle_embedding, r_embedding)[0][0].item()
                if sim > 0.8:  # High similarity threshold for "retrieved"
                    found = True
                    break

            if found:
                recalled_count += 1

        recall = recalled_count / len(oracle_verses) if oracle_verses else 0.0
        return float(max(0.0, min(1.0, recall)))

    def evaluate_response(
        self,
        question: str,
        answer: str,
        context_verses: List[Dict],
        oracle_verses: List[Dict] = None
    ) -> Dict[str, float]:
        """
        Compute all RAGAS metrics for a complete RAG response.
        """
        logger.info(f"Evaluating response for question: {question[:50]}...")

        metrics = {
            "faithfulness": self.faithfulness(question, answer, context_verses),
            "answer_relevancy": self.answer_relevancy(question, answer),
            "context_precision": self.context_precision(question, context_verses),
            "context_recall": self.context_recall(question, context_verses, oracle_verses),
        }

        # Calculate overall score (equally weighted)
        metrics["ragas_score"] = np.mean(list(metrics.values()))

        return metrics

    def batch_evaluate(
        self, 
        test_cases: List[Dict],
        oracle_set: Dict = None
    ) -> Dict:
        """
        Evaluate multiple test cases and compute aggregate metrics.

        test_cases format:
        [
            {
                "question": "...",
                "answer": "...",
                "context_verses": [...]
            },
            ...
        ]
        """
        logger.info(f"Batch evaluating {len(test_cases)} test cases...")

        all_results = []
        metric_sums = {
            "faithfulness": 0,
            "answer_relevancy": 0,
            "context_precision": 0,
            "context_recall": 0,
        }

        for i, test_case in enumerate(test_cases):
            oracle = None
            if oracle_set and test_case["question"] in oracle_set:
                oracle = oracle_set[test_case["question"]]

            metrics = self.evaluate_response(
                test_case["question"],
                test_case["answer"],
                test_case["context_verses"],
                oracle
            )

            all_results.append(
                {
                    "question": test_case["question"],
                    "metrics": metrics
                }
            )

            # Accumulate sums
            for key in metric_sums:
                metric_sums[key] += metrics[key]

            if (i + 1) % 5 == 0:
                logger.info(f"  Evaluated {i + 1}/{len(test_cases)} cases...")

        # Calculate aggregate scores
        n = len(test_cases)
        aggregate_metrics = {
            f"avg_{key}": metric_sums[key] / n
            for key in metric_sums
        }
        aggregate_metrics["avg_ragas_score"] = np.mean(list(aggregate_metrics.values()))

        return {
            "individual_results": all_results,
            "aggregate_metrics": aggregate_metrics,
            "test_cases_evaluated": n,
        }

    def save_evaluation_to_db(self, query: str, context_verses: List[Dict], answer: str, metrics: Dict):
        """Save evaluation results to SQLite database."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        retrieved_verses_str = json.dumps([
            {"chapter": v["chapter"], "verse": v["verse"]}
            for v in context_verses
        ])

        cursor.execute(
            """
            INSERT INTO evaluation_results
            (query_text, retrieved_verses, generated_answer, faithfulness_score, 
             answer_relevancy, context_precision, context_recall)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                query,
                retrieved_verses_str,
                answer,
                metrics.get("faithfulness", 0),
                metrics.get("answer_relevancy", 0),
                metrics.get("context_precision", 0),
                metrics.get("context_recall", 0),
            ),
        )

        conn.commit()
        conn.close()

    def generate_evaluation_report(self, evaluation_result: Dict) -> str:
        """Generate a human-readable evaluation report."""
        report = "=" * 60 + "\n"
        report += "RAGAS Evaluation Report\n"
        report += "=" * 60 + "\n\n"

        agg_metrics = evaluation_result["aggregate_metrics"]

        report += "Aggregate Metrics:\n"
        report += "-" * 40 + "\n"
        for key, value in agg_metrics.items():
            if key != "avg_ragas_score":
                report += f"{key.replace('avg_', '').replace('_', ' ').title():.<30} {value:.4f}\n"

        report += "\n" + "=" * 40 + "\n"
        report += f"Overall RAGAS Score: {agg_metrics['avg_ragas_score']:.4f}\n"
        report += "=" * 40 + "\n"

        report += "\nInterpretation:\n"
        report += "-" * 40 + "\n"

        score = agg_metrics["avg_ragas_score"]
        if score > 0.85:
            report += "✓ Excellent: RAG system performs very well\n"
        elif score > 0.70:
            report += "✓ Good: RAG system performs adequately\n"
        elif score > 0.50:
            report += "⚠ Fair: RAG system has room for improvement\n"
        else:
            report += "✗ Poor: RAG system needs significant improvement\n"

        report += "\nTest Cases Evaluated: " + str(evaluation_result["test_cases_evaluated"]) + "\n"

        return report

    def save_report(self, evaluation_result: Dict, filename: str = None) -> str:
        """Save evaluation report to file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ragas_report_{timestamp}.txt"

        report = self.generate_evaluation_report(evaluation_result)
        filepath = self.eval_dir / filename

        with open(filepath, "w") as f:
            f.write(report)

        logger.info(f"Report saved to {filepath}")
        return str(filepath)


class EvaluationDatasetBuilder:
    """
    Builds evaluation datasets with oracle annotations.
    Used to create ground truth for RAGAS evaluation.
    """

    def __init__(self, db_path: str = str(SQLITE_DB)):
        self.db_path = db_path

    def create_test_queries(self) -> List[Dict]:
        """Create a set of test queries covering different topics from the Gita."""
        test_queries = [
            {
                "query": "How should I approach my work and career?",
                "topics": ["karma", "duty", "action"],
            },
            {
                "query": "How can I find peace in difficult times?",
                "topics": ["detachment", "equanimity", "peace"],
            },
            {
                "query": "What is the path to spiritual awakening?",
                "topics": ["meditation", "knowledge", "liberation"],
            },
            {
                "query": "How do I handle attachment and loss?",
                "topics": ["attachment", "detachment", "dharma"],
            },
            {
                "query": "What is my duty and dharma?",
                "topics": ["dharma", "duty", "righteous"],
            },
            {
                "query": "How can I develop faith and devotion?",
                "topics": ["bhakti", "devotion", "faith"],
            },
            {
                "query": "What teaches about the nature of the soul?",
                "topics": ["soul", "eternal", "consciousness"],
            },
            {
                "query": "How do I overcome fear and doubt?",
                "topics": ["courage", "faith", "strength"],
            },
        ]

        return test_queries

    def annotate_oracle_verses(self, query: str) -> List[Dict]:
        """
        For a given query, return oracle (manually verified) relevant verses.
        This would be done by domain experts in production.
        """
        oracle_mapping = {
            "How should I approach my work and career?": [
                {"chapter": 2, "verse": 47},  # Karma Yoga
                {"chapter": 3, "verse": 27},  # Gunas perform actions
                {"chapter": 6, "verse": 16},  # Moderation in all
            ],
            "How can I find peace in difficult times?": [
                {"chapter": 2, "verse": 47},  # Equanimity
                {"chapter": 5, "verse": 24},  # Equality in all
                {"chapter": 6, "verse": 5},   # Mind is friend/enemy
            ],
            "What is the path to spiritual awakening?": [
                {"chapter": 4, "verse": 37},  # Knowledge burns karma
                {"chapter": 6, "verse": 5},   # Meditation
                {"chapter": 15, "verse": 15}, # Krishna in hearts
            ],
        }

        return oracle_mapping.get(query, [])


if __name__ == "__main__":
    evaluator = RAGASEvaluator()
    builder = EvaluationDatasetBuilder()

    test_queries = builder.create_test_queries()
    print(f"Created {len(test_queries)} test queries for evaluation")

    # Example: evaluate a single response
    # results = evaluator.evaluate_response(
    #     question="How should I work?",
    #     answer="Krishna teaches karma yoga...",
    #     context_verses=[...]
    # )
