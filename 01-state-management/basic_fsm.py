"""
Basic Finite State Machine for Agent Workflows

Demonstrates explicit states and transitions for predictable agent behavior.
This is the foundational pattern - understand this before moving to frameworks.
"""

from enum import Enum
from typing import Optional, Callable
from dataclasses import dataclass
from datetime import datetime


class State(Enum):
    """Explicit states for document processing workflow."""
    RECEIVED = "received"
    PROCESSING = "processing"
    VALIDATED = "validated"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRY = "retry"


@dataclass
class WorkflowContext:
    """Context passed through the workflow."""
    document_id: str
    content: Optional[str] = None
    validation_result: Optional[bool] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3


class StateMachine:
    """
    Simple FSM implementation.

    Key principles:
    - States are explicit (no hidden states)
    - Transitions are defined (no unexpected jumps)
    - Every transition is logged (auditability)
    """

    # Define valid transitions: current_state -> [allowed_next_states]
    TRANSITIONS = {
        State.RECEIVED: [State.PROCESSING],
        State.PROCESSING: [State.VALIDATED, State.FAILED],
        State.VALIDATED: [State.COMPLETED, State.FAILED],
        State.FAILED: [State.RETRY],
        State.RETRY: [State.PROCESSING],
        State.COMPLETED: [],  # Terminal state
    }

    def __init__(self, context: WorkflowContext):
        self.context = context
        self.state = State.RECEIVED
        self.history: list[tuple[datetime, State, State]] = []

    def can_transition(self, to_state: State) -> bool:
        """Check if transition is valid."""
        return to_state in self.TRANSITIONS.get(self.state, [])

    def transition(self, to_state: State) -> bool:
        """
        Attempt state transition.

        Returns True if successful, False if invalid transition.
        """
        if not self.can_transition(to_state):
            print(f"Invalid transition: {self.state.value} -> {to_state.value}")
            return False

        # Log the transition (audit trail)
        self.history.append((datetime.now(), self.state, to_state))

        from_state = self.state
        self.state = to_state
        print(f"Transition: {from_state.value} -> {to_state.value}")

        return True

    def is_terminal(self) -> bool:
        """Check if we've reached a terminal state."""
        return self.state == State.COMPLETED or (
            self.state == State.FAILED and
            self.context.retry_count >= self.context.max_retries
        )


def process_document(content: str) -> tuple[bool, Optional[str]]:
    """Simulate document processing. Returns (success, error_message)."""
    # Simulate processing logic
    if "error" in content.lower():
        return False, "Processing failed: invalid content"
    return True, None


def validate_document(content: str) -> bool:
    """Simulate document validation."""
    return len(content) > 10


def run_workflow(document_id: str, content: str) -> str:
    """
    Run the document processing workflow.

    This demonstrates the FSM pattern in action:
    1. Explicit states prevent confusion
    2. Invalid transitions are caught
    3. Retry logic is part of the state machine
    4. Complete history for debugging
    """
    context = WorkflowContext(document_id=document_id, content=content)
    fsm = StateMachine(context)

    print(f"\nStarting workflow for document: {document_id}")
    print(f"Initial state: {fsm.state.value}")

    while not fsm.is_terminal():

        if fsm.state == State.RECEIVED:
            fsm.transition(State.PROCESSING)

        elif fsm.state == State.PROCESSING:
            success, error = process_document(context.content)
            if success:
                context.validation_result = validate_document(context.content)
                fsm.transition(State.VALIDATED)
            else:
                context.error_message = error
                fsm.transition(State.FAILED)

        elif fsm.state == State.VALIDATED:
            if context.validation_result:
                fsm.transition(State.COMPLETED)
            else:
                context.error_message = "Validation failed"
                fsm.transition(State.FAILED)

        elif fsm.state == State.FAILED:
            if context.retry_count < context.max_retries:
                context.retry_count += 1
                print(f"Retry attempt {context.retry_count}/{context.max_retries}")
                fsm.transition(State.RETRY)
            else:
                print("Max retries exceeded")
                break

        elif fsm.state == State.RETRY:
            fsm.transition(State.PROCESSING)

    print(f"\nFinal state: {fsm.state.value}")
    print(f"Transitions: {len(fsm.history)}")

    return fsm.state.value


if __name__ == "__main__":
    # Example 1: Successful workflow
    print("=" * 50)
    print("Example 1: Successful document")
    result = run_workflow("doc-001", "This is a valid document with enough content.")

    # Example 2: Failed workflow (will retry)
    print("\n" + "=" * 50)
    print("Example 2: Document with error (triggers retry)")
    result = run_workflow("doc-002", "error")

    # Example 3: Failed validation
    print("\n" + "=" * 50)
    print("Example 3: Too short (validation fails)")
    result = run_workflow("doc-003", "short")
