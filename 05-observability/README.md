# Skill 5: Observability for Agentic Systems

Seeing inside the AI black box - tracing, metrics, and quality evaluation for production agents.

## Video Reference

Watch the full explanation: [When AI Breaks: Observability for Agentic Systems](https://youtube.com/@your-channel)

## Key Concepts

- **Distributed Tracing**: See the complete journey of a request through all agent operations
- **Semantic Quality Metrics**: Evaluate output quality beyond latency and errors
- **LLM-as-Judge**: Use AI to evaluate AI output at scale
- **Quality Gates**: Automated checks before deploying to production

## Examples

### 1. Distributed Tracing (`distributed_tracing.py`)

Demonstrates OpenTelemetry-style tracing for agents:

- Span creation for all operations (LLM calls, tools, retrieval, guardrails)
- Parent-child relationships showing the call hierarchy
- Custom attributes for agentic data (tokens, models, quality scores)
- Trace visualization as a tree

```python
# Key pattern: Every significant operation gets its own span
with tracer.span("llm_generate_response", SpanKind.LLM) as span:
    result = llm.generate(prompt)
    span.attributes["llm.model"] = "claude-3-5-haiku"
    span.attributes["llm.tokens"] = 570
```

### 2. Quality Metrics (`quality_metrics.py`)

Demonstrates semantic quality evaluation:

- Multi-dimensional scoring (groundedness, relevance, coherence, helpfulness)
- LLM-as-judge evaluation patterns
- Quality gates for deployment decisions
- Regression detection over time

```python
# Key pattern: LLM evaluates LLM output
judge = LLMAsJudge(judge_model="claude-3-5-haiku")
evaluation = judge.evaluate(
    query="What's your return policy?",
    response=agent_response,
    context=retrieved_docs
)
# evaluation.scores[GROUNDEDNESS] = 0.92
```

## Running the Examples

```bash
# Install dependencies
pip install -r requirements.txt

# Run Distributed Tracing demonstration
python distributed_tracing.py

# Run Quality Metrics demonstration
python quality_metrics.py
```

## The Three Pillars of Observability

| Pillar | What It Shows | Agentic Application |
|--------|--------------|---------------------|
| Traces | Request flow through system | LLM calls, tool use, retrieval |
| Metrics | Aggregated measurements | Latency, tokens, quality scores |
| Logs | Discrete events | State transitions, errors, decisions |

## Quality Dimensions

| Dimension | Question Answered | Failure Example |
|-----------|------------------|-----------------|
| Groundedness | Is it supported by sources? | Hallucinated facts |
| Relevance | Does it answer the question? | Off-topic response |
| Coherence | Is it internally consistent? | Contradictory statements |
| Completeness | Does it fully address the query? | Partial answer |
| Helpfulness | Is it actually useful? | Correct but unhelpful |

## Key Takeaways

1. **Traditional metrics aren't enough**: Latency and error rate don't tell you if answers are good
2. **Every operation gets a span**: LLM calls, tool use, retrieval, guardrails - trace them all
3. **LLM-as-judge scales**: Human evaluation doesn't scale; AI evaluation does
4. **Quality gates prevent regressions**: Don't deploy if quality benchmarks aren't met
5. **Continuous monitoring catches drift**: Production quality can degrade over time

## Connection to Other Skills

- **Skill 4 (Context Economics)**: Track token costs alongside latency
- **Skill 6 (Data Governance)**: Trace data lineage through agent decisions
- **Skill 9 (Agentic Security)**: Monitor for security-relevant events
- **Capstone**: Observability integrates with all production systems
