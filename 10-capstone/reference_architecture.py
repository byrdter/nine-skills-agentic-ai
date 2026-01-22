"""
Reference Architecture: Production Agentic System

Demonstrates how all nine skills integrate into a complete,
production-ready agent system.

This example shows:
- Layered architecture (orchestration, data, security, operations)
- Integration points between skills
- Production deployment patterns
- Common failure modes and prevention

Reference: "From Zero to Production: Building a Complete Agentic System" video

Key Concept: Skills in isolation aren't systems. This capstone shows
how the skills combine into a coherent, production-grade architecture.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


# =============================================================================
# Architecture Layers
# =============================================================================

class ArchitectureLayer(Enum):
    """
    The four layers of the reference architecture.

    Each layer addresses different concerns and skills:
    - ORCHESTRATION: State management, workflow coordination
    - DATA: Memory, retrieval, governance
    - SECURITY: Identity, tools, guardrails
    - OPERATIONS: Observability, optimization
    """
    ORCHESTRATION = "orchestration"  # Skills 1, 2
    DATA = "data"                    # Skills 3, 6
    SECURITY = "security"            # Skills 7, 8, 9
    OPERATIONS = "operations"        # Skills 4, 5


@dataclass
class SkillMapping:
    """Maps skills to architecture layers."""
    skill_number: int
    skill_name: str
    layer: ArchitectureLayer
    components: List[str]


SKILL_MAPPINGS = [
    SkillMapping(1, "State Management", ArchitectureLayer.ORCHESTRATION,
                 ["Finite State Machine", "Checkpointing", "Event Sourcing"]),
    SkillMapping(2, "Interoperability", ArchitectureLayer.ORCHESTRATION,
                 ["A2A Protocol", "MCP Tools", "Adapter Pattern"]),
    SkillMapping(3, "Hybrid Memory", ArchitectureLayer.DATA,
                 ["Vector Store", "Knowledge Graph", "Hybrid Retrieval"]),
    SkillMapping(4, "Context Economics", ArchitectureLayer.OPERATIONS,
                 ["Prefix Caching", "Summarization", "Cost Tracking"]),
    SkillMapping(5, "Observability", ArchitectureLayer.OPERATIONS,
                 ["Distributed Tracing", "Quality Metrics", "Dashboards"]),
    SkillMapping(6, "Data Governance", ArchitectureLayer.DATA,
                 ["Validation", "Lineage", "Grounding"]),
    SkillMapping(7, "Non-Human Identity", ArchitectureLayer.SECURITY,
                 ["Service Principals", "Dynamic Credentials", "OPA Policies"]),
    SkillMapping(8, "Tool Engineering", ArchitectureLayer.SECURITY,
                 ["Tool Schemas", "Error Handling", "Progressive Disclosure"]),
    SkillMapping(9, "Agentic Security", ArchitectureLayer.SECURITY,
                 ["Guardrails", "Red Teaming", "Human-in-the-Loop"]),
]


# =============================================================================
# Reference Architecture Components
# =============================================================================

@dataclass
class RequestContext:
    """Context for a single agent request through the system."""
    request_id: str
    user_id: str
    session_id: str
    query: str
    timestamp: datetime = field(default_factory=datetime.now)

    # Tracking through layers
    layer_results: Dict[str, Any] = field(default_factory=dict)


class OrchestrationLayer:
    """
    LAYER 1: Orchestration
    Skills: State Management (1), Interoperability (2)

    Responsibilities:
    - Workflow coordination via FSM
    - State persistence and checkpointing
    - Inter-agent communication
    """

    def __init__(self):
        self.current_state = "INITIALIZED"
        self.checkpoints: Dict[str, Any] = {}

    def process(self, ctx: RequestContext) -> Dict[str, Any]:
        """Process request through orchestration layer."""
        # State machine transition
        self.current_state = "PROCESSING"

        # Checkpoint for fault tolerance
        self.checkpoints[ctx.request_id] = {
            "state": self.current_state,
            "timestamp": datetime.now()
        }

        return {
            "layer": "orchestration",
            "state": self.current_state,
            "checkpoint_saved": True,
            "skills_applied": ["state_management", "interoperability"]
        }


class DataLayer:
    """
    LAYER 2: Data
    Skills: Hybrid Memory (3), Data Governance (6)

    Responsibilities:
    - Context retrieval (vector + graph)
    - Data validation and quality
    - Grounding and citation
    """

    def process(self, ctx: RequestContext) -> Dict[str, Any]:
        """Process request through data layer."""
        # Simulate retrieval
        retrieved_context = f"Relevant context for: {ctx.query[:30]}..."

        # Data quality check
        freshness_check = "FRESH"
        grounding_score = 0.92

        return {
            "layer": "data",
            "context_retrieved": True,
            "retrieval_type": "hybrid (vector + graph)",
            "freshness": freshness_check,
            "grounding_score": grounding_score,
            "skills_applied": ["hybrid_memory", "data_governance"]
        }


class SecurityLayer:
    """
    LAYER 3: Security
    Skills: Non-Human Identity (7), Tool Engineering (8), Agentic Security (9)

    Responsibilities:
    - Agent authentication and authorization
    - Tool access control
    - Input/output guardrails
    """

    def process(self, ctx: RequestContext) -> Dict[str, Any]:
        """Process request through security layer."""
        # Input guardrail check
        input_safe = True

        # Authorization check
        authorized = True

        # Tool access determination
        available_tools = ["search_orders", "get_policy", "create_ticket"]

        return {
            "layer": "security",
            "input_guardrail_passed": input_safe,
            "authorized": authorized,
            "available_tools": available_tools,
            "human_approval_required": False,
            "skills_applied": ["non_human_identity", "tool_engineering", "agentic_security"]
        }


class OperationsLayer:
    """
    LAYER 4: Operations
    Skills: Context Economics (4), Observability (5)

    Responsibilities:
    - Cost tracking and optimization
    - Distributed tracing
    - Quality evaluation
    """

    def process(self, ctx: RequestContext, response: str) -> Dict[str, Any]:
        """Process through operations layer (post-response)."""
        # Simulate metrics
        tokens_used = 450
        latency_ms = 320
        quality_score = 0.87
        cost_usd = 0.0012

        return {
            "layer": "operations",
            "tokens_used": tokens_used,
            "latency_ms": latency_ms,
            "quality_score": quality_score,
            "cost_usd": cost_usd,
            "cache_hit": True,
            "skills_applied": ["context_economics", "observability"]
        }


class ReferenceArchitecture:
    """
    Complete reference architecture integrating all skills.

    This demonstrates the full request flow through all layers:
    1. Orchestration: Route and coordinate
    2. Data: Retrieve context
    3. Security: Validate and authorize
    4. LLM: Generate response
    5. Operations: Monitor and optimize
    """

    def __init__(self):
        self.orchestration = OrchestrationLayer()
        self.data = DataLayer()
        self.security = SecurityLayer()
        self.operations = OperationsLayer()

    def process_request(self, user_id: str, query: str) -> Dict[str, Any]:
        """
        Process a request through the complete architecture.

        This is the main entry point showing how all skills integrate.
        """
        import uuid

        # Create request context
        ctx = RequestContext(
            request_id=str(uuid.uuid4())[:8],
            user_id=user_id,
            session_id="sess-001",
            query=query
        )

        results = {
            "request_id": ctx.request_id,
            "query": query,
            "layers": {}
        }

        # Layer 1: Orchestration
        results["layers"]["orchestration"] = self.orchestration.process(ctx)

        # Layer 2: Data
        results["layers"]["data"] = self.data.process(ctx)

        # Layer 3: Security
        results["layers"]["security"] = self.security.process(ctx)

        # Check if we can proceed
        if not results["layers"]["security"]["input_guardrail_passed"]:
            return {**results, "status": "blocked", "reason": "Security guardrail"}

        # Simulate LLM response
        response = f"Based on our policy, items can be returned within 30 days. [Citation: Policy v2.3]"

        # Layer 4: Operations (post-response)
        results["layers"]["operations"] = self.operations.process(ctx, response)

        results["response"] = response
        results["status"] = "success"

        return results


# =============================================================================
# Production Deployment Patterns
# =============================================================================

@dataclass
class DeploymentChecklist:
    """Pre-production deployment checklist."""

    items: List[Dict[str, Any]] = field(default_factory=lambda: [
        {"category": "Orchestration", "item": "State machine defined and tested", "required": True},
        {"category": "Orchestration", "item": "Checkpointing implemented", "required": True},
        {"category": "Data", "item": "Data validation rules defined", "required": True},
        {"category": "Data", "item": "Freshness tracking enabled", "required": True},
        {"category": "Data", "item": "Strict grounding enforced", "required": True},
        {"category": "Security", "item": "Agent identities provisioned", "required": True},
        {"category": "Security", "item": "Least privilege enforced", "required": True},
        {"category": "Security", "item": "Input guardrails deployed", "required": True},
        {"category": "Security", "item": "Output guardrails deployed", "required": True},
        {"category": "Security", "item": "Red team testing completed", "required": True},
        {"category": "Operations", "item": "Distributed tracing enabled", "required": True},
        {"category": "Operations", "item": "Quality metrics defined", "required": True},
        {"category": "Operations", "item": "Cost alerting configured", "required": True},
        {"category": "Operations", "item": "Dashboards created", "required": False},
    ])


# =============================================================================
# Demonstration
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("Reference Architecture Demonstration")
    print("=" * 70)

    # Show skill mapping to layers
    print("\n[1] Skills Mapped to Architecture Layers")
    print("-" * 50)

    for layer in ArchitectureLayer:
        skills = [s for s in SKILL_MAPPINGS if s.layer == layer]
        print(f"\n  {layer.value.upper()} Layer:")
        for skill in skills:
            print(f"    Skill {skill.skill_number}: {skill.skill_name}")
            print(f"      Components: {', '.join(skill.components[:2])}...")

    # Process a sample request
    print("\n[2] Sample Request Through All Layers")
    print("-" * 50)

    arch = ReferenceArchitecture()
    result = arch.process_request("user-123", "What is your return policy?")

    print(f"\n  Request ID: {result['request_id']}")
    print(f"  Query: {result['query']}")
    print(f"  Status: {result['status']}")

    for layer_name, layer_result in result["layers"].items():
        print(f"\n  {layer_name.upper()} Layer:")
        for key, value in layer_result.items():
            if key != "layer" and key != "skills_applied":
                print(f"    {key}: {value}")
        print(f"    Skills: {', '.join(layer_result.get('skills_applied', []))}")

    if "response" in result:
        print(f"\n  Response: {result['response']}")

    # Show deployment checklist
    print("\n[3] Production Deployment Checklist")
    print("-" * 50)

    checklist = DeploymentChecklist()
    by_category = {}
    for item in checklist.items:
        cat = item["category"]
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(item)

    for category, items in by_category.items():
        print(f"\n  {category}:")
        for item in items:
            req = "[REQUIRED]" if item["required"] else "[optional]"
            print(f"    [ ] {item['item']} {req}")

    print("\n" + "=" * 70)
    print("Key Takeaways:")
    print("1. Four layers: Orchestration, Data, Security, Operations")
    print("2. Each skill maps to a specific layer")
    print("3. Request flows through all layers in sequence")
    print("4. Skills support each other - remove one and the system weakens")
    print("5. Checklist ensures nothing is forgotten before production")
    print("=" * 70)
