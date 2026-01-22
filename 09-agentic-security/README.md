# Skill 9: Agentic Security

Defending against prompt injection, data exfiltration, and adversarial attacks on AI systems.

## Video Reference

Watch the full explanation: [Attacking Your Own AI: Red Teaming and Security for Agentic Systems](https://youtube.com/@your-channel)

## Key Concepts

- **Prompt Injection**: Attacks written in plain English that manipulate agent behavior
- **Defense in Depth**: Multiple layers of protection so one bypass doesn't compromise everything
- **Input/Output Guardrails**: Filter content before it reaches the agent and before it reaches users
- **Human-in-the-Loop**: Gate high-risk operations with human approval

## Examples

### 1. Guardrails (`guardrails.py`)

Demonstrates multi-layer defense architecture:

- Input guardrails for prompt injection detection
- Output guardrails for PII detection and redaction
- Human-in-the-loop for high-risk operations
- Defense in depth pipeline

```python
# Key pattern: Defense in depth - layer multiple guardrails
pipeline = DefenseInDepthPipeline()

# Input: Block injection attempts
result = pipeline.process_input(user_message, source="user")

# Output: Redact PII before returning to user
result = pipeline.process_output(agent_response)
# Automatically redacts: emails, phones, SSNs, API keys
```

## Running the Examples

```bash
# Install dependencies
pip install -r requirements.txt

# Run Guardrails demonstration
python guardrails.py
```

## OWASP Top 10 for Agentic AI

| Threat | Description | Defense |
|--------|-------------|---------|
| Prompt Injection | Malicious instructions in user/document input | Input guardrails, content filtering |
| Insecure Output | PII leakage, API keys in responses | Output guardrails, redaction |
| Excessive Agency | Over-privileged agents cause more damage | Least privilege, role-based access |
| Data Poisoning | Corrupted knowledge base content | Data validation, lineage tracking |
| Model DoS | Resource exhaustion attacks | Rate limiting, input validation |

## Defense Layers

| Layer | Purpose | Examples |
|-------|---------|----------|
| Input Guardrails | Block malicious input | Injection detection, jailbreak filters |
| Output Guardrails | Prevent data leakage | PII redaction, policy enforcement |
| Action Confirmation | Gate high-risk operations | Human approval for deletions, payments |
| Monitoring | Detect anomalous behavior | Security event logging, alerting |

## Guardrail Actions

| Action | When Used | Effect |
|--------|-----------|--------|
| ALLOW | No threat detected | Content passes through |
| BLOCK | High-confidence threat | Request rejected |
| SANITIZE | PII detected | Content modified/redacted |
| FLAG | Low-confidence threat | Allowed but flagged for review |
| ESCALATE | High-risk operation | Requires human approval |

## Key Takeaways

1. **Your agent is an attack surface**: Attackers don't need exploits - just convincing text
2. **Prompt injection is the new SQL injection**: Except it's harder to detect
3. **Defense in depth is essential**: No single guardrail is perfect
4. **Indirect injection is most dangerous**: Malicious content in "trusted" documents
5. **Test adversarially**: Use Garak, PyRIT, or Promptfoo before attackers find vulnerabilities

## Production Tools

- **Garak**: LLM vulnerability scanner (injection, jailbreak, PII)
- **PyRIT**: Microsoft's Python Risk Identification Toolkit
- **Promptfoo**: Red teaming with custom scenarios
- **NeMo Guardrails**: NVIDIA's guardrail framework
- **Lakera Guard**: Dedicated prompt injection protection

## Connection to Other Skills

- **Skill 2 (Interoperability)**: Security at every boundary
- **Skill 5 (Observability)**: Monitor for security-relevant events
- **Skill 7 (Non-Human Identity)**: Least privilege limits blast radius
- **Skill 8 (Tool Engineering)**: High-risk tools need approval workflows
