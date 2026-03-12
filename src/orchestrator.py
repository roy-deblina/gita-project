"""
Main Orchestrator: Brings together all components of the Gita RAG system.
Coordinates: Retrieval -> Agentic Processing -> Evaluation -> Explainability
"""

import logging
import json
from typing import Dict, Optional
from pathlib import Path

from config.settings import LOGS_DIR
from src.data_loader import GitaDatasetLoader
from src.retriever import HybridRetriever, SupplementaryRetriever
from src.agent import MultiStepAgent
from src.evaluator import RAGASEvaluator
from src.explainability import ExplainabilityEngine, TransparencyReportGenerator
from src.traditions import TraditionAnalyzer, TraditionIntegrator

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / "gita_rag.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class GitaRAGSystem:
    """Main RAG system orchestrator."""

    def __init__(self, initialize_data: bool = True):
        """Initialize all components of the Gita RAG system."""
        logger.info("Initializing Gita RAG System...")

        # Load/create dataset
        if initialize_data:
            logger.info("Loading dataset...")
            data_loader = GitaDatasetLoader()
            self.verses = data_loader.initialize()
        else:
            logger.info("Skipping data initialization")
            self.verses = []

        # Initialize main components
        logger.info("Initializing retriever...")
        self.retriever = HybridRetriever(use_bm25=True, use_semantic=True)

        logger.info("Initializing supplementary tools...")
        self.supplementary = SupplementaryRetriever(self.retriever)

        logger.info("Initializing agent...")
        self.agent = MultiStepAgent(self.retriever)

        logger.info("Initializing evaluator...")
        self.evaluator = RAGASEvaluator()

        logger.info("Initializing explainability engine...")
        self.explainability = ExplainabilityEngine()

        logger.info("Initializing tradition analyzer...")
        self.tradition_analyzer = TraditionAnalyzer(str(self.retriever.db_path))
        self.tradition_integrator = TraditionIntegrator(self.tradition_analyzer)

        logger.info("✓ System initialization complete!")

    def process_query(
        self,
        question: str,
        include_evaluation: bool = True,
        include_traditions: bool = True,
        verbose: bool = True,
    ) -> Dict:
        """
        Process a query through the complete pipeline.

        Returns comprehensive response with answer, reasoning, evaluation, and explainability.
        """
        logger.info(f"\n{'='*70}")
        logger.info(f"Processing Query: {question}")
        logger.info(f"{'='*70}\n")

        result = {
            "question": question,
            "timestamp": None,
            "pipeline_stages": {},
        }

        # Stage 1: Agentic Processing
        logger.info("Stage 1: Multi-Step Agentic Processing")
        logger.info("-" * 70)
        agent_result = self.agent.run(question, verbose=verbose)
        result["pipeline_stages"]["agent"] = agent_result
        result["final_answer"] = agent_result["answer"]
        result["confidence_score"] = agent_result["confidence_score"]

        # Stage 2: Evaluation (Optional)
        if include_evaluation:
            logger.info("\nStage 2: RAGAS Evaluation")
            logger.info("-" * 70)
            eval_metrics = self.evaluator.evaluate_response(
                question,
                agent_result["answer"],
                agent_result["graded_verses"],
            )
            result["pipeline_stages"]["evaluation"] = eval_metrics
            logger.info("Evaluation metrics:")
            for metric, score in eval_metrics.items():
                if metric != "ragas_score":
                    logger.info(f"  {metric}: {score:.4f}")

        # Stage 3: Explainability
        logger.info("\nStage 3: Generating Explainability Report")
        logger.info("-" * 70)
        explainable_response = self.explainability.create_explainable_response(
            question=question,
            answer=agent_result["answer"],
            confidence_score=agent_result["confidence_score"],
            primary_verses=agent_result["graded_verses"][:3],
            supporting_verses=agent_result["graded_verses"][3:],
            reasoning_steps=agent_result["reasoning_chain"],
            agent_output=agent_result,
        )
        result["pipeline_stages"]["explainability"] = explainable_response

        # Stage 4: Cross-Tradition Analysis (Optional)
        if include_traditions:
            logger.info("\nStage 4: Cross-Tradition Analysis")
            logger.info("-" * 70)
            tradition_comparison = self._analyze_traditions(
                question, agent_result["graded_verses"]
            )
            result["pipeline_stages"]["traditions"] = tradition_comparison

            # Enhance answer with tradition insights
            balanced_answer = self.tradition_integrator.create_balanced_response(
                question,
                agent_result["answer"],
                agent_result["graded_verses"],
            )
            result["final_answer_with_traditions"] = balanced_answer

        logger.info(f"\n{'='*70}")
        logger.info("Query Processing Complete")
        logger.info(f"{'='*70}\n")

        return result

    def _analyze_traditions(
        self, question: str, verses: list
    ) -> Dict:
        """Analyze how different traditions interpret the answer."""
        analysis = {
            "question": question,
            "tradition_profiles": self.tradition_analyzer.TRADITION_PROFILES,
            "verse_analyses": [],
        }

        # Analyze top 2 verses
        for verse in verses[:2]:
            verse_analysis = self.tradition_analyzer.analyze_verse_traditions(
                verse["chapter"], verse["verse"]
            )
            if verse_analysis:
                analysis["verse_analyses"].append(verse_analysis)

        # Add philosophical comparison
        analysis["philosophical_comparison"] = (
            self.tradition_analyzer.compare_philosophical_approaches()
        )

        return analysis

    def generate_reports(self, result: Dict, output_dir: Optional[Path] = None) -> Dict:
        """Generate all reports from a processed query."""
        if output_dir is None:
            output_dir = LOGS_DIR / "reports"
        output_dir.mkdir(parents=True, exist_ok=True)

        reports = {}

        # Markdown report
        explainable = result["pipeline_stages"]["explainability"]
        markdown_report = TransparencyReportGenerator.generate_markdown_report(
            explainable
        )
        markdown_path = output_dir / f"report_{int(hash(result['question']))}.md"
        with open(markdown_path, "w") as f:
            f.write(markdown_report)
        reports["markdown"] = str(markdown_path)

        # JSON report (for programmatic use)
        json_report = TransparencyReportGenerator.generate_json_report(explainable)
        json_path = output_dir / f"report_{int(hash(result['question']))}.json"
        with open(json_path, "w") as f:
            f.write(json_report)
        reports["json"] = str(json_path)

        logger.info(f"Reports saved to {output_dir}")
        return reports

    def batch_process(self, questions: list) -> Dict:
        """Process multiple queries and return batch results."""
        logger.info(f"\nBatch Processing {len(questions)} queries\n")

        batch_results = {
            "total_queries": len(questions),
            "results": [],
            "aggregate_metrics": {},
        }

        for i, question in enumerate(questions, 1):
            logger.info(f"\nQuery {i}/{len(questions)}")
            try:
                result = self.process_query(
                    question, include_evaluation=True, include_traditions=True
                )
                batch_results["results"].append(result)
            except Exception as e:
                logger.error(f"Error processing query {i}: {e}")
                batch_results["results"].append(
                    {"question": question, "error": str(e)}
                )

        # Calculate aggregate metrics
        eval_results = [
            r.get("pipeline_stages", {}).get("evaluation", {})
            for r in batch_results["results"]
        ]
        if eval_results:
            metrics = {}
            for key in ["faithfulness", "answer_relevancy", "context_precision", "context_recall", "ragas_score"]:
                scores = [e.get(key, 0) for e in eval_results if e.get(key)]
                if scores:
                    metrics[f"avg_{key}"] = sum(scores) / len(scores)

            batch_results["aggregate_metrics"] = metrics

            logger.info("\nBatch Evaluation Summary:")
            for metric, value in metrics.items():
                logger.info(f"  {metric}: {value:.4f}")

        return batch_results

    def create_evaluation_dataset(self) -> Dict:
        """Create a standard evaluation dataset."""
        from src.evaluator import EvaluationDatasetBuilder

        builder = EvaluationDatasetBuilder()
        test_queries = builder.create_test_queries()

        dataset = {
            "test_queries": test_queries,
            "oracle_annotations": {},
        }

        for query_dict in test_queries:
            query = query_dict["query"]
            oracle = builder.annotate_oracle_verses(query)
            dataset["oracle_annotations"][query] = oracle

        logger.info(
            f"Created evaluation dataset with {len(test_queries)} test queries"
        )
        return dataset


def main():
    """Demo execution of the complete system."""
    # Initialize system
    system = GitaRAGSystem(initialize_data=True)

    # Test queries
    test_queries = [
        "How should I approach my work and career challenges?",
        "How can I find inner peace during difficult times?",
        "What does the Gita teach about the nature of the self?",
    ]

    # Process single query with full pipeline
    print("\n" + "=" * 80)
    print("SINGLE QUERY PROCESSING WITH FULL PIPELINE")
    print("=" * 80)

    result = system.process_query(
        test_queries[0],
        include_evaluation=True,
        include_traditions=True,
        verbose=True,
    )

    # Generate reports
    print("\nGenerating reports...")
    reports = system.generate_reports(result)
    print(f"Reports generated: {reports}")

    # Batch processing
    print("\n" + "=" * 80)
    print("BATCH PROCESSING")
    print("=" * 80)

    batch_result = system.batch_process(test_queries)
    print(f"\nBatch processing complete: {batch_result['total_queries']} queries processed")


if __name__ == "__main__":
    main()
