"""
Adapter Pattern for Legacy System Integration

Demonstrates how to wrap legacy APIs with agent-friendly interfaces.
This is essential for integrating modern AI agents with existing
enterprise systems that may be decades old.

This example shows:
- The Adapter Pattern for protocol translation
- Wrapping SOAP/XML services with REST/JSON interfaces
- Implementing resiliency patterns (retry, circuit breaker)
- Safe database access patterns (read-only views, command queues)

Reference: "Making AI Agents Talk to Each Other" video - Chapter 4

Key Principle: The legacy system thinks it's talking to a normal client.
The agent thinks it's talking to a modern API.
"""

import json
import time
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Callable, List
from enum import Enum
from abc import ABC, abstractmethod
from functools import wraps
import random


# =============================================================================
# Resiliency Patterns
# =============================================================================

class CircuitState(Enum):
    """
    Circuit Breaker States

    The circuit breaker pattern prevents cascading failures:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Too many failures, requests are rejected immediately
    - HALF_OPEN: Testing if service has recovered
    """
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreaker:
    """
    Circuit Breaker for resilient legacy system integration.

    Key Principle: Don't keep hammering a failing service.
    Fail fast and give it time to recover.
    """
    failure_threshold: int = 5          # Failures before opening
    recovery_timeout: float = 30.0      # Seconds before trying again
    half_open_max_calls: int = 3        # Test calls in half-open state

    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    last_failure_time: float = 0
    half_open_calls: int = 0

    def can_execute(self) -> bool:
        """Check if a request should be allowed."""
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                self.half_open_calls = 0
                return True
            return False

        if self.state == CircuitState.HALF_OPEN:
            return self.half_open_calls < self.half_open_max_calls

        return False

    def record_success(self) -> None:
        """Record a successful call."""
        if self.state == CircuitState.HALF_OPEN:
            self.half_open_calls += 1
            if self.half_open_calls >= self.half_open_max_calls:
                # Service recovered, close the circuit
                self.state = CircuitState.CLOSED
                self.failure_count = 0

    def record_failure(self) -> None:
        """Record a failed call."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.state == CircuitState.HALF_OPEN:
            # Failed during recovery test, reopen
            self.state = CircuitState.OPEN
        elif self.failure_count >= self.failure_threshold:
            # Too many failures, open the circuit
            self.state = CircuitState.OPEN


def with_retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """
    Retry decorator with exponential backoff.

    Key Principle: Legacy systems may have transient failures.
    Automatic retry handles many issues without human intervention.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        time.sleep(current_delay)
                        current_delay *= backoff

            raise last_exception
        return wrapper
    return decorator


# =============================================================================
# Legacy System Adapter Base Class
# =============================================================================

