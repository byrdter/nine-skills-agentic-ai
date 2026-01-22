"""
Model Context Protocol (MCP) Tool Definitions

Demonstrates the MCP pattern for exposing tools and resources to LLMs.
MCP standardizes how agents access external capabilities - the difference
between an agent that can only talk and one that can actually DO things.

This example shows:
- Tool definition with JSON Schema
- Resource access patterns
- The "Golden Skills" concept (curated, safe tool sets)
- Security considerations for enterprise data exposure

Reference: "Making AI Agents Talk to Each Other" video - Chapter 3

Key Concept: MCP uses a Host-Client-Server topology:
- Host: The LLM application (Claude, GPT, etc.)
- Client: Mediator enforcing security policies
- Server: Capability provider exposing tools and data
"""

import json
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable
from enum import Enum
from abc import ABC, abstractmethod


class ToolCategory(Enum):
    """
    Tool categories for organizing and filtering available capabilities.

    Key Principle: Categorization enables "Golden Skills" - curated sets
    of approved tools appropriate for specific agent roles.
    """
    SEARCH = "search"           # Information retrieval
    COMPUTE = "compute"         # Calculations, data processing
    COMMUNICATE = "communicate" # Emails, messages, notifications
    STORAGE = "storage"         # File and database operations
    EXTERNAL_API = "external"   # Third-party service integrations


class RiskLevel(Enum):
    """
    Risk classification for tools.

    High-risk tools require additional approval or restrictions.
    This implements the capability-based security discussed in the video.
    """
    LOW = "low"         # Read-only, no side effects
    MEDIUM = "medium"   # Limited side effects, reversible
    HIGH = "high"       # Significant side effects, may be irreversible


@dataclass
class MCPTool:
    """
    Represents an MCP Tool - a function the LLM can invoke.

    Tools are the "verbs" of MCP - actions the agent can take.
    Each tool must have a clear schema so the LLM knows:
    1. WHAT the tool does
    2. WHEN to use it (context/conditions)
    3. HOW to call it (parameters)
    4. WHAT it returns (output format)
    """
    name: str
    description: str
    parameters: Dict[str, Any]      # JSON Schema for inputs
    returns: Dict[str, Any]         # JSON Schema for outputs

    # Metadata for discovery and security
    category: ToolCategory = ToolCategory.SEARCH
    risk_level: RiskLevel = RiskLevel.LOW
    requires_approval: bool = False
    tags: List[str] = field(default_factory=list)

    # Optional examples for few-shot learning
    examples: List[Dict[str, Any]] = field(default_factory=list)

    def to_json_schema(self) -> Dict[str, Any]:
        """
        Convert tool definition to JSON Schema format.

        This is the format expected by most LLM function calling APIs.
        """
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }


@dataclass
class MCPResource:
    """
    Represents an MCP Resource - data the LLM can access.

    Resources are the "nouns" of MCP - information the agent can read.
    Unlike tools, resources are passive - they provide data but don't
    perform actions.

    Key Principle: Every Resource request must be authenticated and
    authorized. The MCP Server acts as a secure gateway.
    """
    uri: str                        # Unique identifier (e.g., "file:///docs/policy.md")
    name: str                       # Human-readable name
    description: str                # What this resource contains
    mime_type: str = "text/plain"   # Content type

    # Access control
    required_scopes: List[str] = field(default_factory=list)

    # Optional metadata
    last_updated: Optional[str] = None
    size_bytes: Optional[int] = None


