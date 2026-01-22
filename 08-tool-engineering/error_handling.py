"""
Structured Error Handling for Agent Tools

Demonstrates how to design error responses that enable agents
to self-correct rather than fail repeatedly.

This example shows:
- Structured error response format
- Actionable error messages with suggestions
- Error categories for programmatic handling
- Graceful degradation patterns

Reference: "Golden Tools vs. Dangerous APIs" video - Chapter 2

Key Concept: A tool that returns "Error 500: NullPointerException" is useless
to an agent. Structured errors with suggestions enable self-correction.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime


class ErrorCategory(Enum):
    """
    Categories of tool errors for programmatic handling.

    Agents can take different actions based on error category.
    """
    VALIDATION = "validation"       # Bad input parameters
    NOT_FOUND = "not_found"         # Resource doesn't exist
    PERMISSION = "permission"       # Not authorized
    RATE_LIMIT = "rate_limit"       # Too many requests
    TIMEOUT = "timeout"             # Operation took too long
    DEPENDENCY = "dependency"       # External service failed
    INTERNAL = "internal"           # Unexpected error


class RecoveryAction(Enum):
    """Suggested recovery actions for the agent."""
    RETRY = "retry"                 # Try the same request again
    MODIFY_INPUT = "modify_input"   # Change the input parameters
    USE_FALLBACK = "use_fallback"   # Use an alternative tool
    ESCALATE = "escalate"           # Ask for human help
    WAIT = "wait"                   # Wait and retry later
    ABORT = "abort"                 # Cannot recover


@dataclass
class StructuredError:
    """
    A structured error response that enables agent self-correction.

    Key Principle: Include not just WHAT went wrong,
    but HOW the agent can fix it.
    """
    # Required fields
    error_code: str                 # Machine-readable code (e.g., "MISSING_PARAMETER")
    message: str                    # Human-readable message
    category: ErrorCategory

    # Recovery guidance
    suggestion: str = ""            # How to fix the problem
    recovery_action: RecoveryAction = RecoveryAction.ABORT
    retry_after_seconds: Optional[int] = None

    # Context for debugging
    parameter_name: Optional[str] = None  # Which parameter caused the error
    parameter_value: Optional[Any] = None  # What value was provided
    expected_format: Optional[str] = None  # What format is expected

    # Metadata
    timestamp: datetime = field(default_factory=datetime.now)
    request_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON response."""
        result = {
            "error": True,
            "error_code": self.error_code,
            "message": self.message,
            "category": self.category.value,
            "suggestion": self.suggestion,
            "recovery_action": self.recovery_action.value,
        }

        if self.parameter_name:
            result["parameter_name"] = self.parameter_name
        if self.expected_format:
            result["expected_format"] = self.expected_format
        if self.retry_after_seconds:
            result["retry_after_seconds"] = self.retry_after_seconds

        return result


class ToolErrorHandler:
    """
    Creates structured errors for common tool failure scenarios.

    In production, use this handler in your tool implementations
    to ensure consistent, helpful error responses.
    """

    @staticmethod
    def missing_parameter(param_name: str, expected_type: str = "") -> StructuredError:
        """Error for missing required parameter."""
        return StructuredError(
            error_code="MISSING_PARAMETER",
            message=f"Required parameter '{param_name}' is missing",
            category=ErrorCategory.VALIDATION,
            suggestion=f"Please provide the '{param_name}' parameter"
                       + (f" as a {expected_type}" if expected_type else ""),
            recovery_action=RecoveryAction.MODIFY_INPUT,
            parameter_name=param_name,
            expected_format=expected_type
        )

    @staticmethod
    def invalid_format(param_name: str, value: Any, expected: str) -> StructuredError:
        """Error for invalid parameter format."""
        return StructuredError(
            error_code="INVALID_FORMAT",
            message=f"Parameter '{param_name}' has invalid format",
            category=ErrorCategory.VALIDATION,
            suggestion=f"Expected format: {expected}. Please reformat and try again.",
            recovery_action=RecoveryAction.MODIFY_INPUT,
            parameter_name=param_name,
            parameter_value=str(value)[:100],  # Truncate for safety
            expected_format=expected
        )

    @staticmethod
    def not_found(resource_type: str, identifier: str) -> StructuredError:
        """Error for resource not found."""
        return StructuredError(
            error_code="NOT_FOUND",
            message=f"{resource_type} '{identifier}' not found",
            category=ErrorCategory.NOT_FOUND,
            suggestion=f"Verify the {resource_type.lower()} ID is correct. "
                       "You may need to search for available options first.",
            recovery_action=RecoveryAction.MODIFY_INPUT
        )

    @staticmethod
    def rate_limited(retry_after: int) -> StructuredError:
        """Error for rate limiting."""
        return StructuredError(
            error_code="RATE_LIMITED",
            message="Too many requests. Rate limit exceeded.",
            category=ErrorCategory.RATE_LIMIT,
            suggestion=f"Wait {retry_after} seconds before retrying.",
            recovery_action=RecoveryAction.WAIT,
            retry_after_seconds=retry_after
        )

    @staticmethod
    def permission_denied(action: str, reason: str = "") -> StructuredError:
        """Error for permission issues."""
        return StructuredError(
            error_code="PERMISSION_DENIED",
            message=f"Not authorized to {action}",
            category=ErrorCategory.PERMISSION,
            suggestion=reason if reason else "This action requires different permissions. "
                       "You may need to escalate to a human.",
            recovery_action=RecoveryAction.ESCALATE
        )

    @staticmethod
    def timeout(operation: str, timeout_seconds: int) -> StructuredError:
        """Error for operation timeout."""
        return StructuredError(
            error_code="TIMEOUT",
            message=f"Operation '{operation}' timed out after {timeout_seconds}s",
            category=ErrorCategory.TIMEOUT,
            suggestion="The operation took too long. You can retry with a simpler request "
                       "or try again later when the system is less busy.",
            recovery_action=RecoveryAction.RETRY
        )