class LegacySystemAdapter(ABC):
    """
    Base class for legacy system adapters.

    Adapters translate between:
    - Modern JSON/REST interfaces (what agents expect)
    - Legacy protocols (SOAP, XML-RPC, proprietary formats)

    Key Principle: Isolate protocol-specific code from business logic.
    """

    def __init__(self, name: str):
        self.name = name
        self.circuit_breaker = CircuitBreaker()

    @abstractmethod
    def translate_request(self, agent_request: Dict[str, Any]) -> Any:
        """Convert agent request to legacy format."""
        pass

    @abstractmethod
    def translate_response(self, legacy_response: Any) -> Dict[str, Any]:
        """Convert legacy response to agent-friendly JSON."""
        pass

    @abstractmethod
    def call_legacy_system(self, legacy_request: Any) -> Any:
        """Make the actual call to the legacy system."""
        pass

    def execute(self, agent_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a request through the adapter.

        This method handles:
        1. Circuit breaker check
        2. Request translation
        3. Legacy system call
        4. Response translation
        5. Error handling
        """
        # Check circuit breaker
        if not self.circuit_breaker.can_execute():
            return {
                "error": "Service temporarily unavailable",
                "details": "Circuit breaker is open - too many recent failures"
            }

        try:
            # Translate request
            legacy_request = self.translate_request(agent_request)

            # Call legacy system (with retry)
            legacy_response = self._call_with_retry(legacy_request)

            # Translate response
            result = self.translate_response(legacy_response)

            # Record success
            self.circuit_breaker.record_success()

            return result

        except Exception as e:
            self.circuit_breaker.record_failure()
            return {
                "error": "Legacy system call failed",
                "details": str(e)
            }

    @with_retry(max_attempts=3, delay=0.5)
    def _call_with_retry(self, legacy_request: Any) -> Any:
        """Call legacy system with automatic retry."""
        return self.call_legacy_system(legacy_request)


# =============================================================================
# Example: SOAP to REST Adapter (ERP System)
# =============================================================================

class ERPSoapAdapter(LegacySystemAdapter):
    """
    Adapter for a legacy SOAP-based ERP system.

    Scenario from the video: A 20-year-old SAP installation that
    returns XML. The adapter makes it look like a modern REST API.

    What the legacy system sees: Normal SOAP client
    What the agent sees: Modern JSON API
    """

    def __init__(self):
        super().__init__("legacy-erp-soap")

        # Simulated legacy data
        self._inventory = {
            "SKU-001": {"name": "Widget Pro", "quantity": 150, "warehouse": "WH-A"},
            "SKU-002": {"name": "Gadget Plus", "quantity": 75, "warehouse": "WH-B"},
        }

    def translate_request(self, agent_request: Dict[str, Any]) -> str:
        """
        Convert JSON request to SOAP/XML envelope.

        Agent sends: {"action": "get_inventory", "sku": "SKU-001"}
        Legacy needs: <soap:Envelope>...</soap:Envelope>
        """
        action = agent_request.get("action")
        sku = agent_request.get("sku", "")

        # Build SOAP envelope (simplified)
        soap_envelope = f"""<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <{action} xmlns="http://erp.example.com/inventory">
      <sku>{sku}</sku>
    </{action}>
  </soap:Body>
</soap:Envelope>"""

        return soap_envelope

    def translate_response(self, legacy_response: str) -> Dict[str, Any]:
        """
        Convert SOAP/XML response to JSON.

        Legacy returns: <InventoryResponse>...</InventoryResponse>
        Agent receives: {"sku": "...", "quantity": 150, ...}
        """
        # In production, this would parse XML properly
        # Simplified for demonstration
        return legacy_response

    def call_legacy_system(self, legacy_request: str) -> Dict[str, Any]:
        """
        Simulate calling the legacy SOAP service.

        In production, this would use suds, zeep, or requests
        to make actual SOAP calls.
        """
        # Simulate network delay
        time.sleep(0.1)

        # Simulate occasional failures (10% chance)
        if random.random() < 0.1:
            raise ConnectionError("Legacy system timeout")

        # Parse the "SOAP" request to extract SKU (simplified)
        for sku, data in self._inventory.items():
            if sku in legacy_request:
                return {
                    "sku": sku,
                    "name": data["name"],
                    "quantity": data["quantity"],
                    "warehouse": data["warehouse"],
                    "source": "legacy-erp"
                }

        return {"error": "SKU not found"}


# =============================================================================
# Example: Safe Database Access Adapter
# =============================================================================

@dataclass
class DatabaseCommand:
    """
    Represents a database write command for the command queue.

    Key Principle: Agents should almost never have direct write access
    to production databases. Instead, they submit commands to a queue
    that a validated process executes.
    """
    command_id: str
    command_type: str           # insert, update, delete
    table: str
    data: Dict[str, Any]
    submitted_by: str           # Agent ID
    status: str = "pending"     # pending, validated, executed, rejected
    validation_errors: List[str] = field(default_factory=list)


class SafeDatabaseAdapter(LegacySystemAdapter):
    """
    Adapter implementing safe database access patterns.

    For READ operations:
    - Uses secure views that expose only authorized columns/rows
    - Filters data based on agent's authorization level

    For WRITE operations:
    - Submits to a command queue (not direct writes)
    - Separate validation process approves/rejects
    - Audit trail for all operations

    Key Principle: Read through views, write through queues.
    """

    def __init__(self):
        super().__init__("safe-database")

        # Simulated database tables
        self._customers = {
            "1": {"id": "1", "name": "Alice", "email": "alice@example.com",
                  "ssn": "***-**-1234", "credit_score": 750},
            "2": {"id": "2", "name": "Bob", "email": "bob@example.com",
                  "ssn": "***-**-5678", "credit_score": 680},
        }

        # Command queue for writes
        self._command_queue: List[DatabaseCommand] = []

        # Secure view definitions (which columns agents can see)
        self._secure_views = {
            "customer_basic": ["id", "name", "email"],  # No SSN or credit score
            "customer_full": ["id", "name", "email", "credit_score"]  # Still no SSN
        }

    def translate_request(self, agent_request: Dict[str, Any]) -> Dict[str, Any]:
        """Translate agent request (already JSON, minimal translation needed)."""
        return agent_request

    def translate_response(self, legacy_response: Any) -> Dict[str, Any]:
        """Translate response (already dict, just pass through)."""
        return legacy_response

    def call_legacy_system(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle database operations through safe patterns.
        """
        operation = request.get("operation")
        view_name = request.get("view", "customer_basic")
        customer_id = request.get("customer_id")

        if operation == "read":
            return self._read_through_view(view_name, customer_id)
        elif operation == "write":
            return self._write_through_queue(request)
        else:
            return {"error": f"Unknown operation: {operation}"}

    def _read_through_view(self, view_name: str,
                           customer_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Read data through a secure view.

        Key Principle: The view filters out columns the agent
        shouldn't see (like SSN).
        """
        allowed_columns = self._secure_views.get(view_name)
        if not allowed_columns:
            return {"error": f"View '{view_name}' not found"}

        if customer_id:
            # Single record
            if customer_id not in self._customers:
                return {"error": "Customer not found"}

            customer = self._customers[customer_id]
            # Filter to allowed columns only
            filtered = {k: v for k, v in customer.items() if k in allowed_columns}
            return {"data": filtered, "view": view_name}
        else:
            # All records (filtered)
            results = []
            for customer in self._customers.values():
                filtered = {k: v for k, v in customer.items() if k in allowed_columns}
                results.append(filtered)
            return {"data": results, "view": view_name}

    def _write_through_queue(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Submit write operation to command queue.

        Key Principle: The agent submits a REQUEST to write,
        not the write itself. A separate validated process
        reviews and executes (or rejects) the command.
        """
        command = DatabaseCommand(
            command_id=f"CMD-{len(self._command_queue) + 1:04d}",
            command_type=request.get("command_type", "update"),
            table=request.get("table", ""),
            data=request.get("data", {}),
            submitted_by=request.get("agent_id", "unknown")
        )

        self._command_queue.append(command)

        return {
            "status": "submitted",
            "command_id": command.command_id,
            "message": "Command queued for validation. "
                       "A separate process will review and execute."
        }

    def get_pending_commands(self) -> List[Dict[str, Any]]:
        """Get all pending commands (for the validation process)."""
        return [
            {
                "command_id": cmd.command_id,
                "type": cmd.command_type,
                "table": cmd.table,
                "data": cmd.data,
                "submitted_by": cmd.submitted_by,
                "status": cmd.status
            }
            for cmd in self._command_queue
            if cmd.status == "pending"
        ]


# =============================================================================
# Example: Message Queue Adapter
# =============================================================================

class MessageQueueAdapter:
    """
    Adapter for integrating agents with enterprise message queues.

    Enables agents to participate in existing enterprise workflows
    without requiring those workflows to change.

    Key Principle: A2A task completion can trigger a Kafka event.
    An incoming Kafka message can spawn a new agent task.
    """

    def __init__(self):
        # Simulated message queues
        self._queues: Dict[str, List[Dict[str, Any]]] = {
            "orders": [],
            "notifications": [],
            "agent-tasks": []
        }

    def publish(self, queue_name: str, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Publish a message to a queue.

        Use case: Agent completes a task and notifies downstream systems.
        """
        if queue_name not in self._queues:
            return {"error": f"Queue '{queue_name}' not found"}

        enriched_message = {
            **message,
            "timestamp": time.time(),
            "source": "agent-adapter"
        }

        self._queues[queue_name].append(enriched_message)

        return {
            "status": "published",
            "queue": queue_name,
            "message_count": len(self._queues[queue_name])
        }

    def consume(self, queue_name: str) -> Optional[Dict[str, Any]]:
        """
        Consume a message from a queue.

        Use case: Agent polls for new tasks from enterprise systems.
        """
        if queue_name not in self._queues:
            return {"error": f"Queue '{queue_name}' not found"}

        if self._queues[queue_name]:
            return self._queues[queue_name].pop(0)

        return None


# =============================================================================
# Demonstration
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("Adapter Pattern Demonstration (Legacy System Integration)")
    print("=" * 70)

    # Example 1: SOAP to REST Adapter
    print("\n[1] SOAP to REST Adapter (ERP System)")
    print("-" * 50)
    erp_adapter = ERPSoapAdapter()

    # Agent sends JSON, adapter handles SOAP internally
    result = erp_adapter.execute({
        "action": "get_inventory",
        "sku": "SKU-001"
    })
    print(f"Agent request (JSON): get_inventory for SKU-001")
    print(f"Agent receives (JSON): {result}")

    # Example 2: Safe Database Access
    print("\n[2] Safe Database Adapter (Read through Views)")
    print("-" * 50)
    db_adapter = SafeDatabaseAdapter()

    # Read through basic view (no sensitive data)
    result = db_adapter.execute({
        "operation": "read",
        "view": "customer_basic",
        "customer_id": "1"
    })
    print(f"View 'customer_basic': {result}")

    # Read through full view (more data, but still no SSN)
    result = db_adapter.execute({
        "operation": "read",
        "view": "customer_full",
        "customer_id": "1"
    })
    print(f"View 'customer_full': {result}")

    # Example 3: Write through Command Queue
    print("\n[3] Safe Database Adapter (Write through Queue)")
    print("-" * 50)
    result = db_adapter.execute({
        "operation": "write",
        "command_type": "update",
        "table": "customers",
        "data": {"id": "1", "email": "alice.new@example.com"},
        "agent_id": "customer-service-agent"
    })
    print(f"Write request result: {result}")
    print(f"Pending commands: {db_adapter.get_pending_commands()}")

    # Example 4: Circuit Breaker
    print("\n[4] Circuit Breaker (Resiliency)")
    print("-" * 50)
    cb = CircuitBreaker(failure_threshold=3)
    print(f"Initial state: {cb.state.value}")

    # Simulate failures
    for i in range(4):
        cb.record_failure()
        print(f"After failure {i+1}: {cb.state.value}")

    print(f"Can execute now? {cb.can_execute()}")

    print("\n" + "=" * 70)
    print("Key Takeaways:")
    print("1. Adapters translate protocols (SOAP/XML -> REST/JSON)")
    print("2. Read through secure views that filter sensitive data")
    print("3. Write through command queues, not direct database access")
    print("4. Circuit breakers prevent cascading failures")
    print("5. Retry logic handles transient failures automatically")
    print("=" * 70)
