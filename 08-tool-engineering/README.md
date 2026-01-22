# Skill 8: Tool Engineering

Designing the agent's user interface - clear schemas, semantic descriptions, and error handling that enables self-correction.

## Video Reference

Watch the full explanation: [Golden Tools vs. Dangerous APIs: Engineering the Capabilities Your Agents Can Use](https://youtube.com/@your-channel)

## Key Concepts

- **The Four Questions**: Every tool description should answer: What, When, How (inputs), What Returns
- **Semantic Altitude**: Finding the right level of abstraction (not too specific, not too general)
- **Structured Errors**: Error responses that enable agent self-correction
- **Progressive Disclosure**: Loading full tool docs only when needed

## Examples

### 1. Tool Schemas (`tool_schemas.py`)

Demonstrates effective tool definition design:

- The Four Questions framework for descriptions
- Semantic altitude analysis
- Examples for few-shot learning
- Limitations documentation

```python
# Key pattern: Answer FOUR questions in every tool description
tool = ToolDefinition(
    name="get_weather",
    description=(
        "WHAT: Retrieves current weather conditions...\n"
        "WHEN: Use when user asks about weather, NOT forecasts...\n"
        "INPUT: Location as city name or city,country...\n"
        "OUTPUT: JSON with temperature, conditions, humidity..."
    ),
    examples=[...]  # Few-shot learning
)
```

### 2. Error Handling (`error_handling.py`)

Demonstrates structured error responses:

- Error categories for programmatic handling
- Actionable suggestions for self-correction
- Recovery action guidance
- Expected format documentation

```python
# Key pattern: Include HOW to fix, not just WHAT went wrong
error = StructuredError(
    error_code="MISSING_PARAMETER",
    message="Required parameter 'order_id' is missing",
    suggestion="Please provide the 'order_id' as a string (ORD-XXXXX format)",
    recovery_action=RecoveryAction.MODIFY_INPUT,
    expected_format="ORD-XXXXX"
)
```

## Running the Examples

```bash
# Install dependencies
pip install -r requirements.txt

# Run Tool Schemas demonstration
python tool_schemas.py

# Run Error Handling demonstration
python error_handling.py
```

## The Four Questions

| Question | Purpose | Example |
|----------|---------|---------|
| WHAT does it do? | Core functionality | "Retrieves current weather" |
| WHEN to use it? | Selection criteria | "When user asks about weather, NOT forecasts" |
| WHAT are inputs? | Parameters and format | "location: city name or city,country" |
| WHAT returns? | Output structure | "JSON: temperature, conditions, humidity" |

## Semantic Altitude Scale

| Level | Problem | Example |
|-------|---------|---------|
| TOO LOW | Inflexible | "Get weather in SF in Fahrenheit" |
| OPTIMAL | Balanced | "Get weather for any location in units" |
| TOO HIGH | Useless | "Get information about something" |

## Error Recovery Actions

| Category | Recovery Action | Agent Behavior |
|----------|----------------|----------------|
| Validation | Modify Input | Fix parameter and retry |
| Not Found | Modify Input | Search for valid options |
| Rate Limit | Wait | Retry after delay |
| Permission | Escalate | Ask human for help |
| Timeout | Retry | Simplify request and retry |

## Key Takeaways

1. **Tools are the agent's UI**: Poor descriptions cause mistakes at machine speed
2. **Answer all four questions**: Most tools only answer "what" - that's not enough
3. **Examples accelerate learning**: Few-shot examples reduce trial-and-error
4. **Structured errors enable self-correction**: Include how to fix, not just what failed
5. **Test with actual agents**: Usability issues that humans miss often trip up agents

## Connection to Other Skills

- **Skill 2 (Interoperability)**: MCP tools follow these design principles
- **Skill 4 (Context Economics)**: Tool descriptions consume context budget
- **Skill 5 (Observability)**: Trace tool selection and execution
- **Skill 9 (Agentic Security)**: High-risk tools need approval workflows
