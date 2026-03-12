"""
Hybrid Retrieval Engine combining BM25 (keyword) and Vector (semantic) search.
Uses Reciprocal Rank Fusion (RRF) for optimal result combination.
"""

import sqlite3
from typing import List, Dict, Tuple
from pathlib import Path
import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer
import chromadb
from config.settings import SQLITE_DB, CHROMA_DIR, EMBEDDING_MODEL, TOP_K_RETRIEVAL


class HybridRetriever:
    """Combines BM25 and semantic search using RRF."""

    def __init__(self, use_bm25: bool = True, use_semantic: bool = True):
        self.db_path = SQLITE_DB
        self.chroma_dir = CHROMA_DIR
        self.use_bm25 = use_bm25
        self.use_semantic = use_semantic
        self.top_k = TOP_K_RETRIEVAL

        # Initialize BM25
        self.bm25_corpus = []
        self.bm25_index = None

        # Initialize embedding model
        self.embedding_model = SentenceTransformer(EMBEDDING_MODEL)

        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(path=str(self.chroma_dir))
        self.collection = None

        # Load data
        self._load_corpus()
        self._initialize_bm25()
        self._initialize_chromadb()

    def _load_corpus(self):
        """Load all verses from SQLite."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, chapter_number, verse_number, english, combined_text, sanskrit
            FROM verses ORDER BY chapter_number, verse_number
        """
        )

        self.corpus = [dict(row) for row in cursor.fetchall()]
        conn.close()

    def _initialize_bm25(self):
        """Initialize BM25 index for keyword search."""
        if not self.use_bm25:
            return

        # Tokenize texts for BM25
        corpus_texts = [verse["combined_text"] for verse in self.corpus]
        tokenized_corpus = [text.lower().split() for text in corpus_texts]

        self.bm25_index = BM25Okapi(tokenized_corpus)
        print(f"✓ BM25 index created with {len(self.corpus)} documents")

    def _initialize_chromadb(self):
        """Initialize ChromaDB for semantic search."""
        if not self.use_semantic:
            return

        # Check if collection exists
        try:
            self.collection = self.client.get_collection(
                name="gita_verses",
                embedding_function=chromadb.utils.embedding_functions.SentenceTransformerEmbeddingFunction(
                    model_name=EMBEDDING_MODEL
                ),
            )
            print(f"✓ ChromaDB collection loaded: {self.collection.count()} verses")
            return
        except:
            pass

        # Create if doesn't exist
        self.collection = self.client.create_collection(
            name="gita_verses",
            embedding_function=chromadb.utils.embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=EMBEDDING_MODEL
            ),
            metadata={"hnsw:space": "cosine"},
        )

        # Add verses to collection
        ids = []
        documents = []
        metadatas = []

        for verse in self.corpus:
            verse_id = f"ch{verse['chapter_number']}_v{verse['verse_number']}"
            ids.append(verse_id)
            documents.append(verse["combined_text"])
            metadatas.append(
                {
                    "chapter": str(verse["chapter_number"]),
                    "verse": str(verse["verse_number"]),
                    "english": verse["english"][:500],  # Truncate for metadata
                }
            )

        # Batch add to avoid memory issues
        batch_size = 100
        for i in range(0, len(ids), batch_size):
            batch_ids = ids[i : i + batch_size]
            batch_docs = documents[i : i + batch_size]
            batch_meta = metadatas[i : i + batch_size]

            self.collection.add(ids=batch_ids, documents=batch_docs, metadatas=batch_meta)

        print(f"✓ ChromaDB indexed {len(ids)} verses")

    def _bm25_search(self, query: str, top_k: int = None) -> List[Tuple[int, float]]:
        """BM25 keyword search. Returns (verse_idx, score) tuples."""
        if not self.use_bm25 or self.bm25_index is None:
            return []

        top_k = top_k or self.top_k
        query_tokens = query.lower().split()
        scores = self.bm25_index.get_scores(query_tokens)

        # Get top-k indices
        top_indices = np.argsort(scores)[-top_k:][::-1]
        results = [(int(idx), float(scores[idx])) for idx in top_indices]

        return results

    def _semantic_search(
        self, query: str, top_k: int = None
    ) -> List[Tuple[int, float]]:
        """Vector semantic search. Returns (verse_idx, score) tuples."""
        if not self.use_semantic or self.collection is None:
            return []

        top_k = top_k or self.top_k

        results = self.collection.query(
            query_texts=[query], n_results=top_k, include=["distances", "metadatas"]
        )

        # Convert ChromaDB results to our format
        # ChromaDB returns distances, we convert to similarities (1 - distance for cosine)
        verse_results = []
        if results["ids"] and len(results["ids"]) > 0:
            for verse_id, distance in zip(results["ids"][0], results["distances"][0]):
                # Parse verse_id to get corpus index
                parts = verse_id.split("_")
                chapter = int(parts[0][2:])
                verse = int(parts[1][1:])

                # Find corpus index
                corpus_idx = next(
                    (
                        i
                        for i, v in enumerate(self.corpus)
                        if v["chapter_number"] == chapter and v["verse_number"] == verse
                    ),
                    -1,
                )

                if corpus_idx >= 0:
                    similarity = 1 - distance  # Convert distance to similarity
                    verse_results.append((corpus_idx, similarity))

        return verse_results

    def _reciprocal_rank_fusion(
        self, bm25_results: List[Tuple[int, float]], semantic_results: List[Tuple[int, float]], top_k: int = None
    ) -> List[Dict]:
        """
        Combines BM25 and semantic results using Reciprocal Rank Fusion.
        Higher RRF score = better result.
        """
        top_k = top_k or self.top_k

        # Build RRF scores
        rrf_scores = {}
        k = 60  # RRF parameter (typically 60)

        # Score from BM25 (rank + 1 based)
        for rank, (verse_idx, score) in enumerate(bm25_results):
            rrf_scores[verse_idx] = rrf_scores.get(verse_idx, 0) + 1 / (k + rank + 1)

        # Score from semantic search
        for rank, (verse_idx, score) in enumerate(semantic_results):
            rrf_scores[verse_idx] = rrf_scores.get(verse_idx, 0) + 1 / (k + rank + 1)

        # Sort by RRF score
        sorted_verses = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[
            :top_k
        ]

        # Build results with metadata
        results = []
        for verse_idx, rrf_score in sorted_verses:
            verse = self.corpus[verse_idx]
            results.append(
                {
                    "chapter": verse["chapter_number"],
                    "verse": verse["verse_number"],
                    "english": verse["english"],
                    "sanskrit": verse["sanskrit"],
                    "combined_text": verse["combined_text"],
                    "rrf_score": float(rrf_score),
                    "corpus_idx": verse_idx,
                }
            )

        return results

    def retrieve(self, query: str, top_k: int = None) -> List[Dict]:
        """
        Main retrieval method. Runs both BM25 and semantic search, combines with RRF.
        """
        top_k = top_k or self.top_k

        # Run both searches
        bm25_results = self._bm25_search(query, top_k=top_k * 2)
        semantic_results = self._semantic_search(query, top_k=top_k * 2)

        # Combine with RRF
        final_results = self._reciprocal_rank_fusion(
            bm25_results, semantic_results, top_k=top_k
        )

        return final_results

    def retrieve_with_scores(self, query: str, top_k: int = None) -> Tuple[List[Dict], Dict]:
        """Retrieve with detailed scoring information for analysis."""
        top_k = top_k or self.top_k

        bm25_results = self._bm25_search(query, top_k=top_k * 2)
        semantic_results = self._semantic_search(query, top_k=top_k * 2)

        final_results = self._reciprocal_rank_fusion(
            bm25_results, semantic_results, top_k=top_k
        )

        scoring_info = {
            "bm25_count": len(bm25_results),
            "semantic_count": len(semantic_results),
            "top_rrf_score": final_results[0]["rrf_score"] if final_results else 0,
        }

        return final_results, scoring_info


