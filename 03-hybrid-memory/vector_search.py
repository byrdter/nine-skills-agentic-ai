"""
Vector Search Fundamentals

Demonstrates the foundation of modern RAG systems - converting text into
high-dimensional vectors (embeddings) for semantic similarity search.

This example shows:
- How embeddings capture semantic meaning
- Approximate nearest neighbor search
- The strengths of vector search (breadth, fuzzy matching)
- The limitations (no relationship understanding)

Reference: "Beyond RAG: The Three-Tier Memory Architecture" video - Chapter 3

Key Concept: Vector search finds relevant information even when
exact keywords don't match - 'car' and 'automobile' cluster together.
"""

import math
from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple, Optional
import hashlib


@dataclass
class Document:
    """
    A document in the vector store.

    Each document has:
    - Raw text content
    - An embedding (vector representation)
    - Metadata for filtering and attribution
    """
    doc_id: str
    content: str
    embedding: List[float]
    metadata: Dict[str, Any] = field(default_factory=dict)

    # For contextual embeddings (video concept)
    context_prefix: str = ""  # e.g., "Document: Policy Manual, Section: Returns"


@dataclass
class SearchResult:
    """Result from a vector similarity search."""
    document: Document
    similarity_score: float
    rank: int


class SimpleVectorStore:
    """
    A simplified vector store for educational purposes.

    In production, you would use:
    - Weaviate, Pinecone, Qdrant, Chroma, etc.
    - HNSW (Hierarchical Navigable Small World) for fast ANN search
    - GPU acceleration for large-scale deployments

    Key Principle: Embeddings capture MEANING, not just keywords.
    """

    def __init__(self):
        self._documents: Dict[str, Document] = {}

    def add_document(self, doc: Document) -> None:
        """Add a document to the store."""
        self._documents[doc.doc_id] = doc

    def add_documents(self, docs: List[Document]) -> None:
        """Add multiple documents."""
        for doc in docs:
            self.add_document(doc)

    def similarity_search(self, query_embedding: List[float],
                          top_k: int = 5,
                          metadata_filter: Optional[Dict[str, Any]] = None
                          ) -> List[SearchResult]:
        """
        Find documents most similar to the query embedding.

        Uses cosine similarity: how aligned are the vectors?
        - 1.0 = identical direction (maximum similarity)
        - 0.0 = perpendicular (no relationship)
        - -1.0 = opposite direction (opposite meaning)

        Key Principle: This finds semantically similar content
        even with completely different wording.
        """
        results = []

        for doc in self._documents.values():
            # Apply metadata filter if provided
            if metadata_filter:
                if not self._matches_filter(doc.metadata, metadata_filter):
                    continue

            # Calculate cosine similarity
            similarity = self._cosine_similarity(query_embedding, doc.embedding)
            results.append((doc, similarity))

        # Sort by similarity (highest first)
        results.sort(key=lambda x: x[1], reverse=True)

        # Return top_k results
        return [
            SearchResult(document=doc, similarity_score=score, rank=i+1)
            for i, (doc, score) in enumerate(results[:top_k])
        ]

    @staticmethod
    def _cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors.

        cosine_sim = (A · B) / (||A|| * ||B||)

        This measures the angle between vectors, not their magnitude.
        """
        if len(vec_a) != len(vec_b):
            raise ValueError("Vectors must have same dimensions")

        dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
        magnitude_a = math.sqrt(sum(a * a for a in vec_a))
        magnitude_b = math.sqrt(sum(b * b for b in vec_b))

        if magnitude_a == 0 or magnitude_b == 0:
            return 0.0

        return dot_product / (magnitude_a * magnitude_b)

    @staticmethod
    def _matches_filter(metadata: Dict[str, Any],
                        filter_dict: Dict[str, Any]) -> bool:
        """Check if document metadata matches the filter."""
        for key, value in filter_dict.items():
            if key not in metadata or metadata[key] != value:
                return False
        return True


class SimpleEmbedder:
    """
    A simplified embedding generator for educational purposes.

    In production, you would use:
    - OpenAI text-embedding-3-small/large
    - Sentence Transformers (all-MiniLM-L6-v2, etc.)
    - Cohere embed-english-v3.0
    - Custom fine-tuned models

    This simple version uses word frequency as a stand-in.
    Real embeddings capture deep semantic meaning.
    """

    def __init__(self, vocab_size: int = 100):
        self.vocab_size = vocab_size
        # In production, this would be a trained neural network

    def embed(self, text: str) -> List[float]:
        """
        Generate an embedding for the given text.

        Real embeddings are dense vectors (e.g., 384, 768, or 1536 dimensions)
        that capture semantic meaning through neural network processing.
        """
        # Simplified: hash words to create pseudo-embedding
        # Real embeddings capture meaning, not just word presence
        words = text.lower().split()
        embedding = [0.0] * self.vocab_size

        for word in words:
            # Hash word to get consistent index
            index = int(hashlib.md5(word.encode()).hexdigest(), 16) % self.vocab_size
            embedding[index] += 1.0

        # Normalize to unit vector
        magnitude = math.sqrt(sum(x * x for x in embedding))
        if magnitude > 0:
            embedding = [x / magnitude for x in embedding]

        return embedding


def demonstrate_contextual_embeddings():
    """
    Demonstrate the contextual embeddings concept from the video.

    Key Insight: When you embed a document chunk, prepend it with context.
    A paragraph about 'implementation' means different things in different docs.
    """
    print("\n" + "=" * 60)
    print("Contextual Embeddings Demonstration")
    print("=" * 60)

    # Same text, different contexts
    text = "The implementation process should follow standard procedures."

    contexts = [
        "Document: Software Development Guide, Section: Coding Standards",
        "Document: HR Policy Manual, Section: Hiring Process",
        "Document: Construction Manual, Section: Building Safety"
    ]

    print("\nSame text with different context prefixes:")
    print(f"Text: '{text}'")
    print("\nContextual versions:")
    for ctx in contexts:
        combined = f"{ctx}\n\n{text}"
        print(f"\n  Context: {ctx[:50]}...")
        print(f"  Combined text for embedding: {combined[:80]}...")

    print("\n  Key Principle: Context disambiguates meaning!")
    print("  'Implementation' in software != 'Implementation' in HR")


# =============================================================================
# Demonstration
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("Vector Search Demonstration")
    print("=" * 70)

    # Create embedder and vector store
    embedder = SimpleEmbedder(vocab_size=50)
    store = SimpleVectorStore()

    # Add sample documents (simulating a knowledge base)
    documents = [
        Document(
            doc_id="doc-001",
            content="The return policy allows refunds within 30 days of purchase.",
            embedding=embedder.embed("The return policy allows refunds within 30 days of purchase."),
            metadata={"type": "policy", "department": "customer_service"}
        ),
        Document(
            doc_id="doc-002",
            content="Customers can get their money back if they return items within a month.",
            embedding=embedder.embed("Customers can get their money back if they return items within a month."),
            metadata={"type": "faq", "department": "customer_service"}
        ),
        Document(
            doc_id="doc-003",
            content="Our shipping rates depend on the destination and package weight.",
            embedding=embedder.embed("Our shipping rates depend on the destination and package weight."),
            metadata={"type": "policy", "department": "logistics"}
        ),
        Document(
            doc_id="doc-004",
            content="Product warranty covers manufacturing defects for 12 months.",
            embedding=embedder.embed("Product warranty covers manufacturing defects for 12 months."),
            metadata={"type": "policy", "department": "support"}
        ),
    ]

    store.add_documents(documents)

    # Demonstrate semantic search
    print("\n[1] Semantic Similarity Search")
    print("-" * 50)

    # Query that uses different words but same meaning
    query = "How do I get a refund?"
    query_embedding = embedder.embed(query)

    print(f"Query: '{query}'")
    print("\nResults (note: 'refund' not in doc-002, but it matches semantically):")

    results = store.similarity_search(query_embedding, top_k=3)
    for result in results:
        print(f"\n  #{result.rank}: {result.document.content[:60]}...")
        print(f"      Similarity: {result.similarity_score:.3f}")
        print(f"      ID: {result.document.doc_id}")

    # Demonstrate metadata filtering
    print("\n[2] Filtered Search (by department)")
    print("-" * 50)

    query = "What is the policy?"
    query_embedding = embedder.embed(query)

    print(f"Query: '{query}' (filtered to customer_service)")

    results = store.similarity_search(
        query_embedding,
        top_k=5,
        metadata_filter={"department": "customer_service"}
    )

    print(f"Found {len(results)} results in customer_service:")
    for result in results:
        print(f"  - {result.document.content[:50]}...")

    # Show the limitation
    print("\n[3] Vector Search Limitation")
    print("-" * 50)
    print("""
Vector search excels at:
  - Finding semantically similar content
  - Handling unstructured data (docs, emails, chats)
  - "Vibes-based" queries (find similar documents)

Vector search CANNOT:
  - Understand relationships between entities
  - Answer multi-hop questions
  - Trace paths: "How does Project A affect Budget B?"

For that, you need GRAPHS (see knowledge_graph.py)
    """)

    # Demonstrate contextual embeddings
    demonstrate_contextual_embeddings()

    print("\n" + "=" * 70)
    print("Key Takeaways:")
    print("1. Embeddings capture MEANING, not just keywords")
    print("2. Cosine similarity finds semantically related content")
    print("3. Contextual embeddings improve retrieval accuracy")
    print("4. Vector search provides BREADTH but not DEPTH (relationships)")
    print("=" * 70)
