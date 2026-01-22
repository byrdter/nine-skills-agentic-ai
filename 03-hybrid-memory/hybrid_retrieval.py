"""
Hybrid Retrieval: Combining Vector Search and Graph Traversal

Demonstrates the three-tier memory architecture that combines:
- Episodic Memory: What happened when (user interactions, events)
- Semantic Memory: Facts and knowledge (documents, domain expertise)
- Procedural Memory: How-to knowledge (solution patterns, workflows)

This example shows:
- Reciprocal Rank Fusion for combining results
- Hierarchical retrieval (domain -> document -> chunk)
- The complete hybrid retrieval pattern

Reference: "Beyond RAG: The Three-Tier Memory Architecture" video - Chapters 2 & 5

Key Concept: Vector search provides BREADTH (find similar content).
Graph traversal provides DEPTH (follow relationships). Together: comprehensive context.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from enum import Enum


# =============================================================================
# Three-Tier Memory Architecture
# =============================================================================

class MemoryTier(Enum):
    """
    The three tiers of agent memory, inspired by human cognition.

    Each tier serves a different purpose and uses different retrieval strategies.
    """
    EPISODIC = "episodic"       # What happened when (events, interactions)
    SEMANTIC = "semantic"       # Facts and knowledge (documents, entities)
    PROCEDURAL = "procedural"   # How-to knowledge (patterns, workflows)


@dataclass
class MemoryItem:
    """A single item in the memory system."""
    item_id: str
    tier: MemoryTier
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: List[float] = field(default_factory=list)

    # For episodic memories
    timestamp: Optional[datetime] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None

    # For procedural memories
    success_rate: Optional[float] = None
    use_count: int = 0


@dataclass
class RetrievalResult:
    """Result from any retrieval method."""
    item: MemoryItem
    score: float
    source: str         # "vector", "graph", "hybrid"
    rank: int = 0


# =============================================================================
# Reciprocal Rank Fusion
# =============================================================================

def reciprocal_rank_fusion(ranked_lists: List[List[RetrievalResult]],
                           k: int = 60) -> List[RetrievalResult]:
    """
    Combine rankings from multiple retrieval sources using RRF.

    Reciprocal Rank Fusion gives credit to items that appear high in
    MULTIPLE lists. It's robust and doesn't require score normalization.

    Formula: RRF_score(d) = sum(1 / (k + rank(d, list_i)))

    Key Principle: Items that appear high in both vector AND graph results
    get boosted to the top.

    Args:
        ranked_lists: List of ranked result lists from different sources
        k: Constant to prevent high scores for top ranks (default 60)

    Returns:
        Fused ranking with combined scores
    """
    # Track RRF scores by item_id
    rrf_scores: Dict[str, float] = {}
    item_map: Dict[str, MemoryItem] = {}

    for results in ranked_lists:
        for i, result in enumerate(results):
            rank = i + 1  # 1-indexed
            item_id = result.item.item_id

            # RRF formula
            rrf_contribution = 1.0 / (k + rank)

            if item_id not in rrf_scores:
                rrf_scores[item_id] = 0.0
                item_map[item_id] = result.item

            rrf_scores[item_id] += rrf_contribution

    # Sort by RRF score
    sorted_items = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

    # Build final results
    return [
        RetrievalResult(
            item=item_map[item_id],
            score=score,
            source="hybrid_rrf",
            rank=i + 1
        )
        for i, (item_id, score) in enumerate(sorted_items)
    ]


# =============================================================================
# Hybrid Memory System
# =============================================================================

class HybridMemorySystem:
    """
    A hybrid memory system implementing the three-tier architecture.

    This combines:
    1. Vector search for semantic similarity (breadth)
    2. Graph traversal for relationship following (depth)
    3. Temporal indexing for episodic memory

    Key Principle: Different query types need different retrieval strategies.
    The hybrid system dynamically selects the best approach.
    """

    def __init__(self):
        # Simulated stores (in production, use real databases)
        self._memories: Dict[str, MemoryItem] = {}
        self._by_tier: Dict[MemoryTier, List[MemoryItem]] = {
            tier: [] for tier in MemoryTier
        }
        self._by_user: Dict[str, List[MemoryItem]] = {}

        # Simulated graph (entity relationships)
        self._entity_to_memories: Dict[str, List[str]] = {}

    def store(self, item: MemoryItem) -> None:
        """Store a memory item."""
        self._memories[item.item_id] = item
        self._by_tier[item.tier].append(item)

        if item.user_id:
            if item.user_id not in self._by_user:
                self._by_user[item.user_id] = []
            self._by_user[item.user_id].append(item)

        # Index by mentioned entities (simplified)
        for entity in item.metadata.get("entities", []):
            if entity not in self._entity_to_memories:
                self._entity_to_memories[entity] = []
            self._entity_to_memories[entity].append(item.item_id)

    def retrieve_episodic(self, user_id: str, session_id: Optional[str] = None,
                          limit: int = 10) -> List[RetrievalResult]:
        """
        Retrieve episodic memories - what happened to this user.

        Used for: "This user had a similar issue two weeks ago..."

        Key Principle: Episodic memory provides personalized context
        based on the user's history.
        """
        memories = self._by_user.get(user_id, [])

        if session_id:
            memories = [m for m in memories if m.session_id == session_id]

        # Sort by timestamp (most recent first)
        memories = sorted(
            [m for m in memories if m.timestamp],
            key=lambda x: x.timestamp,
            reverse=True
        )[:limit]

        return [
            RetrievalResult(item=m, score=1.0 / (i + 1), source="episodic", rank=i + 1)
            for i, m in enumerate(memories)
        ]

    def retrieve_semantic(self, query_embedding: List[float],
                          limit: int = 10) -> List[RetrievalResult]:
        """
        Retrieve semantic memories - facts and knowledge.

        Used for: "Here's what the policy says about returns..."

        This is the vector search component.
        """
        semantic_memories = self._by_tier[MemoryTier.SEMANTIC]

        # Simplified similarity (in production, use proper cosine similarity)
        results = []
        for memory in semantic_memories:
            if memory.embedding:
                # Mock similarity score
                score = sum(a * b for a, b in zip(
                    query_embedding[:10], memory.embedding[:10]
                )) / 10
                results.append((memory, abs(score)))

        results.sort(key=lambda x: x[1], reverse=True)

        return [
            RetrievalResult(item=m, score=s, source="semantic_vector", rank=i + 1)
            for i, (m, s) in enumerate(results[:limit])
        ]

    def retrieve_by_entity(self, entity: str, limit: int = 10) -> List[RetrievalResult]:
        """
        Retrieve memories related to a specific entity.

        Used for: "What do we know about Project Apollo?"

        This is the graph traversal component (simplified).
        """
        memory_ids = self._entity_to_memories.get(entity, [])
        memories = [self._memories[mid] for mid in memory_ids if mid in self._memories]

        return [
            RetrievalResult(item=m, score=1.0 / (i + 1), source="graph_entity", rank=i + 1)
            for i, m in enumerate(memories[:limit])
        ]

    def retrieve_procedural(self, task_type: str, limit: int = 5) -> List[RetrievalResult]:
        """
        Retrieve procedural memories - proven solution patterns.

        Used for: "Here's how we solved similar issues before..."

        Key Principle: Don't reason from scratch. Retrieve and adapt
        proven patterns.
        """
        procedural_memories = self._by_tier[MemoryTier.PROCEDURAL]

        # Filter by task type and sort by success rate
        relevant = [
            m for m in procedural_memories
            if m.metadata.get("task_type") == task_type
        ]

        # Sort by success rate (highest first)
        relevant.sort(
            key=lambda x: (x.success_rate or 0, x.use_count),
            reverse=True
        )

        return [
            RetrievalResult(item=m, score=m.success_rate or 0.5, source="procedural", rank=i + 1)
            for i, m in enumerate(relevant[:limit])
        ]

    def hybrid_retrieve(self, query_embedding: List[float],
                        user_id: Optional[str] = None,
                        entities: Optional[List[str]] = None,
                        task_type: Optional[str] = None,
                        limit: int = 10) -> List[RetrievalResult]:
        """
        Perform hybrid retrieval combining all memory tiers.

        This is the main retrieval interface - it:
        1. Retrieves from multiple sources
        2. Combines results using Reciprocal Rank Fusion
        3. Returns a unified, ranked result set

        Key Principle: Comprehensive context requires multiple retrieval strategies.
        """
        ranked_lists = []

        # Semantic (vector) retrieval
        semantic_results = self.retrieve_semantic(query_embedding, limit=limit)
        if semantic_results:
            ranked_lists.append(semantic_results)

        # Episodic (user history) retrieval
        if user_id:
            episodic_results = self.retrieve_episodic(user_id, limit=limit)
            if episodic_results:
                ranked_lists.append(episodic_results)

        # Graph (entity) retrieval
        if entities:
            for entity in entities:
                entity_results = self.retrieve_by_entity(entity, limit=limit)
                if entity_results:
                    ranked_lists.append(entity_results)

        # Procedural (pattern) retrieval
        if task_type:
            procedural_results = self.retrieve_procedural(task_type, limit=limit)
            if procedural_results:
                ranked_lists.append(procedural_results)

        # Fuse all results
        if not ranked_lists:
            return []

        return reciprocal_rank_fusion(ranked_lists)[:limit]


# =============================================================================
# Hierarchical Retrieval
# =============================================================================

@dataclass
class HierarchicalIndex:
    """
    Hierarchical retrieval structure for efficient search.

    Levels:
    1. Domain/Category (e.g., "Customer Service", "Legal")
    2. Document (e.g., "Return Policy v2.3")
    3. Chunk (e.g., "Section 4.2: Exceptions")

    Key Principle: Check the drawer label before searching the folders.
    This reduces latency and eliminates irrelevant results.
    """
    domains: Dict[str, List[str]] = field(default_factory=dict)  # domain -> doc_ids
    documents: Dict[str, Dict[str, Any]] = field(default_factory=dict)  # doc_id -> metadata
    chunks: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)  # doc_id -> chunks


def hierarchical_retrieve(index: HierarchicalIndex,
                          query: str,
                          domain_hint: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Perform hierarchical retrieval.

    Step 1: Identify relevant domain (if not provided)
    Step 2: Narrow to documents in that domain
    Step 3: Search chunks within relevant documents

    This approach is faster and more precise than flat search.
    """
    # Step 1: Domain selection
    if domain_hint:
        relevant_domains = [domain_hint]
    else:
        # In production, use embeddings to find relevant domains
        relevant_domains = list(index.domains.keys())[:2]

    # Step 2: Document filtering
    relevant_docs = []
    for domain in relevant_domains:
        relevant_docs.extend(index.domains.get(domain, []))

    # Step 3: Chunk retrieval
    results = []
    for doc_id in relevant_docs:
        chunks = index.chunks.get(doc_id, [])
        for chunk in chunks:
            # In production, use vector similarity
            if any(word in chunk.get("content", "").lower() for word in query.lower().split()):
                results.append({
                    "doc_id": doc_id,
                    "doc_metadata": index.documents.get(doc_id, {}),
                    "chunk": chunk
                })

    return results


