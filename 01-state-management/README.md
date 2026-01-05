# Skill 1: State Management

Patterns for managing agent state, workflow orchestration, and fault tolerance.

## Video Reference

This code accompanies **Video 1: State Management** in the Nine Essential Skills series.
[Watch the Video](link)

## Key Concepts

- **Finite State Machines (FSMs)**: Explicit states and transitions for predictable behavior
- **Checkpointing**: Persist state for fault tolerance and recovery
- **Event Sourcing**: Immutable event logs for auditability and replay

## Examples

### 1. Basic Finite State Machine (`basic_fsm.py`)

A simple FSM implementation showing explicit states and transitions for a document processing workflow.

```
States: RECEIVED → PROCESSING → VALIDATED → COMPLETED
                      ↓
                   FAILED → RETRY
```

### 2. LangGraph State Machine (`langgraph_fsm.py`)

Using LangGraph's StateGraph for agent orchestration with built-in state management.

### 3. Checkpointing (`checkpointing.py`)

Demonstrates state persistence for crash recovery:
- Save state at each transition
- Resume from last checkpoint after failure
- SQLite-based checkpoint store

### 4. Event Sourcing (`event_sourcing.py`)

Immutable event log pattern:
- All state changes recorded as events
- State reconstruction from event replay
- Complete audit trail

## Running the Examples

```bash
# Install dependencies
pip install -r requirements.txt

# Run basic FSM example
python basic_fsm.py

# Run LangGraph example
python langgraph_fsm.py

# Run checkpointing example
python checkpointing.py

# Run event sourcing example
python event_sourcing.py
```

## When to Use What

| Pattern | Use When |
|---------|----------|
| Basic FSM | Simple workflows, learning the concept |
| LangGraph | Production agent orchestration |
| Checkpointing | Long-running tasks, crash recovery needed |
| Event Sourcing | Audit requirements, debugging complex flows |

## Key Takeaways

1. **Explicit states prevent infinite loops** - Know exactly where your agent is
2. **Checkpoints enable recovery** - Resume, don't restart
3. **Events enable debugging** - Replay and understand what happened
4. **State machines are predictable** - No surprises in production
