"""
Checkpointing for Fault-Tolerant Agent Workflows

Demonstrates state persistence for crash recovery.
If your agent crashes mid-workflow, resume from the last checkpoint - don't restart.
"""

import json
import sqlite3
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Optional
from pathlib import Path


@dataclass
class WorkflowState:
    """Serializable workflow state."""
    workflow_id: str
    current_step: str
    data: dict
    created_at: str
    updated_at: str
    completed: bool = False


class CheckpointStore:
    """
    SQLite-based checkpoint store.

    In production, you might use:
    - Redis for speed
    - PostgreSQL for durability
    - S3 for large states
    """

    def __init__(self, db_path: str = "checkpoints.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize the checkpoint table."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS checkpoints (
                workflow_id TEXT PRIMARY KEY,
                current_step TEXT,
                data TEXT,
                created_at TEXT,
                updated_at TEXT,
                completed INTEGER DEFAULT 0
            )
        """)
        conn.commit()
        conn.close()

    def save(self, state: WorkflowState):
        """Save checkpoint."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT OR REPLACE INTO checkpoints
            (workflow_id, current_step, data, created_at, updated_at, completed)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            state.workflow_id,
            state.current_step,
            json.dumps(state.data),
            state.created_at,
            state.updated_at,
            1 if state.completed else 0
        ))
        conn.commit()
        conn.close()
        print(f"  [Checkpoint] Saved at step: {state.current_step}")

    def load(self, workflow_id: str) -> Optional[WorkflowState]:
        """Load checkpoint if exists."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            "SELECT * FROM checkpoints WHERE workflow_id = ?",
            (workflow_id,)
        )
        row = cursor.fetchone()
        conn.close()

        if row:
            return WorkflowState(
                workflow_id=row[0],
                current_step=row[1],
                data=json.loads(row[2]),
                created_at=row[3],
                updated_at=row[4],
                completed=bool(row[5])
            )
        return None

    def delete(self, workflow_id: str):
        """Delete checkpoint after successful completion."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("DELETE FROM checkpoints WHERE workflow_id = ?", (workflow_id,))
        conn.commit()
        conn.close()


class CheckpointedWorkflow:
    """
    Workflow with automatic checkpointing.

    Key pattern:
    1. Check for existing checkpoint on start
    2. Resume from checkpoint if found
    3. Save checkpoint after each step
    4. Clean up checkpoint on completion
    """

    STEPS = ["extract", "transform", "validate", "enrich", "complete"]

    def __init__(self, workflow_id: str, store: CheckpointStore):
        self.workflow_id = workflow_id
        self.store = store
        self.state: Optional[WorkflowState] = None

    def _get_step_index(self, step: str) -> int:
        """Get index of step in workflow."""
        return self.STEPS.index(step) if step in self.STEPS else 0

    def start_or_resume(self, initial_data: dict) -> WorkflowState:
        """
        Start new workflow or resume from checkpoint.

        This is the key pattern for fault tolerance.
        """
        # Check for existing checkpoint
        existing = self.store.load(self.workflow_id)

        if existing and not existing.completed:
            print(f"Resuming workflow from step: {existing.current_step}")
            self.state = existing
        else:
            print(f"Starting new workflow: {self.workflow_id}")
            self.state = WorkflowState(
                workflow_id=self.workflow_id,
                current_step=self.STEPS[0],
                data=initial_data,
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            )
            self.store.save(self.state)

        return self.state

    def advance(self, step_result: dict):
        """
        Complete current step and advance to next.

        Always checkpoint after advancing.
        """
        current_index = self._get_step_index(self.state.current_step)

        # Merge step result into state data
        self.state.data.update(step_result)
        self.state.updated_at = datetime.now().isoformat()

        # Advance to next step
        if current_index < len(self.STEPS) - 1:
            self.state.current_step = self.STEPS[current_index + 1]
        else:
            self.state.completed = True

        # Checkpoint!
        self.store.save(self.state)

    def is_complete(self) -> bool:
        """Check if workflow is complete."""
        return self.state.completed


def simulate_step(step: str, data: dict, fail_at: Optional[str] = None) -> dict:
    """
    Simulate a workflow step.

    Set fail_at to simulate a crash at a specific step.
    """
    if step == fail_at:
        raise RuntimeError(f"Simulated crash at step: {step}")

    print(f"  Executing step: {step}")

    # Simulate step-specific processing
    if step == "extract":
        return {"extracted_fields": ["title", "date", "amount"]}
    elif step == "transform":
        return {"transformed": True, "format": "normalized"}
    elif step == "validate":
        return {"valid": True, "errors": []}
    elif step == "enrich":
        return {"enriched": True, "external_data": {"category": "invoice"}}
    elif step == "complete":
        return {"status": "completed"}

    return {}


def run_workflow(workflow_id: str, data: dict, fail_at: Optional[str] = None):
    """
    Run workflow with checkpointing.

    Try running with fail_at="validate", then run again without it.
    You'll see it resume from the checkpoint!
    """
    store = CheckpointStore()
    workflow = CheckpointedWorkflow(workflow_id, store)

    # Start or resume
    state = workflow.start_or_resume(data)

    # Process remaining steps
    while not workflow.is_complete():
        try:
            result = simulate_step(state.current_step, state.data, fail_at)
            workflow.advance(result)
        except RuntimeError as e:
            print(f"\n  CRASH: {e}")
            print("  State saved at checkpoint. Run again to resume.")
            return

    print(f"\nWorkflow completed!")
    print(f"Final data: {json.dumps(state.data, indent=2)}")

    # Clean up checkpoint
    store.delete(workflow_id)
    print("Checkpoint cleaned up.")


if __name__ == "__main__":
    # Clean up any previous test data
    Path("checkpoints.db").unlink(missing_ok=True)

    print("=" * 60)
    print("Example 1: Workflow that crashes at 'validate' step")
    print("=" * 60)
    run_workflow(
        workflow_id="doc-001",
        data={"document": "invoice.pdf"},
        fail_at="validate"  # Simulate crash
    )

    print("\n" + "=" * 60)
    print("Example 2: Resume the same workflow (no crash this time)")
    print("=" * 60)
    run_workflow(
        workflow_id="doc-001",  # Same ID - will resume!
        data={"document": "invoice.pdf"},
        fail_at=None  # No crash
    )

    print("\n" + "=" * 60)
    print("Example 3: Fresh workflow (different ID)")
    print("=" * 60)
    run_workflow(
        workflow_id="doc-002",
        data={"document": "contract.pdf"},
        fail_at=None
    )