# =============================================================================
# Demonstration
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("Hybrid Retrieval Demonstration")
    print("=" * 70)

    # Create hybrid memory system
    memory = HybridMemorySystem()

    # Add episodic memories (user interaction history)
    print("\n[1] Adding Episodic Memories (User History)")
    print("-" * 50)
    memory.store(MemoryItem(
        item_id="ep-001",
        tier=MemoryTier.EPISODIC,
        content="User asked about return policy, resolved with 30-day refund info",
        timestamp=datetime(2026, 1, 10),
        user_id="user-123",
        session_id="sess-001",
        metadata={"outcome": "resolved", "topic": "returns"}
    ))
    memory.store(MemoryItem(
        item_id="ep-002",
        tier=MemoryTier.EPISODIC,
        content="User had shipping delay issue, provided tracking update",
        timestamp=datetime(2026, 1, 5),
        user_id="user-123",
        session_id="sess-002",
        metadata={"outcome": "resolved", "topic": "shipping"}
    ))
    print("  Added 2 episodic memories for user-123")

    # Add semantic memories (knowledge base)
    print("\n[2] Adding Semantic Memories (Knowledge Base)")
    print("-" * 50)
    memory.store(MemoryItem(
        item_id="sem-001",
        tier=MemoryTier.SEMANTIC,
        content="Return policy: Items may be returned within 30 days for full refund.",
        embedding=[0.1, 0.2, 0.3, 0.4, 0.5] * 10,  # Mock embedding
        metadata={"entities": ["return-policy"], "source": "policy-manual"}
    ))
    memory.store(MemoryItem(
        item_id="sem-002",
        tier=MemoryTier.SEMANTIC,
        content="Shipping times: Standard 5-7 days, Express 2-3 days.",
        embedding=[0.2, 0.1, 0.4, 0.3, 0.6] * 10,
        metadata={"entities": ["shipping-info"], "source": "shipping-guide"}
    ))
    print("  Added 2 semantic memories (policy documents)")

    # Add procedural memories (solution patterns)
    print("\n[3] Adding Procedural Memories (Solution Patterns)")
    print("-" * 50)
    memory.store(MemoryItem(
        item_id="proc-001",
        tier=MemoryTier.PROCEDURAL,
        content="Return handling workflow: 1) Verify order 2) Check eligibility 3) Generate label 4) Process refund",
        metadata={"task_type": "return_request"},
        success_rate=0.95,
        use_count=150
    ))
    print("  Added 1 procedural memory (return workflow pattern)")

    # Perform hybrid retrieval
    print("\n[4] Hybrid Retrieval")
    print("-" * 50)
    print("Query: Customer asking about returns")
    print("User: user-123")
    print("Entities: return-policy")
    print("Task: return_request")

    results = memory.hybrid_retrieve(
        query_embedding=[0.1, 0.2, 0.3, 0.4, 0.5] * 10,
        user_id="user-123",
        entities=["return-policy"],
        task_type="return_request",
        limit=5
    )

    print("\nHybrid Results (RRF-fused):")
    for result in results:
        print(f"\n  #{result.rank}: {result.item.content[:60]}...")
        print(f"      Tier: {result.item.tier.value}")
        print(f"      Source: {result.source}")
        print(f"      Score: {result.score:.4f}")

    # Demonstrate RRF
    print("\n[5] Reciprocal Rank Fusion Explained")
    print("-" * 50)
    print("""
Why RRF works:
  - Items appearing high in MULTIPLE lists get boosted
  - No need for score normalization across sources
  - Robust to different score distributions

Example:
  Vector search ranks: [A, B, C, D]
  Graph search ranks:  [C, A, E, F]

  RRF scores:
  - A: 1/(60+1) + 1/(60+2) = 0.0164 + 0.0161 = 0.0325
  - C: 1/(60+3) + 1/(60+1) = 0.0159 + 0.0164 = 0.0323
  - B: 1/(60+2) = 0.0161
  - E: 1/(60+3) = 0.0159

  Fused ranking: [A, C, B, D, E, F]
  (A beats C because it's #1 in vector search)
    """)

    print("\n" + "=" * 70)
    print("Key Takeaways:")
    print("1. Three tiers: Episodic (events), Semantic (facts), Procedural (patterns)")
    print("2. Vector search provides BREADTH (semantic similarity)")
    print("3. Graph traversal provides DEPTH (relationships)")
    print("4. RRF combines rankings without score normalization")
    print("5. Hierarchical retrieval: domain -> document -> chunk")
    print("=" * 70)
