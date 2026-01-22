# Skill 4: Context Economics

Managing the finite resource of context windows - optimizing for cost, latency, and quality.

## Video Reference

Watch the full explanation: [The $10,000 Prompt: Mastering Context Economics for Agentic AI](https://youtube.com/@your-channel)

## Key Concepts

- **Prefix Caching**: Structure prompts so static content (system prompts) is cached and reused
- **Hierarchical Summarization**: Compress older context while preserving recent detail
- **Cost Attribution**: Know who/what is spending your token budget
- **Context Optimization**: Include high-value information, exclude noise

## Examples

### 1. Prefix Caching (`prefix_caching.py`)

Demonstrates cache-friendly prompt structure:

- Static content FIRST (system prompt, RAG context) = cached
- Dynamic content LAST (user query) = computed fresh
- Platform-specific caching strategies (Anthropic, OpenAI, Gemini)

```python
# Key pattern: Static content FIRST, dynamic content LAST
prompt = PromptStructure(
    system_prompt="...",    # Layer 1: ALWAYS cached
    rag_context="...",      # Layer 2: OFTEN cached
    conversation="...",     # Layer 3: SOMETIMES cached
    current_query="..."     # Layer 4: NEVER cached
)
```

### 2. Context Compaction (`context_compaction.py`)

Demonstrates techniques for managing unbounded history:

- Sliding window with summarization (detailed recent, summarized old)
- Hierarchical summarization (turn -> session -> user levels)
- Semantic compression (entity extraction, deduplication)

```python
# Key pattern: Recent = detailed, older = summarized
window = SlidingWindowManager(window_size=10)
window.add_turn("user", "I want to return...")
window.add_turn("assistant", "I'd be happy to help...")
# Oldest turns are automatically summarized when window exceeds limit
```

### 3. Cost Tracking (`cost_tracking.py`)

Demonstrates production cost management:

- Per-request cost calculation with model pricing
- Budget allocation and alerts by team/project
- Anomaly detection for runaway loops
- Optimization recommendations

```python
# Key pattern: If you can't measure it, you can't optimize it
tracker = CostTracker()
tracker.set_budget("customer-service", 1000.0)  # $1000/month
tracker.record_usage(record)  # Track every API call
recommendations = OptimizationRecommender.analyze(tracker)
```

## Running the Examples

```bash
# Install dependencies
pip install -r requirements.txt

# Run Prefix Caching demonstration
python prefix_caching.py

# Run Context Compaction demonstration
python context_compaction.py

# Run Cost Tracking demonstration
python cost_tracking.py
```

## Optimization Strategies

| Strategy | Savings | Complexity | When to Use |
|----------|---------|------------|-------------|
| Prefix Caching | 50-90% | Low | Always - structure prompts correctly |
| Model Routing | 40-60% | Medium | Route simple queries to cheaper models |
| Summarization | 20-40% | Medium | Long-running conversations |
| Output Limits | 10-20% | Low | Verbose responses |
| Batch Processing | 30-50% | High | High-volume pipelines |

## Compression Ratios

| Level | Ratio | Use Case |
|-------|-------|----------|
| Turn Summary | 5:1 | Individual exchanges |
| Session Summary | 10:1 | Complete conversations |
| User Profile | 20:1 | Long-term patterns |

## Key Takeaways

1. **Static content FIRST**: System prompts and RAG context should come before dynamic content
2. **Hierarchical summarization**: Different time horizons need different granularity
3. **Attribution enables accountability**: Track costs by team, project, and workflow
4. **Anomaly detection prevents disasters**: A runaway loop can burn $10,000 before anyone notices
5. **Data-driven optimization**: Let usage patterns guide your optimization efforts

## Platform-Specific Caching

| Platform | Min Tokens | TTL | Cost Reduction | API Type |
|----------|-----------|-----|----------------|----------|
| Anthropic | 1,024 | 5 min | 90% | Explicit |
| OpenAI | Auto | ~1 hour | 50% | Automatic |
| Gemini | Up to 32K | 1 hour | Variable | Explicit |

## Connection to Other Skills

- **Skill 3 (Hybrid Memory)**: Memory retrieval affects context usage
- **Skill 5 (Observability)**: Track token metrics alongside latency and quality
- **Skill 8 (Tool Engineering)**: Tool descriptions consume context budget
- **Capstone**: Budget management integrates with all other systems
