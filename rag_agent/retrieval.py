
from pathlib import Path
import hashlib
import time

import chromadb
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import MarkdownHeaderTextSplitter


BASE_DIR = Path(__file__).resolve().parent
DOCS_DIR = BASE_DIR / "docs"
DB_DIR = BASE_DIR / "chroma_db"

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
COLLECTION_NAME = "cloud_documentation"

HEADERS = [
    ("#", "h1"),
    ("##", "h2"),
    ("###", "h3"),
]

CHUNK_SIZE = 1200
OVERLAP = 150


class CloudRetriever:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=str(DB_DIR))
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

        self.embedder = SentenceTransformer(EMBEDDING_MODEL)
        self.splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=HEADERS,
            strip_headers=False,
        )

        self.documents = []
        self.bm25 = None
        self.index_signature = None

        self._build_index()
        self._load_bm25()

    def _read_chunks(self):
        chunks = []

        for path in sorted(DOCS_DIR.rglob("*.md")):
            text = path.read_text(encoding="utf-8")
            if not text.strip():
                continue

            sections = self.splitter.split_text(text)

            for section_number, section in enumerate(sections):
                content = section.page_content.strip()
                if not content:
                    continue

                # Keep chunks bounded without adding another dependency.
                for start in range(0, len(content), CHUNK_SIZE - OVERLAP):
                    chunk = content[start:start + CHUNK_SIZE].strip()
                    if not chunk:
                        continue

                    metadata = {
                        "source": str(path.relative_to(DOCS_DIR)),
                        "section": " > ".join(
                            str(v) for v in section.metadata.values()
                        ) or path.stem,
                        "chunk_id": f"{path.stem}-{section_number}-{start}",
                    }

                    chunks.append((chunk, metadata))

        return chunks

    def _signature(self):
        digest = hashlib.sha256()

        for path in sorted(DOCS_DIR.rglob("*.md")):
            digest.update(str(path.relative_to(DOCS_DIR)).encode())
            digest.update(path.read_bytes())

        return digest.hexdigest()

    def _build_index(self):
        signature = self._signature()
        stored = self.collection.get(
            limit=1,
            include=["metadatas"],
        )

        # Reuse the index if the documentation has not changed.
        if stored["ids"] and stored["metadatas"]:
            old_signature = stored["metadatas"][0].get("signature")
            if old_signature == signature:
                return

        chunks = self._read_chunks()

        self.collection.delete(
            ids=self.collection.get()["ids"]
        ) if self.collection.count() else None

        if not chunks:
            print(f"No Markdown documents found in {DOCS_DIR}")
            return

        texts = [text for text, _ in chunks]
        ids = []
        metadatas = []

        for i, (text, metadata) in enumerate(chunks):
            ids.append(hashlib.sha256(
                f"{metadata['chunk_id']}:{text}".encode()
            ).hexdigest())
            metadatas.append({
                **metadata,
                "signature": signature,
            })

        # Embed in batches to reduce overhead.
        embeddings = self.embedder.encode(
            texts,
            batch_size=32,
            normalize_embeddings=True,
            show_progress_bar=False,
        ).tolist()

        self.collection.upsert(
            ids=ids,
            documents=texts,
            metadatas=metadatas,
            embeddings=embeddings,
        )

        print(f"Indexed {len(texts)} chunks from {DOCS_DIR}")

    def _load_bm25(self):
        result = self.collection.get(
            include=["documents", "metadatas"]
        )

        self.documents = [
            {
                "text": text,
                "metadata": metadata,
                "id": doc_id,
            }
            for doc_id, text, metadata in zip(
                result["ids"],
                result["documents"],
                result["metadatas"],
            )
        ]

        if self.documents:
            tokenized = [
                item["text"].lower().split()
                for item in self.documents
            ]
            self.bm25 = BM25Okapi(tokenized)

    def search(self, query: str, top_k: int = 3) -> list[dict]:
        started = time.perf_counter()

        if not self.documents or self.bm25 is None:
            return []

        # Dense retrieval.
        query_embedding = self.embedder.encode(
            query,
            normalize_embeddings=True,
        ).tolist()

        dense = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(5, len(self.documents)),
            include=["documents", "metadatas", "distances"],
        )

        dense_ids = dense["ids"][0]

        # Keyword retrieval.
        scores = self.bm25.get_scores(query.lower().split())
        keyword_indices = sorted(
            range(len(scores)),
            key=lambda i: scores[i],
            reverse=True,
        )[:5]

        keyword_ids = [
            self.documents[i]["id"]
            for i in keyword_indices
            if scores[i] > 0
        ]

        # Reciprocal Rank Fusion.
        rrf_scores = {}
        for ranked_ids in (dense_ids, keyword_ids):
            for rank, doc_id in enumerate(ranked_ids, start=1):
                rrf_scores[doc_id] = (
                    rrf_scores.get(doc_id, 0.0)
                    + 1.0 / (60 + rank)
                )

        by_id = {item["id"]: item for item in self.documents}
        ranked = sorted(
            rrf_scores,
            key=rrf_scores.get,
            reverse=True,
        )[:top_k]

        results = [
            {
                "text": by_id[doc_id]["text"],
                "source": by_id[doc_id]["metadata"]["source"],
                "section": by_id[doc_id]["metadata"]["section"],
                "score": round(rrf_scores[doc_id], 5),
            }
            for doc_id in ranked
        ]

        print(
            f"[RAG] Retrieval: "
            f"{(time.perf_counter() - started) * 1000:.0f} ms"
        )

        return results


# One retriever per Python process.
retriever = CloudRetriever()


def search_cloud_docs(query: str) -> dict:
    """Search local cloud documentation using hybrid retrieval."""
    results = retriever.search(query)

    if not results:
        return {
            "results": [],
            "message": "No relevant documentation was found.",
        }

    return {"results": results}
