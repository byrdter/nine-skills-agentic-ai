# Agent Authorization Policies
# Using Open Policy Agent (OPA) for context-aware access control
#
# These policies demonstrate:
# - Business hours restrictions
# - Amount-based approval requirements
# - Role-based permissions
# - Resource-specific access control

package agent.authz

import future.keywords.if
import future.keywords.in

# Default deny - explicit allow required
default allow := false

# ---------------------------------------------
# RULE 1: Invoice Agent - Read Invoices
# Only during business hours (9 AM - 5 PM)
# ---------------------------------------------

allow if {
    input.agent_id == "invoice-processor"
    input.action == "read"
    input.resource_type == "invoice"
    is_business_hours
}

is_business_hours if {
    # Get current hour (0-23)
    time.clock(time.now_ns())[0] >= 9
    time.clock(time.now_ns())[0] < 17
}

# ---------------------------------------------
# RULE 2: Payment Agent - Process Payments
# Under $10,000: auto-approve
# Over $10,000: requires human approval
# ---------------------------------------------

allow if {
    input.agent_id == "payment-processor"
    input.action == "process_payment"
    input.amount <= 10000
}

allow if {
    input.agent_id == "payment-processor"
    input.action == "process_payment"
    input.amount > 10000
    input.has_approval == true
}

# Denial reason for audit logging
deny_reason["Payment over $10,000 requires human approval"] if {
    input.agent_id == "payment-processor"
    input.action == "process_payment"
    input.amount > 10000
    not input.has_approval
}

# ---------------------------------------------
# RULE 3: Customer Service Agent
# Can read customer data, cannot modify
# ---------------------------------------------

allow if {
    input.agent_id == "customer-service"
    input.action == "read"
    input.resource_type in ["customer", "order", "ticket"]
}

# Explicitly deny write operations
deny_reason["Customer service agent cannot modify data"] if {
    input.agent_id == "customer-service"
    input.action in ["create", "update", "delete"]
}

# ---------------------------------------------
# RULE 4: Analytics Agent
# Read-only access to specific tables
# No PII access
# ---------------------------------------------

allow if {
    input.agent_id == "analytics"
    input.action == "read"
    input.resource_type == "table"
    input.resource_name in allowed_analytics_tables
    not contains_pii(input.resource_name)
}

allowed_analytics_tables := {
    "orders_summary",
    "product_metrics",
    "sales_by_region",
    "inventory_levels"
}

# Tables containing PII - analytics agent cannot access
contains_pii(table_name) if {
    table_name in {
        "customers",
        "customer_addresses",
        "payment_methods",
        "user_credentials"
    }
}

deny_reason["Analytics agent cannot access PII tables"] if {
    input.agent_id == "analytics"
    contains_pii(input.resource_name)
}

# ---------------------------------------------
# HELPER: Collect all denial reasons
# ---------------------------------------------

all_deny_reasons := reasons if {
    reasons := {reason | deny_reason[reason]}
}
