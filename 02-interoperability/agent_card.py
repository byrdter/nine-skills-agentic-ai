"""
Agent Card Implementation (A2A Protocol)

Demonstrates the Agent2Agent (A2A) protocol's Agent Card concept - a self-describing
document that allows agents to discover each other's capabilities.

This example shows:
- How to define an Agent Card with capabilities
- JSON-RPC task lifecycle (submitted -> working -> completed/failed)
- Agent discovery and capability matching

Reference: "Making AI Agents Talk to Each Other" video - Chapter 2
"""

import json
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime
import hashlib


class TaskStatus(Enum):
    """
    A2A Task Lifecycle States

    The A2A protocol defines explicit states for task tracking:
    - SUBMITTED: Task received, awaiting processing
    - WORKING: Agent is actively processing the task
    - COMPLETED: Task finished successfully
    - FAILED: Task encountered an error
    - CANCELLED: Task was cancelled before completion
    """
    SUBMITTED = "submitted"
    WORKING = "working"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class AgentSkill:
    """
    Represents a single capability that an agent can perform.

    The Agent Card declares skills with enough detail for other agents
    to understand WHAT the agent can do and HOW to invoke it.

    Key Principle: Skills should be specific enough to be useful,
    but general enough to be reusable across different contexts.
    """
    name: str                           # Unique skill identifier
    description: str                    # What this skill does
    input_schema: Dict[str, Any]        # JSON Schema for expected inputs
    output_schema: Dict[str, Any]       # JSON Schema for outputs

    # Optional metadata for discovery
    tags: List[str] = field(default_factory=list)
    examples: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class AgentCard:
    """
    The Agent Card - a self-describing document for A2A-compliant agents.

    Every A2A agent publishes an Agent Card at a well-known URL (e.g.,
    /.well-known/agent-card.json). Other agents read this card to:

    1. Verify the agent's identity
    2. Discover available capabilities (skills)
    3. Understand how to communicate with the agent
    4. Check protocol compatibility

    Key Principle: The Agent Card is like a "business card for AI agents" -
    it enables discovery without prior coordination.
    """
    # Identity
    agent_id: str                       # Unique identifier for this agent
    name: str                           # Human-readable name
    description: str                    # What this agent does

    # Communication
    service_endpoint: str               # URL for task submission
    protocol_version: str               # A2A protocol version (e.g., "1.0")

    # Capabilities
    skills: List[AgentSkill]            # What this agent can do

    # Optional metadata
    provider: str = ""                  # Organization providing this agent
    documentation_url: str = ""         # Link to detailed docs
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_json(self) -> str:
        """Serialize the Agent Card to JSON for publishing."""
        return json.dumps(asdict(self), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "AgentCard":
        """Parse an Agent Card from JSON."""
        data = json.loads(json_str)
        # Convert skill dicts back to AgentSkill objects
        data["skills"] = [AgentSkill(**s) for s in data["skills"]]
        return cls(**data)

    def find_skill(self, skill_name: str) -> Optional[AgentSkill]:
        """Find a skill by name."""
        for skill in self.skills:
            if skill.name == skill_name:
                return skill
        return None

    def matches_capability(self, query: str) -> List[AgentSkill]:
        """
        Find skills that might match a capability query.

        In production, this would use semantic search/embeddings.
        This simplified version uses keyword matching.
        """
        query_lower = query.lower()
        matches = []
        for skill in self.skills:
            # Check name, description, and tags
            if (query_lower in skill.name.lower() or
                query_lower in skill.description.lower() or
                any(query_lower in tag.lower() for tag in skill.tags)):
                matches.append(skill)
        return matches


@dataclass
class A2ATask:
    """
    Represents a task in the A2A protocol lifecycle.

    Tasks flow through explicit states, enabling:
    - Progress monitoring (polling, streaming, or webhooks)
    - Audit trails for compliance
    - Graceful error handling and retry logic
    """
    task_id: str
    skill_name: str
    input_data: Dict[str, Any]
    status: TaskStatus = TaskStatus.SUBMITTED
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def transition_to(self, new_status: TaskStatus,
                      result: Optional[Dict[str, Any]] = None,
                      error: Optional[str] = None) -> None:
        """
        Transition task to a new state.

        Key Principle: State transitions are explicit and logged,
        enabling debugging and audit trails.
        """
        # Validate transition (simplified - production would have full FSM)
        valid_transitions = {
            TaskStatus.SUBMITTED: [TaskStatus.WORKING, TaskStatus.CANCELLED],
            TaskStatus.WORKING: [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED],
        }

        if self.status in valid_transitions:
            if new_status not in valid_transitions[self.status]:
                raise ValueError(
                    f"Invalid transition from {self.status.value} to {new_status.value}"
                )

        self.status = new_status
        self.updated_at = datetime.utcnow().isoformat()

        if result:
            self.result = result
        if error:
            self.error = error


# =============================================================================
# Example: Compliance Agent Card
# =============================================================================

def create_compliance_agent_card() -> AgentCard:
    """
    Create an Agent Card for a Regulatory Compliance Agent.

    This example from the video shows how a financial firm's compliance
    agent might advertise its capabilities for other agents to discover.
    """
    return AgentCard(
        agent_id="compliance-agent-001",
        name="Regulatory Compliance Agent",
        description="Analyzes transactions and activities for regulatory compliance",
        service_endpoint="https://compliance.example.com/a2a/tasks",
        protocol_version="1.0",
        provider="Example Financial Corp",
        documentation_url="https://docs.example.com/compliance-agent",
        skills=[
            AgentSkill(
                name="check_trade_compliance",
                description=(
                    "Analyzes a proposed trade for regulatory compliance. "
                    "Checks against current SEC regulations, insider trading rules, "
                    "and firm-specific policies. Returns approval status with detailed "
                    "compliance report."
                ),
                input_schema={
                    "type": "object",
                    "properties": {
                        "trade_details": {
                            "type": "object",
                            "properties": {
                                "symbol": {"type": "string"},
                                "quantity": {"type": "number"},
                                "side": {"type": "string", "enum": ["buy", "sell"]},
                                "trader_id": {"type": "string"}
                            },
                            "required": ["symbol", "quantity", "side", "trader_id"]
                        }
                    },
                    "required": ["trade_details"]
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "approved": {"type": "boolean"},
                        "compliance_report": {"type": "string"},
                        "risk_flags": {"type": "array", "items": {"type": "string"}}
                    }
                },
                tags=["compliance", "trading", "regulatory", "SEC"],
                examples=[
                    {
                        "input": {
                            "trade_details": {
                                "symbol": "AAPL",
                                "quantity": 1000,
                                "side": "buy",
                                "trader_id": "trader-123"
                            }
                        },
                        "output": {
                            "approved": True,
                            "compliance_report": "Trade approved. No regulatory concerns identified.",
                            "risk_flags": []
                        }
                    }
                ]
            ),
            AgentSkill(
                name="generate_compliance_report",
                description=(
                    "Generates a comprehensive compliance report for a given time period. "
                    "Includes all reviewed transactions, flagged items, and regulatory status."
                ),
                input_schema={
                    "type": "object",
                    "properties": {
                        "start_date": {"type": "string", "format": "date"},
                        "end_date": {"type": "string", "format": "date"},
                        "report_type": {"type": "string", "enum": ["summary", "detailed"]}
                    },
                    "required": ["start_date", "end_date"]
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "report_id": {"type": "string"},
                        "report_url": {"type": "string"},
                        "summary": {"type": "string"}
                    }
                },
                tags=["compliance", "reporting", "audit"]
            )
        ]
    )


