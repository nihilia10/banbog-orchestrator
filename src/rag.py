"""
llm.py — RAG Agent using GPT-4.1-nano + FAISS vector store.

Flow:
  1. Load the local FAISS index.
  2. Retrieve top-k relevant chunks based on user query and source filters.
  3. Formulate a prompt with retrieved context and user query.
  4. Generate a grounded answer using GPT-4.1-nano.
"""

import os
from typing import Optional, List, Tuple

from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_community.callbacks import get_openai_callback


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

FAISS_INDEX_PATH     = "faiss_index"
if not os.path.exists(FAISS_INDEX_PATH) and os.path.exists(os.path.join("..", FAISS_INDEX_PATH)):
    FAISS_INDEX_PATH = os.path.join("..", FAISS_INDEX_PATH)
EMBEDDING_MODEL      = "text-embedding-3-small"
LLM_MODEL            = "gpt-4.1-nano"
DEFAULT_K            = 5
SIMILARITY_THRESHOLD = 0.40  # 80% similarity threshold (1 / (1 + L2_score))


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """Eres un asistente bancario experto con acceso a documentos internos del banco.
Responde la pregunta del usuario de forma precisa y concisa utilizando ÚNICAMENTE el contexto proporcionado.
Si el contexto no contiene suficiente información para responder, dilo claramente.
No inventes información. Responde en el mismo idioma de la pregunta del usuario."""

RAG_PROMPT_TEMPLATE = """
Contexto (recuperado de documentos internos):
{context}

---
Pregunta del usuario: {question}

Respuesta:"""


# ---------------------------------------------------------------------------
# RAGAgent Class
# ---------------------------------------------------------------------------

class RAGAgent:
    def __init__(
        self,
        index_path: str = FAISS_INDEX_PATH,
        embedding_model: str = EMBEDDING_MODEL,
        llm_model: str = LLM_MODEL,
        threshold: float = SIMILARITY_THRESHOLD
    ):
        """
        Initializes the RAG Agent loader and models.
        """
        if not os.environ.get("OPENAI_API_KEY"):
            raise EnvironmentError("OPENAI_API_KEY not found in environment variables.")

        self.index_path = index_path
        self.threshold = threshold
        
        # Initialize Embeddings and LLM
        self.embeddings = OpenAIEmbeddings(model=embedding_model)
        self.llm = ChatOpenAI(model=llm_model, temperature=0)
        
        # Load Vector Store
        self._vectorstore = self._load_vectorstore()

    def _load_vectorstore(self) -> FAISS:
        """Loads FAISS from local disk."""
        if not os.path.exists(self.index_path):
            raise FileNotFoundError(f"FAISS index not found at '{self.index_path}'.")
        
        return FAISS.load_local(
            folder_path=self.index_path,
            embeddings=self.embeddings,
            allow_dangerous_deserialization=True
        )

    def _retrieve(
        self,
        query: str,
        k: int = DEFAULT_K,
        source_tag: Optional[str] = None
    ) -> str:
        """
        Retrieves top-k candidates, filters by threshold, and returns formatted context.
        """
        search_kwargs: dict = {"k": k}
        if source_tag:
            search_kwargs["filter"] = {"source_tag": source_tag}

        # FAISS returns L2 distance
        raw_results = self._vectorstore.similarity_search_with_score(query, **search_kwargs)

        results = []
        for doc, l2_score in raw_results:
            similarity = 1.0 / (1.0 + l2_score)
            if similarity >= self.threshold:
                results.append((doc, similarity))
        
        if not results:
            return "No se encontró información relevante en los documentos internos."

        return self._format_context(results)

    def _format_context(self, results: List[Tuple[Document, float]]) -> str:
        """Formats retrieved documents into a context block."""
        parts = []
        for i, (doc, sim) in enumerate(results, start=1):
            tag = doc.metadata.get("source_tag", "unknown")
            content = doc.page_content.strip().replace("\n", " ")
            parts.append(f"[{i}] (fuente: {tag} | similitud: {sim:.1%})\n{content}")
        return "\n\n".join(parts)

    def query(self, config: dict) -> str:
        """
        Runs the full RAG pipeline using a config dictionary.
        This signature is compatible with LCEL's dictated output from a previous step.
        """
        question = config.get("question", "")
        source_tag = config.get("source_tag")
        k = config.get("k", DEFAULT_K)
        
        # 1. Retrieve & Augment
        context = self._retrieve(question, k=k, source_tag=source_tag)

        # 2. Generate
        prompt = RAG_PROMPT_TEMPLATE.format(context=context, question=question)
        with get_openai_callback() as cb:
            response = self.llm.invoke([
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ])

            # Log tokens to file
            with open("token_usage.txt", "a") as f:
                f.write(f"--- RAG AGENT ({source_tag}) ---\n")
                f.write(f"Question: {question[:50]}...\n")
                f.write(f"Total Tokens: {cb.total_tokens}\n")
                f.write(f"Prompt Tokens: {cb.prompt_tokens}\n")
                f.write(f"Completion Tokens: {cb.completion_tokens}\n")
                f.write(f"Total Cost (USD): ${cb.total_cost:.6f}\n\n")

        return response.content


# ---------------------------------------------------------------------------
# CLI Usage Demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    agent = RAGAgent()
    
    test_config = {
        "question": "¿Qué beneficios tiene la tarjeta de crédito?",
        "source_tag": "products"
    }
    print(f"Pregunta: {test_config['question']}")
    answer = agent.query(test_config)
    print(f"Respuesta:\n{answer}")
