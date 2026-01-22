# Skill 3: Hybrid Memory Architecture

Combining vector search and knowledge graphs for comprehensive context retrieval, inspired by human cognitive memory systems.

## Video Reference

Watch the full explanation: [Beyond RAG: The Three-Tier Memory Architecture for Intelligent Agents](https://youtube.com/@your-channel)

## Key Concepts

- **Three-Tier Memory**: Episodic (what happened), Semantic (facts/knowledge), Procedural (how-to patterns)
- **Vector Search**: Semantic similarity for breadth - finds related content even with different wording
- **Knowledge Graphs**: Multi-hop traversal for depth - follows explicit relationships between entities
- **Hybrid Retrieval**: Combining both approaches using Reciprocal Rank Fusion

## Examples

### 1. Vector Search (`vector_search.py`)

Demonstrates the foundation of modern RAG:

- Embedding text into high-dimensional vectors
- Cosine similarity for semantic matching
- Contextual embeddings for improved accuracy
- Metadata filtering

```python
# Key pattern: Embeddings capture MEANING, not just keywords
# "How do I get a refund?" matches "return policy allows refunds"
# even though the words are different

results = store.similarity_search(
    query_embedding=embedder.embed("How do I get a refund?"),
    top_k=5
)
```

### 2. Knowledge Graph (`knowledge_graph.py`)

Demonstrates multi-hop reasoning that vector search cannot achieve:

- Entity and relationship modeling
- Path traversal for complex queries
- Temporal knowledge graphs (time-aware)
- Impact analysis through graph connectivity

```python
# Key pattern: Answer questions requiring relationship chains
# "How does the delay in Project Apollo impact the Q3 budget that Sarah approved?"

# Traversal: Project Apollo -> [delayed by] -> Issue -> [affects] -> Budget -> [approved by] -> Sarah
paths = graph.traverse("project-apollo", [DELAYED_BY, AFFECTS, APPROVED_BY])
```

### 3. Hybrid Retrieval (`hybrid_retrieval.py`)

Demonstrates the complete three-tier memory architecture:

- Episodic memory (user interaction history)
- Semantic memory (knowledge base documents)
- Procedural memory (proven solution patterns)
- Reciprocal Rank Fusion for combining results

```python
# Key pattern: Comprehensive context from multiple sources
results = memory.hybrid_retrieve(
    query_embedding=embedding,
    user_id="user-123",        # Episodic: their history
    entities=["return-policy"],  # Graph: related entities
    task_type="return_request"   # Procedural: proven patterns
)
```

## Running the Examples

```bash
# Install dependencies
pip install -r requirements.txt

# Run Vector Search demonstration
python vector_search.py

# Run Knowledge Graph demonstration
python knowledge_graph.py

# Run Hybrid Retrieval demonstration
python hybrid_retrieval.py
```

## Architecture Patterns

| Pattern | When to Use | Key Benefit |
|---------|------------|-------------|
| Vector Search | Semantic similarity, unstructured data | Finds content even with different wording |
| Knowledge Graph | Multi-hop reasoning, relationship queries | Traces connections between entities |
| Hybrid Retrieval | Complex queries requiring both | Breadth AND depth |
| Contextual Embeddings | Ambiguous content | Disambiguates meaning with context |
| Hierarchical Retrieval | Large knowledge bases | Domain -> Document -> Chunk efficiency |

## Memory Tier Comparison

| Tier | Human Analogy | Agent Use Case | Example |
|------|--------------|----------------|---------|
| Episodic | "Remember when..." | User interaction history | "This user had a similar issue last week" |
| Semantic | "I know that..." | Facts and knowledge | "The return policy says 30 days" |
| Procedural | "Here's how to..." | Proven patterns | "Follow this workflow for returns" |

## Key Takeaways

1. **Vector search provides BREADTH**: Find semantically similar content, handle fuzzy queries
2. **Graphs provide DEPTH**: Follow explicit relationships, answer multi-hop questions
3. **Neither alone is sufficient**: The question "How does Project A affect Budget B via Issue C?" requires BOTH similarity and relationship traversal
4. **Reciprocal Rank Fusion**: Combine rankings from multiple sources without score normalization
5. **Contextual embeddings**: Prepend context to chunks before embedding - "implementation" in software != "implementation" in HR

## Connection to Other Skills

- **Skill 2 (Interoperability)**: Memory systems need protocol-agnostic interfaces
- **Skill 4 (Context Economics)**: Memory retrieval affects context window usage
- **Skill 5 (Observability)**: Trace which memories influenced agent decisions
- **Skill 6 (Data Governance)**: Memory content must be validated and governed
