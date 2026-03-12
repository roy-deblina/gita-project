import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CHROMA_DIR = DATA_DIR / "chroma_db"
SQLITE_DB = DATA_DIR / "gita.db"
LOGS_DIR = PROJECT_ROOT / "logs"
EVALUATION_DIR = PROJECT_ROOT / "evaluation"

# Create directories if they don't exist
for dir_path in [DATA_DIR, CHROMA_DIR, LOGS_DIR, EVALUATION_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# Embedding settings
EMBEDDING_MODEL = "BAAI/bge-base-en-v1.5"
CHUNK_SIZE = 512
CHUNK_OVERLAP = 100

# Retrieval settings
USE_BM25 = True
USE_SEMANTIC = True
HYBRID_WEIGHT = 0.5  # Weight for combining BM25 and semantic search
TOP_K_RETRIEVAL = 5

# LLM settings
LOCAL_LLM_MODEL = "llama2:7b"  # Ollama model
LLM_TEMPERATURE = 0.3
MAX_TOKENS = 1024

# RAG settings
USE_SELF_RAG = True
REFLECTION_THRESHOLD = 0.7

# Database settings
DB_BATCH_SIZE = 100

# API settings
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY", "")

# Evaluation settings
RAGAS_EVAL_BATCH_SIZE = 10
RAGAS_EVALUATION_METRICS = [
    "faithfulness",
    "answer_relevancy",
    "context_precision",
    "context_recall",
    "answer_similarity",
]

# Logging settings
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