class MCPServer(ABC):
    """
    Abstract base class for an MCP Server.

    The Server exposes Tools and Resources to LLM applications.
    It acts as a secure gateway to enterprise systems, implementing:
    - Authentication and authorization
    - Data masking and filtering
    - Audit logging
    - Rate limiting

    Key Principle: The LLM only sees what it's authorized to see.
    """

    def __init__(self, server_name: str):
        self.server_name = server_name
        self._tools: Dict[str, MCPTool] = {}
        self._resources: Dict[str, MCPResource] = {}

    def register_tool(self, tool: MCPTool) -> None:
        """Register a tool with this server."""
        self._tools[tool.name] = tool

    def register_resource(self, resource: MCPResource) -> None:
        """Register a resource with this server."""
        self._resources[resource.uri] = resource

    def list_tools(self, category: Optional[ToolCategory] = None) -> List[MCPTool]:
        """List available tools, optionally filtered by category."""
        tools = list(self._tools.values())
        if category:
            tools = [t for t in tools if t.category == category]
        return tools

    def list_resources(self) -> List[MCPResource]:
        """List available resources."""
        return list(self._resources.values())

    @abstractmethod
    def execute_tool(self, tool_name: str, parameters: Dict[str, Any],
                     user_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool with the given parameters.

        Args:
            tool_name: Name of the tool to execute
            parameters: Tool input parameters
            user_context: Information about the requesting user/agent

        Returns:
            Tool execution result

        Key Principle: Always validate user_context for authorization
        before executing any tool.
        """
        pass

    @abstractmethod
    def read_resource(self, uri: str, user_context: Dict[str, Any]) -> str:
        """
        Read a resource's contents.

        Args:
            uri: Resource URI
            user_context: Information about the requesting user/agent

        Returns:
            Resource content

        Key Principle: Apply data masking for sensitive fields based
        on user_context authorization level.
        """
        pass


# =============================================================================
# Example: Customer Service MCP Server
# =============================================================================

class CustomerServiceMCPServer(MCPServer):
    """
    Example MCP Server for a customer service agent.

    Demonstrates the "Golden Skills" concept - a carefully scoped set
    of tools appropriate for customer service tasks.

    What's included:
    - Search customer records (read-only)
    - Look up order status
    - Check return eligibility
    - Create support tickets

    What's NOT included (inappropriate for this role):
    - Database deletion tools
    - Payment processing
    - Admin functions
    """

    def __init__(self):
        super().__init__("customer-service-mcp")
        self._setup_tools()
        self._setup_resources()

        # Simulated data store
        self._customers = {
            "CUST-001": {
                "name": "Alice Johnson",
                "email": "alice@example.com",
                "tier": "gold"
            }
        }
        self._orders = {
            "ORD-12345": {
                "customer_id": "CUST-001",
                "status": "shipped",
                "items": ["Widget Pro", "Gadget Plus"],
                "total": 149.99
            }
        }

    def _setup_tools(self) -> None:
        """Register the Golden Skills for customer service."""

        # Tool 1: Search customers (low risk, read-only)
        self.register_tool(MCPTool(
            name="search_customer",
            description=(
                "Search for a customer by ID, email, or name. "
                "Use when the user provides customer identification. "
                "Returns customer profile with name, email, and tier. "
                "Does NOT return sensitive data like payment info."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Customer ID, email, or name to search"
                    }
                },
                "required": ["query"]
            },
            returns={
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string"},
                    "name": {"type": "string"},
                    "email": {"type": "string"},
                    "tier": {"type": "string"}
                }
            },
            category=ToolCategory.SEARCH,
            risk_level=RiskLevel.LOW,
            tags=["customer", "lookup", "search"],
            examples=[
                {
                    "input": {"query": "CUST-001"},
                    "output": {"customer_id": "CUST-001", "name": "Alice Johnson"}
                }
            ]
        ))

        # Tool 2: Order status (low risk, read-only)
        self.register_tool(MCPTool(
            name="get_order_status",
            description=(
                "Retrieve the current status of an order. "
                "Use when customer asks about their order. "
                "Input is the order ID (format: ORD-XXXXX). "
                "Returns order status, items, and shipping info."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "pattern": "^ORD-[0-9]+$",
                        "description": "Order ID in format ORD-XXXXX"
                    }
                },
                "required": ["order_id"]
            },
            returns={
                "type": "object",
                "properties": {
                    "order_id": {"type": "string"},
                    "status": {"type": "string"},
                    "items": {"type": "array"},
                    "tracking_number": {"type": "string"}
                }
            },
            category=ToolCategory.SEARCH,
            risk_level=RiskLevel.LOW,
            tags=["order", "status", "tracking"]
        ))

        # Tool 3: Create support ticket (medium risk, creates data)
        self.register_tool(MCPTool(
            name="create_support_ticket",
            description=(
                "Create a new support ticket for customer issues. "
                "Use when the issue cannot be resolved immediately "
                "and needs escalation or follow-up. "
                "Returns the ticket ID for reference."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string"},
                    "issue_type": {
                        "type": "string",
                        "enum": ["billing", "shipping", "product", "account", "other"]
                    },
                    "description": {"type": "string"},
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                        "default": "medium"
                    }
                },
                "required": ["customer_id", "issue_type", "description"]
            },
            returns={
                "type": "object",
                "properties": {
                    "ticket_id": {"type": "string"},
                    "status": {"type": "string"},
                    "estimated_response_time": {"type": "string"}
                }
            },
            category=ToolCategory.STORAGE,
            risk_level=RiskLevel.MEDIUM,
            tags=["support", "ticket", "escalation"]
        ))

    def _setup_resources(self) -> None:
        """Register available data resources."""

        self.register_resource(MCPResource(
            uri="policy://return-policy",
            name="Return Policy",
            description="Current return and refund policy document",
            mime_type="text/markdown",
            required_scopes=["customer_service:read"]
        ))

        self.register_resource(MCPResource(
            uri="policy://shipping-info",
            name="Shipping Information",
            description="Shipping rates, times, and carrier information",
            mime_type="text/markdown",
            required_scopes=["customer_service:read"]
        ))

    def execute_tool(self, tool_name: str, parameters: Dict[str, Any],
                     user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool with authorization checks."""

        # Verify tool exists
        if tool_name not in self._tools:
            return {"error": f"Tool '{tool_name}' not found"}

        tool = self._tools[tool_name]

        # Check if approval is required (for high-risk tools)
        if tool.requires_approval:
            # In production, this would trigger an approval workflow
            return {"error": "This tool requires human approval"}

        # Execute based on tool name
        if tool_name == "search_customer":
            return self._search_customer(parameters.get("query", ""))
        elif tool_name == "get_order_status":
            return self._get_order_status(parameters.get("order_id", ""))
        elif tool_name == "create_support_ticket":
            return self._create_ticket(parameters)
        else:
            return {"error": f"Tool '{tool_name}' not implemented"}

    def read_resource(self, uri: str, user_context: Dict[str, Any]) -> str:
        """Read a resource with authorization checks."""

        if uri not in self._resources:
            return f"Resource '{uri}' not found"

        resource = self._resources[uri]

        # Check authorization (simplified - production would check user_context)
        # Key Principle: Always verify scopes before returning data

        if uri == "policy://return-policy":
            return """
# Return Policy

Items may be returned within 30 days of purchase for a full refund.
- Items must be in original packaging
- Electronics must be unopened
- Sale items are final sale

For returns, please contact customer service with your order number.
"""
        elif uri == "policy://shipping-info":
            return """
# Shipping Information

- Standard Shipping: 5-7 business days ($5.99)
- Express Shipping: 2-3 business days ($12.99)
- Overnight Shipping: Next business day ($24.99)

Free shipping on orders over $50!
"""
        return ""

    def _search_customer(self, query: str) -> Dict[str, Any]:
        """Search for a customer (internal implementation)."""
        # Simplified - production would search database
        for cust_id, data in self._customers.items():
            if query in cust_id or query.lower() in data["email"].lower():
                return {
                    "customer_id": cust_id,
                    "name": data["name"],
                    "email": data["email"],
                    "tier": data["tier"]
                }
        return {"error": "Customer not found"}

    def _get_order_status(self, order_id: str) -> Dict[str, Any]:
        """Get order status (internal implementation)."""
        if order_id in self._orders:
            order = self._orders[order_id]
            return {
                "order_id": order_id,
                "status": order["status"],
                "items": order["items"],
                "total": order["total"]
            }
        return {"error": "Order not found"}

    def _create_ticket(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a support ticket (internal implementation)."""
        import random
        ticket_id = f"TKT-{random.randint(10000, 99999)}"
        return {
            "ticket_id": ticket_id,
            "status": "open",
            "estimated_response_time": "24 hours"
        }


# =============================================================================
# Demonstration
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("MCP Tools Demonstration (Model Context Protocol)")
    print("=" * 70)

    # Create the MCP server
    server = CustomerServiceMCPServer()

    # List available tools (Golden Skills)
    print("\n[1] Golden Skills - Available Tools")
    print("-" * 50)
    for tool in server.list_tools():
        print(f"  - {tool.name} [{tool.risk_level.value} risk]")
        print(f"    {tool.description[:60]}...")

    # Show tool schema (what the LLM sees)
    print("\n[2] Tool Schema (JSON for LLM)")
    print("-" * 50)
    tool = server._tools["search_customer"]
    print(json.dumps(tool.to_json_schema(), indent=2))

    # Execute a tool
    print("\n[3] Tool Execution")
    print("-" * 50)
    user_context = {"user_id": "agent-001", "scopes": ["customer_service:read"]}

    result = server.execute_tool(
        "search_customer",
        {"query": "CUST-001"},
        user_context
    )
    print(f"search_customer('CUST-001'): {result}")

    result = server.execute_tool(
        "get_order_status",
        {"order_id": "ORD-12345"},
        user_context
    )
    print(f"get_order_status('ORD-12345'): {result}")

    # Read a resource
    print("\n[4] Resource Access")
    print("-" * 50)
    policy = server.read_resource("policy://return-policy", user_context)
    print(f"Return Policy:\n{policy[:200]}...")

    print("\n" + "=" * 70)
    print("Key Takeaways:")
    print("1. MCP Tools are 'verbs' - actions the agent can take")
    print("2. MCP Resources are 'nouns' - data the agent can read")
    print("3. Golden Skills = curated, role-appropriate tool sets")
    print("4. Every request must be authorized against user context")
    print("=" * 70)
