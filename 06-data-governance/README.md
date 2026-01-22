# Skill 6: Data Governance for Agentic AI

Ensuring agents work with accurate, current, and properly governed data - the foundation of reliability.

## Video Reference

Watch the full explanation: [Garbage In, Hallucinations Out: Why Data Governance is Your Agent's Foundation](https://youtube.com/@your-channel)

## Key Concepts

- **Data Validation**: Schema enforcement and quality checks before data enters your system
- **Freshness Tracking**: Detecting and handling stale data
- **Strict Grounding**: Constraining agents to only assert what's in the documents
- **Citation & Confidence**: Every claim should have a source; express uncertainty when appropriate

## Examples

### 1. Data Validation (`data_validation.py`)

Demonstrates data quality assurance:

- Schema validation for incoming documents
- Freshness tracking with TTL policies
- Entity resolution and deduplication
- Data quality dimensions (accuracy, completeness, consistency, timeliness)

```python
# Key pattern: Validate ALL data before it enters your system
validator = SchemaValidator()
results = validator.validate(document)
# results contains any schema violations

tracker = FreshnessTracker()
freshness = tracker.check_freshness(document)
# FreshnessLevel.FRESH, AGING, STALE, or EXPIRED
```

### 2. Grounding (`grounding.py`)

Demonstrates hallucination prevention:

- Strict grounding checks for claim verification
- Citation generation linking claims to sources
- Confidence scoring with thresholds
- Response gates based on confidence levels

```python
# Key pattern: Only assert what's in the documents
checker = GroundingChecker(strictness=0.7)
is_grounded, citations, confidence = checker.check_claim(claim, sources)

# Low confidence triggers caveats or refusal
gate = ConfidenceGate()
action = gate.apply_gate(response)  # respond, escalate, or refuse
```

## Running the Examples

```bash
# Install dependencies
pip install -r requirements.txt

# Run Data Validation demonstration
python data_validation.py

# Run Grounding demonstration
python grounding.py
```

## Data Quality Dimensions

| Dimension | Question | Validation Example |
|-----------|----------|-------------------|
| Accuracy | Is the data correct? | Schema validation, type checking |
| Completeness | Is anything missing? | Required field checks |
| Consistency | Do sources agree? | Cross-reference validation |
| Timeliness | Is the data current? | TTL enforcement, freshness checks |

## Confidence Response Actions

| Confidence | Level | Action |
|------------|-------|--------|
| 90%+ | High | Respond directly |
| 60-90% | Medium | Respond with caveats |
| 30-60% | Low | Escalate to human |
| <30% | Insufficient | Refuse to answer |

## Key Takeaways

1. **Garbage in, hallucinations out**: Perfect reasoning fails with bad data
2. **Validate at ingestion**: Don't let bad data enter your system
3. **Track freshness**: A policy from 2020 isn't relevant in 2026
4. **Strict grounding prevents hallucination**: Only assert what's documented
5. **Express uncertainty**: Low confidence should trigger caveats or refusal, not confident nonsense

## Connection to Other Skills

- **Skill 3 (Hybrid Memory)**: Memory content must be governed
- **Skill 5 (Observability)**: Track data lineage through agent decisions
- **Skill 9 (Agentic Security)**: Data governance prevents information leakage
- **Capstone**: Data quality is foundational to the entire system