def compare_error_responses():
    """
    Compare BAD vs GOOD error response design.
    """
    print("\n" + "=" * 60)
    print("BAD vs GOOD Error Response Comparison")
    print("=" * 60)

    print("\n[BAD] Cryptic Error (Agent Cannot Self-Correct):")
    print("-" * 40)
    bad_error = {
        "error": True,
        "code": 500,
        "message": "NullPointerException at line 42"
    }
    print(f"  Response: {bad_error}")
    print("  Problem: Agent has no idea what went wrong or how to fix it.")

    print("\n[GOOD] Structured Error (Agent Can Self-Correct):")
    print("-" * 40)
    handler = ToolErrorHandler()
    good_error = handler.missing_parameter("customer_id", "string")
    print(f"  Response: {good_error.to_dict()}")
    print(f"\n  Agent can now:")
    print(f"    1. Understand: Parameter 'customer_id' is missing")
    print(f"    2. Fix: Add the customer_id parameter")
    print(f"    3. Retry: With the corrected input")


# =============================================================================
# Demonstration
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("Structured Error Handling Demonstration")
    print("=" * 70)

    handler = ToolErrorHandler()

    # Example errors
    print("\n[1] Common Error Scenarios")
    print("-" * 50)

    errors = [
        ("Missing Parameter", handler.missing_parameter("order_id", "string (ORD-XXXXX format)")),
        ("Invalid Format", handler.invalid_format("date", "2026/01/15", "YYYY-MM-DD")),
        ("Not Found", handler.not_found("Customer", "CUST-99999")),
        ("Rate Limited", handler.rate_limited(30)),
        ("Permission Denied", handler.permission_denied("delete customer records")),
    ]

    for name, error in errors:
        print(f"\n  {name}:")
        print(f"    Code: {error.error_code}")
        print(f"    Message: {error.message}")
        print(f"    Suggestion: {error.suggestion}")
        print(f"    Recovery: {error.recovery_action.value}")

    # Compare bad vs good
    compare_error_responses()

    # Show error categories
    print("\n[2] Error Categories and Recovery Actions")
    print("-" * 50)

    categories = [
        (ErrorCategory.VALIDATION, RecoveryAction.MODIFY_INPUT, "Fix the input and retry"),
        (ErrorCategory.NOT_FOUND, RecoveryAction.MODIFY_INPUT, "Search for valid options"),
        (ErrorCategory.RATE_LIMIT, RecoveryAction.WAIT, "Wait and retry later"),
        (ErrorCategory.PERMISSION, RecoveryAction.ESCALATE, "Ask human for help"),
        (ErrorCategory.TIMEOUT, RecoveryAction.RETRY, "Retry with simpler request"),
    ]

    for cat, action, guidance in categories:
        print(f"  {cat.value:12} -> {action.value:12} | {guidance}")

    print("\n" + "=" * 70)
    print("Key Takeaways:")
    print("1. Include WHAT went wrong (error code, message)")
    print("2. Include HOW to fix it (suggestion, expected format)")
    print("3. Include WHAT action to take (retry, modify, escalate)")
    print("4. Structured errors enable agent self-correction")
    print("=" * 70)
