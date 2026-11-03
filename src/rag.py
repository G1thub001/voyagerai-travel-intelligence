from functools import lru_cache
from hashlib import sha256
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer


# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
GUIDES_DIR = PROJECT_ROOT / "data" / "travel_guides"
CHROMA_DIR = PROJECT_ROOT / "storage" / "chroma"

# Retrieval configuration
COLLECTION_NAME = "travel_guides"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

CHUNK_SIZE = 600
CHUNK_OVERLAP = 100
DEFAULT_RESULTS = 2
INDEX_VERSION = "3"


@lru_cache(maxsize=1)
def get_embedding_model():
    """Load the embedding model once and reuse it."""
    return SentenceTransformer(EMBEDDING_MODEL)


@lru_cache(maxsize=1)
def get_collection():
    """Create or retrieve the persistent ChromaDB collection."""
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def chunk_text(text: str) -> list[str]:
    """
    Split text into paragraph-aware, overlapping chunks.

    Prefer paragraph and sentence boundaries. Fall back to word
    boundaries when a sentence exceeds the configured chunk size.
    """
    if not text or not text.strip():
        return []

    import re

    paragraphs = [
        paragraph.strip()
        for paragraph in re.split(r"\n\s*\n", text)
        if paragraph.strip()
    ]

    chunks = []
    current_chunk = ""

    def split_long_paragraph(paragraph: str) -> list[str]:
        sentences = re.split(r"(?<=[.!?])\s+", paragraph)
        pieces = []
        current = ""

        for sentence in sentences:
            if len(sentence) > CHUNK_SIZE:
                if current:
                    pieces.append(current)
                    current = ""

                words = sentence.split()
                word_chunk = ""

                for word in words:
                    candidate = (
                        f"{word_chunk} {word}".strip()
                    )

                    if len(candidate) <= CHUNK_SIZE:
                        word_chunk = candidate
                    else:
                        if word_chunk:
                            pieces.append(word_chunk)

                        word_chunk = word

                if word_chunk:
                    pieces.append(word_chunk)

                continue

            candidate = f"{current} {sentence}".strip()

            if len(candidate) <= CHUNK_SIZE:
                current = candidate
            else:
                if current:
                    pieces.append(current)

                current = sentence

        if current:
            pieces.append(current)

        return pieces

    for paragraph in paragraphs:
        if len(paragraph) > CHUNK_SIZE:
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = ""

            chunks.extend(split_long_paragraph(paragraph))
            continue

        candidate = (
            f"{current_chunk}\n\n{paragraph}"
            if current_chunk
            else paragraph
        )

        if len(candidate) <= CHUNK_SIZE:
            current_chunk = candidate
        else:
            if current_chunk:
                chunks.append(current_chunk)

            current_chunk = paragraph

    if current_chunk:
        chunks.append(current_chunk)

    # Apply word-boundary overlap between consecutive chunks.
    overlapped_chunks = []

    for index, chunk in enumerate(chunks):
        if index == 0:
            overlapped_chunks.append(chunk)
            continue

        previous_words = chunks[index - 1].split()
        overlap_words = []
        overlap_length = 0

        for word in reversed(previous_words):
            additional_length = len(word) + (
                1 if overlap_words else 0
            )

            if overlap_length + additional_length > CHUNK_OVERLAP:
                break

            overlap_words.insert(0, word)
            overlap_length += additional_length

        overlap = " ".join(overlap_words)
        combined = f"{overlap}\n\n{chunk}" if overlap else chunk

        overlapped_chunks.append(combined)

    return overlapped_chunks


def get_document_hash(content: str) -> str:
    """Generate a SHA-256 fingerprint for document change detection."""
    return sha256(content.encode("utf-8")).hexdigest()


def ensure_index() -> int:
    """
    Index new or modified travel guides.

    Unchanged documents are skipped. Removed source documents
    are deleted from the collection.
    """
    GUIDES_DIR.mkdir(parents=True, exist_ok=True)

    collection = get_collection()

    guide_files = sorted(GUIDES_DIR.glob("*.md"))

    existing = collection.get(include=["metadatas"])

    existing_sources = {}

    for document_id, metadata in zip(
        existing["ids"],
        existing["metadatas"],
    ):
        source = metadata["source"]

        existing_sources.setdefault(source, []).append(
            {
                "id": document_id,
                "content_hash": metadata["content_hash"],
                "index_version": metadata.get("index_version"),
            }
        )

    current_sources = {path.name for path in guide_files}

    # Remove documents that no longer exist in the source directory.
    for source in existing_sources:
        if source not in current_sources:
            collection.delete(where={"source": source})

    indexed_count = 0

    for guide_path in guide_files:
        content = guide_path.read_text(encoding="utf-8")

        if not content.strip():
            continue

        content_hash = get_document_hash(content)
        source = guide_path.name

        previous_chunks = existing_sources.get(source, [])

        # Skip documents that have not changed.
        if previous_chunks and all(
            item["content_hash"] == content_hash
            and item.get("index_version") == INDEX_VERSION
            for item in previous_chunks
        ):
            continue

        # Replace outdated chunks for this source.
        if previous_chunks:
            collection.delete(where={"source": source})

        chunks = chunk_text(content)

        if not chunks:
            continue

        embeddings = get_embedding_model().encode(
            chunks,
            convert_to_numpy=True,
        )

        document_ids = [
            f"{source}::chunk::{index}"
            for index in range(len(chunks))
        ]

        metadatas = [
            {
                "source": source,
                "chunk_index": index,
                "content_hash": content_hash,
                "index_version": INDEX_VERSION,
            }
            for index in range(len(chunks))
        ]

        collection.upsert(
            ids=document_ids,
            documents=chunks,
            embeddings=embeddings.tolist(),
            metadatas=metadatas,
        )

        indexed_count += len(chunks)

    return indexed_count


def search_guides(
    query: str,
    n_results: int = DEFAULT_RESULTS,
) -> list[str]:
    """Retrieve the most semantically relevant travel guide chunks."""
    if not query or not query.strip():
        raise ValueError("Search query cannot be empty.")

    if isinstance(n_results, bool) or not isinstance(n_results, int):
        raise ValueError("n_results must be a positive integer.")

    if n_results < 1:
        raise ValueError("n_results must be a positive integer.")

    collection = get_collection()

    if collection.count() == 0:
        return []

    query_embedding = get_embedding_model().encode(
        [query.strip()],
        convert_to_numpy=True,
    )

    results = collection.query(
        query_embeddings=query_embedding.tolist(),
        n_results=min(n_results, collection.count()),
        include=["documents", "metadatas", "distances"],
    )

    retrieved_chunks = []

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]

    for document, metadata in zip(documents, metadatas):
        source = metadata["source"]

        retrieved_chunks.append(
            f"Source: {source}\n{document}"
        )

    return retrieved_chunks


def rag_ask(question: str) -> str:
    """Retrieve relevant information from the travel knowledge base."""
    results = search_guides(question)

    if not results:
        return "I could not find anything relevant in the travel guides."

    return "Based on the travel knowledge base:\n\n" + "\n\n---\n\n".join(
        results
    )