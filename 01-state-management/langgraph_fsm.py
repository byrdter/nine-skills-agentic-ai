"""
LangGraph State Machine Example

Using LangGraph's StateGraph for production agent orchestration.
This shows how the FSM concepts translate to a real framework.

Requires: pip install langgraph langchain langchain-openai
"""

from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END


# Define the state schema
class AgentState(TypedDict):
    """State passed between nodes in the graph."""
    document: str
    extracted_data: dict | None
    validation_result: bool | None
    enriched_data: dict | None
    final_result: str | None
    error: str | None
    retry_count: int


# Define node functions (each represents a state/action)

def extract_node(state: AgentState) -> AgentState:
    """Extract information from document."""
    print("  [Extract] Processing document...")

    # Simulate extraction (in real code, call an LLM here)
    if "error" in state["document"].lower():
        return {**state, "error": "Extraction failed"}

    extracted = {
        "title": "Sample Document",
        "date": "2024-01-15",
        "amount": 1500.00
    }
    return {**state, "extracted_data": extracted, "error": None}


def validate_node(state: AgentState) -> AgentState:
    """Validate extracted data."""
    print("  [Validate] Checking extracted data...")

    if state["extracted_data"] is None:
        return {**state, "validation_result": False, "error": "No data to validate"}

    # Simulate validation
    is_valid = state["extracted_data"].get("amount", 0) > 0
    return {**state, "validation_result": is_valid}


def enrich_node(state: AgentState) -> AgentState:
    """Enrich data with external information."""
    print("  [Enrich] Adding external data...")

    enriched = {
        **state["extracted_data"],
        "category": "invoice",
        "priority": "normal",
        "processed_at": "2024-01-15T10:30:00Z"
    }
    return {**state, "enriched_data": enriched}


def complete_node(state: AgentState) -> AgentState:
    """Mark workflow as complete."""
    print("  [Complete] Finalizing...")
    return {**state, "final_result": "success"}


def error_node(state: AgentState) -> AgentState:
    """Handle errors."""
    print(f"  [Error] Handling error: {state.get('error', 'Unknown')}")
    retry_count = state.get("retry_count", 0) + 1
    return {**state, "retry_count": retry_count}


# Define routing functions (determine transitions)

def route_after_extract(state: AgentState) -> Literal["validate", "error"]:
    """Route based on extraction result."""
    if state.get("error"):
        return "error"
    return "validate"


def route_after_validate(state: AgentState) -> Literal["enrich", "error"]:
    """Route based on validation result."""
    if not state.get("validation_result"):
        return "error"
    return "enrich"


def route_after_error(state: AgentState) -> Literal["extract", "end"]:
    """Decide whether to retry or give up."""
    if state.get("retry_count", 0) < 3:
        print(f"  [Retry] Attempt {state['retry_count']}/3")
        return "extract"
    print("  [Give Up] Max retries exceeded")
    return "end"


def build_workflow() -> StateGraph:
    """
    Build the LangGraph workflow.

    This is equivalent to the FSM we built manually,
    but with LangGraph handling the orchestration.
    """
    # Create the graph
    workflow = StateGraph(AgentState)

    # Add nodes (states)
    workflow.add_node("extract", extract_node)
    workflow.add_node("validate", validate_node)
    workflow.add_node("enrich", enrich_node)
    workflow.add_node("complete", complete_node)
    workflow.add_node("error", error_node)

    # Set entry point
    workflow.set_entry_point("extract")

    # Add edges (transitions)
    workflow.add_conditional_edges(
        "extract",
        route_after_extract,
        {"validate": "validate", "error": "error"}
    )

    workflow.add_conditional_edges(
        "validate",
        route_after_validate,
        {"enrich": "enrich", "error": "error"}
    )

    workflow.add_edge("enrich", "complete")
    workflow.add_edge("complete", END)

    workflow.add_conditional_edges(
        "error",
        route_after_error,
        {"extract": "extract", "end": END}
    )

    return workflow


def run_example(document: str):
    """Run the workflow with a document."""
    print(f"\nProcessing: {document}")
    print("-" * 40)

    # Build and compile the workflow
    workflow = build_workflow()
    app = workflow.compile()

    # Initial state
    initial_state: AgentState = {
        "document": document,
        "extracted_data": None,
        "validation_result": None,
        "enriched_data": None,
        "final_result": None,
        "error": None,
        "retry_count": 0
    }

    # Run the workflow
    final_state = app.invoke(initial_state)

    print("-" * 40)
    print(f"Result: {final_state.get('final_result', 'failed')}")
    if final_state.get("enriched_data"):
        print(f"Data: {final_state['enriched_data']}")

    return final_state


if __name__ == "__main__":
    print("=" * 60)
    print("LangGraph FSM Example")
    print("=" * 60)

    # Example 1: Successful workflow
    print("\n[Test 1] Valid document")
    run_example("invoice_2024_001.pdf")

    # Example 2: Document that triggers error and retry
    print("\n[Test 2] Document with error (will retry)")
    run_example("error_document.pdf")

    print("\n" + "=" * 60)
    print("Key Takeaway: Same FSM concepts, production-ready framework")
    print("=" * 60)