class SupplementaryRetriever:
    """
    Retrieves supplementary verses based on semantic relationships.
    Useful for cross-tradition analysis.
    """

    def __init__(self, retriever: HybridRetriever):
        self.retriever = retriever
        self.embedding_model = retriever.embedding_model

    def get_commentaries(self, verse_id: Tuple[int, int]) -> Dict:
        """Get both Shankaracharya and Prabhupada commentaries for a verse."""
        chapter, verse_num = verse_id

        conn = sqlite3.connect(str(self.retriever.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT v.id, v.english, v.sanskrit, c.tradition, c.commentary_text, c.author
            FROM verses v
            LEFT JOIN commentaries c ON v.id = c.verse_id
            WHERE v.chapter_number = ? AND v.verse_number = ?
        """,
            (chapter, verse_num),
        )

        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return None

        verse_data = {
            "chapter": chapter,
            "verse": verse_num,
            "english": rows[0]["english"],
            "sanskrit": rows[0]["sanskrit"],
            "commentaries": {},
        }

        for row in rows:
            if row["tradition"]:
                verse_data["commentaries"][row["tradition"]] = {
                    "text": row["commentary_text"],
                    "author": row["author"],
                }

        return verse_data

    def get_related_verses(
        self, query: str, topic: str = None, top_k: int = 3
    ) -> List[Dict]:
        """Get semantically related verses, optionally filtered by topic."""
        main_results = self.retriever.retrieve(query, top_k=1)

        if not main_results:
            return []

        main_verse = main_results[0]

        # Find related verses by embedding similarity to main result
        main_text = main_verse["combined_text"]
        main_embedding = self.embedding_model.encode(main_text)

        similarities = []
        for i, verse in enumerate(self.retriever.corpus):
            verse_embedding = self.embedding_model.encode(verse["combined_text"])
            similarity = np.dot(main_embedding, verse_embedding) / (
                np.linalg.norm(main_embedding) * np.linalg.norm(verse_embedding) + 1e-10
            )
            similarities.append((i, similarity))

        # Sort and get top similar (exclude the main verse itself)
        similarities = sorted(similarities, key=lambda x: x[1], reverse=True)

        related = []
        for idx, similarity in similarities[1 : top_k + 1]:
            verse = self.retriever.corpus[idx]
            related.append(
                {
                    "chapter": verse["chapter_number"],
                    "verse": verse["verse_number"],
                    "english": verse["english"],
                    "similarity_to_main": float(similarity),
                }
            )

        return related


if __name__ == "__main__":
    # Test the retriever
    retriever = HybridRetriever()

    test_queries = [
        "How should I handle stress and anxiety?",
        "What is the path to liberation?",
        "How do I perform my duties?",
    ]

    for query in test_queries:
        print(f"\nQuery: {query}")
        results = retriever.retrieve(query, top_k=3)
        for i, result in enumerate(results, 1):
            print(
                f"  {i}. Ch{result['chapter']}.{result['verse']} (Score: {result['rrf_score']:.3f})"
            )
            print(f"     {result['english'][:100]}...")
