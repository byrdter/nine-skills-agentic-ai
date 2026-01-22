"""
Distributed Tracing for Agentic Systems

Demonstrates OpenTelemetry-based tracing for multi-step agent workflows.
Traces show the complete journey of a request through all agent operations.

This example shows:
- Span creation for agent operations (LLM calls, tool use, retrieval)
- Trace context propagation across async operations
- Custom attributes for agentic-specific data (tokens, model, quality)
- Parent-child span relationships

Reference: "When AI Breaks: Observability for Agentic Systems" video - Chapter 2

Key Concept: A trace is a tree of spans representing the complete request lifecycle.
Each span has: name, duration, attributes, and parent reference.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
from contextlib import contextmanager
import uuid
import time


class SpanKind(Enum):
    """Types of spans in agentic systems."""
    AGENT = "agent"             # Top-level agent operation
    LLM = "llm"                 # LLM API call
    TOOL = "tool"               # Tool invocation
    RETRIEVAL = "retrieval"     # Memory/RAG retrieval
    GUARDRAIL = "guardrail"     # Safety check
    ORCHESTRATION = "orchestration"  # Workflow coordination


class SpanStatus(Enum):
    """Outcome status of a span."""
    OK = "ok"
    ERROR = "error"
    TIMEOUT = "timeout"


@dataclass
class Span:
    """
    Represents a single unit of work in a distributed trace.

    Key Principle: Every significant operation should be its own span.
    This enables:
    - Latency breakdown (where is time being spent?)
    - Error localization (which step failed?)
    - Cost attribution (which operations are expensive?)
    """
    trace_id: str               # Shared across all spans in the trace
    span_id: str                # Unique ID for this span
    parent_span_id: Optional[str] = None  # Parent span (if any)

    name: str = ""              # Human-readable operation name
    kind: SpanKind = SpanKind.AGENT

    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    duration_ms: float = 0.0

    status: SpanStatus = SpanStatus.OK
    error_message: str = ""

    # Agentic-specific attributes
    attributes: Dict[str, Any] = field(default_factory=dict)

    def end(self, status: SpanStatus = SpanStatus.OK, error: str = "") -> None:
        """Mark the span as complete."""
        self.end_time = datetime.now()
        self.duration_ms = (self.end_time - self.start_time).total_seconds() * 1000
        self.status = status
        if error:
            self.error_message = error


@dataclass
class Trace:
    """
    A complete trace containing all spans for a request.

    The trace represents the full journey of a user request through
    the agentic system - from initial receipt through all processing
    steps to final response.
    """
    trace_id: str
    spans: List[Span] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.now)

    def add_span(self, span: Span) -> None:
        """Add a span to this trace."""
        self.spans.append(span)

    def get_root_span(self) -> Optional[Span]:
        """Get the root span (no parent)."""
        for span in self.spans:
            if span.parent_span_id is None:
                return span
        return None

    def get_children(self, parent_span_id: str) -> List[Span]:
        """Get all child spans of a parent."""
        return [s for s in self.spans if s.parent_span_id == parent_span_id]

    def total_duration_ms(self) -> float:
        """Get total trace duration."""
        root = self.get_root_span()
        return root.duration_ms if root else 0.0

    def print_tree(self, span: Optional[Span] = None, indent: int = 0) -> None:
        """Print trace as a tree structure."""
        if span is None:
            span = self.get_root_span()
            if span is None:
                print("  (empty trace)")
                return

        prefix = "  " * indent
        status_icon = "✓" if span.status == SpanStatus.OK else "✗"

        print(f"{prefix}{status_icon} {span.name} ({span.duration_ms:.1f}ms) [{span.kind.value}]")

        # Print key attributes
        for key in ["model", "tokens", "tool_name", "quality_score"]:
            if key in span.attributes:
                print(f"{prefix}    {key}: {span.attributes[key]}")

        # Print children
        for child in self.get_children(span.span_id):
            self.print_tree(child, indent + 1)


class Tracer:
    """
    Creates and manages traces and spans.

    In production, this would use OpenTelemetry SDK:
    - opentelemetry-sdk
    - opentelemetry-api
    - opentelemetry-exporter-otlp

    Key Principle: The tracer maintains context across async boundaries,
    ensuring parent-child relationships are preserved.
    """

    def __init__(self, service_name: str = "agent-service"):
        self.service_name = service_name
        self._current_trace: Optional[Trace] = None
        self._span_stack: List[Span] = []

    def start_trace(self, name: str) -> Trace:
        """Start a new trace."""
        trace_id = str(uuid.uuid4())[:16]
        self._current_trace = Trace(trace_id=trace_id)

        # Create root span
        root_span = self._create_span(name, SpanKind.AGENT)
        self._current_trace.add_span(root_span)
        self._span_stack.append(root_span)

        return self._current_trace

    def _create_span(self, name: str, kind: SpanKind) -> Span:
        """Create a new span."""
        parent_id = self._span_stack[-1].span_id if self._span_stack else None

        return Span(
            trace_id=self._current_trace.trace_id if self._current_trace else "",
            span_id=str(uuid.uuid4())[:8],
            parent_span_id=parent_id,
            name=name,
            kind=kind
        )

    @contextmanager
    def span(self, name: str, kind: SpanKind = SpanKind.AGENT,
             attributes: Optional[Dict[str, Any]] = None):
        """
        Context manager for creating spans.

        Usage:
            with tracer.span("llm_call", SpanKind.LLM) as span:
                # do work
                span.attributes["model"] = "gpt-4"
        """
        span = self._create_span(name, kind)
        if attributes:
            span.attributes.update(attributes)

        if self._current_trace:
            self._current_trace.add_span(span)

        self._span_stack.append(span)

        try:
            yield span
        except Exception as e:
            span.end(SpanStatus.ERROR, str(e))
            raise
        finally:
            span.end()
            self._span_stack.pop()

    def end_trace(self) -> Optional[Trace]:
        """End the current trace."""
        if self._span_stack:
            self._span_stack[0].end()
            self._span_stack.clear()

        trace = self._current_trace
        self._current_trace = None
        return trace


# =============================================================================
# Agentic-Specific Span Attributes
# =============================================================================

@dataclass
class LLMSpanAttributes:
    """
    Attributes specific to LLM API calls.

    These follow the OpenTelemetry Semantic Conventions for Gen AI.
    """
    model: str = ""
    provider: str = ""          # openai, anthropic, etc.
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    temperature: float = 0.0
    max_tokens: int = 0
    finish_reason: str = ""     # stop, length, tool_use, etc.
    cached_tokens: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "llm.model": self.model,
            "llm.provider": self.provider,
            "llm.input_tokens": self.input_tokens,
            "llm.output_tokens": self.output_tokens,
            "llm.total_tokens": self.total_tokens,
            "llm.temperature": self.temperature,
            "llm.cached_tokens": self.cached_tokens,
            "llm.finish_reason": self.finish_reason,
        }


@dataclass
class ToolSpanAttributes:
    """Attributes specific to tool invocations."""
    tool_name: str = ""
    tool_input: str = ""
    tool_output: str = ""
    success: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool.name": self.tool_name,
            "tool.input": self.tool_input[:200],   # Truncate for safety
            "tool.output": self.tool_output[:200],
            "tool.success": self.success,
        }


@dataclass
class RetrievalSpanAttributes:
    """Attributes specific to retrieval/RAG operations."""
    query: str = ""
    num_results: int = 0
    top_score: float = 0.0
    index_name: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "retrieval.query": self.query[:200],
            "retrieval.num_results": self.num_results,
            "retrieval.top_score": self.top_score,
            "retrieval.index_name": self.index_name,
        }


# =============================================================================
# Example: Tracing an Agent Workflow
# =============================================================================

def simulate_agent_workflow(tracer: Tracer) -> Trace:
    """
    Simulate a multi-step agent workflow with tracing.

    This demonstrates how a customer service agent request
    would appear in a distributed trace.
    """
    # Start the trace
    trace = tracer.start_trace("customer_service_request")

    # Step 1: Input Guardrail
    with tracer.span("input_guardrail", SpanKind.GUARDRAIL) as span:
        time.sleep(0.01)  # Simulate work
        span.attributes["guardrail.passed"] = True
        span.attributes["guardrail.checks"] = ["prompt_injection", "pii_detection"]

    # Step 2: Memory Retrieval
    with tracer.span("memory_retrieval", SpanKind.RETRIEVAL) as span:
        time.sleep(0.05)  # Simulate retrieval
        attrs = RetrievalSpanAttributes(
            query="customer return policy",
            num_results=3,
            top_score=0.92,
            index_name="customer-service-kb"
        )
        span.attributes.update(attrs.to_dict())

    # Step 3: LLM Call
    with tracer.span("llm_generate_response", SpanKind.LLM) as span:
        time.sleep(0.15)  # Simulate LLM latency
        attrs = LLMSpanAttributes(
            model="claude-3-5-haiku",
            provider="anthropic",
            input_tokens=450,
            output_tokens=120,
            total_tokens=570,
            temperature=0.3,
            cached_tokens=300,
            finish_reason="stop"
        )
        span.attributes.update(attrs.to_dict())

        # Nested tool call within LLM span
        with tracer.span("tool_call", SpanKind.TOOL) as tool_span:
            time.sleep(0.03)
            tool_attrs = ToolSpanAttributes(
                tool_name="search_orders",
                tool_input='{"customer_id": "CUST-123"}',
                tool_output='{"orders": [...]}',
                success=True
            )
            tool_span.attributes.update(tool_attrs.to_dict())

    # Step 4: Output Guardrail
    with tracer.span("output_guardrail", SpanKind.GUARDRAIL) as span:
        time.sleep(0.02)
        span.attributes["guardrail.passed"] = True
        span.attributes["guardrail.pii_redacted"] = False

    # Step 5: Quality Evaluation (async, but shown inline for simplicity)
    with tracer.span("quality_evaluation", SpanKind.AGENT) as span:
        time.sleep(0.02)
        span.attributes["quality_score"] = 0.87
        span.attributes["groundedness"] = 0.95
        span.attributes["relevance"] = 0.82

    # End the trace
    return tracer.end_trace()


# =============================================================================
# Demonstration
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("Distributed Tracing Demonstration")
    print("=" * 70)

    # Create tracer
    tracer = Tracer(service_name="customer-service-agent")

    # Run simulated workflow with tracing
    print("\n[1] Simulating Agent Workflow with Tracing")
    print("-" * 50)

    trace = simulate_agent_workflow(tracer)

    # Display trace tree
    print("\n[2] Trace Tree View")
    print("-" * 50)
    trace.print_tree()

    # Summary statistics
    print("\n[3] Trace Summary")
    print("-" * 50)
    print(f"  Trace ID: {trace.trace_id}")
    print(f"  Total Duration: {trace.total_duration_ms():.1f}ms")
    print(f"  Span Count: {len(trace.spans)}")

    # Breakdown by span kind
    print("\n  Duration by Operation Type:")
    by_kind: Dict[str, float] = {}
    for span in trace.spans:
        kind = span.kind.value
        by_kind[kind] = by_kind.get(kind, 0) + span.duration_ms

    for kind, duration in sorted(by_kind.items(), key=lambda x: x[1], reverse=True):
        pct = duration / trace.total_duration_ms() * 100
        print(f"    {kind:15} {duration:>8.1f}ms ({pct:>5.1f}%)")

    # Token summary
    print("\n  Token Usage (from LLM spans):")
    for span in trace.spans:
        if span.kind == SpanKind.LLM:
            print(f"    Input:  {span.attributes.get('llm.input_tokens', 0)}")
            print(f"    Output: {span.attributes.get('llm.output_tokens', 0)}")
            print(f"    Cached: {span.attributes.get('llm.cached_tokens', 0)}")

    print("\n" + "=" * 70)
    print("Key Takeaways:")
    print("1. Every significant operation gets its own span")
    print("2. Parent-child relationships show the call hierarchy")
    print("3. Attributes capture agentic-specific data (tokens, models, quality)")
    print("4. Trace tree enables rapid debugging: WHERE did time go? WHAT failed?")
    print("=" * 70)