# =============================================================================
# Demonstration
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("Agent Card Demonstration (A2A Protocol)")
    print("=" * 70)

    # Create and publish an Agent Card
    print("\n[1] Creating Compliance Agent Card")
    print("-" * 50)
    compliance_agent = create_compliance_agent_card()
    print(f"Agent: {compliance_agent.name}")
    print(f"Endpoint: {compliance_agent.service_endpoint}")
    print(f"Skills available: {len(compliance_agent.skills)}")

    # Show the JSON representation (what would be published)
    print("\n[2] Agent Card JSON (published at well-known URL)")
    print("-" * 50)
    print(compliance_agent.to_json()[:500] + "...")

    # Demonstrate capability discovery
    print("\n[3] Capability Discovery")
    print("-" * 50)
    query = "trading compliance"
    matches = compliance_agent.matches_capability(query)
    print(f"Query: '{query}'")
    print(f"Matching skills: {[s.name for s in matches]}")

    # Demonstrate task lifecycle
    print("\n[4] Task Lifecycle (A2A Protocol)")
    print("-" * 50)

    # Create a task
    task = A2ATask(
        task_id="task-" + hashlib.md5(b"example").hexdigest()[:8],
        skill_name="check_trade_compliance",
        input_data={
            "trade_details": {
                "symbol": "AAPL",
                "quantity": 1000,
                "side": "buy",
                "trader_id": "trader-123"
            }
        }
    )
    print(f"Task created: {task.task_id}")
    print(f"Initial status: {task.status.value}")

    # Transition through states
    task.transition_to(TaskStatus.WORKING)
    print(f"After starting work: {task.status.value}")

    task.transition_to(
        TaskStatus.COMPLETED,
        result={
            "approved": True,
            "compliance_report": "Trade approved. No concerns.",
            "risk_flags": []
        }
    )
    print(f"After completion: {task.status.value}")
    print(f"Result: {task.result}")

    print("\n" + "=" * 70)
    print("Key Takeaways:")
    print("1. Agent Cards enable discovery without prior coordination")
    print("2. Skills define WHAT agents can do and HOW to invoke them")
    print("3. Explicit task states enable monitoring and debugging")
    print("4. The A2A protocol is managed by the Linux Foundation")
    print("=" * 70)
