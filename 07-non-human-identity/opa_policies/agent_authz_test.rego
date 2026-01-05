# Tests for Agent Authorization Policies
# Run with: opa test . -v

package agent.authz

# Test: Invoice agent can read invoices during business hours
test_invoice_read_allowed if {
    allow with input as {
        "agent_id": "invoice-processor",
        "action": "read",
        "resource_type": "invoice"
    }
    # Note: This test assumes it's run during business hours
    # In CI, you'd mock the time
}

# Test: Payment under $10k auto-approved
test_payment_under_limit if {
    allow with input as {
        "agent_id": "payment-processor",
        "action": "process_payment",
        "amount": 5000
    }
}

# Test: Payment over $10k requires approval
test_payment_over_limit_denied if {
    not allow with input as {
        "agent_id": "payment-processor",
        "action": "process_payment",
        "amount": 15000,
        "has_approval": false
    }
}

# Test: Payment over $10k with approval allowed
test_payment_over_limit_with_approval if {
    allow with input as {
        "agent_id": "payment-processor",
        "action": "process_payment",
        "amount": 15000,
        "has_approval": true
    }
}

# Test: Customer service can read customers
test_customer_service_read if {
    allow with input as {
        "agent_id": "customer-service",
        "action": "read",
        "resource_type": "customer"
    }
}

# Test: Customer service cannot modify
test_customer_service_no_write if {
    not allow with input as {
        "agent_id": "customer-service",
        "action": "update",
        "resource_type": "customer"
    }
}

# Test: Analytics can read allowed tables
test_analytics_allowed_table if {
    allow with input as {
        "agent_id": "analytics",
        "action": "read",
        "resource_type": "table",
        "resource_name": "orders_summary"
    }
}

# Test: Analytics cannot read PII tables
test_analytics_pii_denied if {
    not allow with input as {
        "agent_id": "analytics",
        "action": "read",
        "resource_type": "table",
        "resource_name": "customers"
    }
}

# Test: Unknown agent denied by default
test_unknown_agent_denied if {
    not allow with input as {
        "agent_id": "unknown-agent",
        "action": "read",
        "resource_type": "anything"
    }
}
