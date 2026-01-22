# Skill 2: Interoperability and Integration Engineering

Making heterogeneous AI systems work together through universal protocols and adapter patterns.

## Video Reference

Watch the full explanation: [Making AI Agents Talk to Each Other: A2A, MCP, and the Integration Challenge](https://youtube.com/@your-channel)

## Key Concepts

- **Agent2Agent (A2A) Protocol**: Linux Foundation standard for agent-to-agent communication, discovery, and task delegation
- **Model Context Protocol (MCP)**: Anthropic's standard for LLMs to access external tools and data
- **Adapter Pattern**: Wrapping legacy APIs with agent-friendly interfaces
- **Defense in Depth**: Security at every boundary with capability-based access control

## Examples

### 1. Agent Card (`agent_card.py`)

Demonstrates the A2A protocol's self-describing Agent Card:

- Define agent capabilities (skills) with JSON Schema
- Task lifecycle management (submitted -> working -> completed/failed)
- Capability discovery and matching

```python
# Key pattern: Agent Cards enable discovery without prior coordination
compliance_agent = AgentCard(
    agent_id="compliance-agent-001",
    name="Regulatory Compliance Agent",
    skills=[
        AgentSkill(
            name="check_trade_compliance",
            description="Analyzes trades for regulatory compliance...",
            input_schema={...},
            output_schema={...}
        )
    ]
)
```

### 2. MCP Tools (`mcp_tools.py`)

Demonstrates the Model Context Protocol for exposing tools to LLMs:

- Tool definitions with complete schemas
- Resource access patterns
- "Golden Skills" - curated, role-appropriate tool sets
- Security considerations for enterprise data

```python
# Key pattern: Golden Skills = carefully scoped tool sets
class CustomerServiceMCPServer(MCPServer):
    """
    What's included: search_customer, get_order_status, create_ticket
    What's NOT included: database deletion, payment processing, admin
    """
```

### 3. Adapter Pattern (`adapter_pattern.py`)

Demonstrates legacy system integration patterns:

- SOAP/XML to REST/JSON translation
- Safe database access (read through views, write through queues)
- Resiliency patterns (retry, circuit breaker)
- Message queue integration

```python
# Key pattern: Isolate protocol translation from business logic
class ERPSoapAdapter(LegacySystemAdapter):
    def translate_request(self, json_request) -> soap_envelope:
        """Agent sends JSON, adapter converts to SOAP."""

    def translate_response(self, soap_response) -> json_dict:
        """Legacy returns XML, adapter converts to JSON."""
```

## Running the Examples

```bash
# Install dependencies
pip install -r requirements.txt

# Run Agent Card demonstration
python agent_card.py

# Run MCP Tools demonstration
python mcp_tools.py

# Run Adapter Pattern demonstration
python adapter_pattern.py
```

## Architecture Patterns

| Pattern | When to Use | Key Benefit |
|---------|------------|-------------|
| A2A Protocol | Agent-to-agent communication | Standard discovery, task lifecycle |
| MCP | LLM access to tools/data | Secure capability exposure |
| Adapter | Legacy system integration | Protocol isolation |
| Circuit Breaker | Unreliable dependencies | Prevent cascading failures |
| Command Queue | Database writes | Validation before execution |

## Key Takeaways

1. **Protocols will change, principles endure**: Loose coupling, canonical data models, and adapter patterns transfer across any technology
2. **Security at every boundary**: Capability-based access control limits blast radius when compromises occur
3. **Agents should never directly write to production databases**: Use command queues with separate validation processes
4. **The Adapter Pattern isolates complexity**: Legacy systems don't know they're talking to AI; agents don't know they're talking to legacy

## Connection to Other Skills

- **Skill 1 (State Management)**: A2A task states map to FSM patterns
- **Skill 5 (Observability)**: Trace every integration point
- **Skill 7 (Non-Human Identity)**: Each agent needs unique credentials for cross-boundary communication
- **Skill 8 (Tool Engineering)**: MCP tools require proper semantic descriptions
