# Skill 7: Non-Human Identity and Access Management

Patterns for secure agent identity, dynamic credentials, and least privilege access.

## Video Reference

This code accompanies **Video 7: Non-Human Identity** in the Nine Essential Skills series.
[Watch the Video](link)

## Key Concepts

- **Service Principals**: Unique identity for each agent (not shared credentials)
- **Dynamic Credentials**: Time-limited secrets that auto-expire
- **Least Privilege**: Grant only the permissions needed for the task
- **Policy-Based Access**: Context-aware authorization rules

## Examples

### 1. Service Principal Setup

- `azure/create_service_principal.sh` - Create Azure AD service principal
- `aws/create_iam_role.tf` - Terraform for AWS IAM role

### 2. Dynamic Credentials with Vault (`vault_client.py`)

Request time-limited database credentials from HashiCorp Vault.

### 3. OAuth Scopes (`oauth_scopes.py`)

Implement least privilege with explicit OAuth scopes.

### 4. Policy-Based Access with OPA (`opa_policies/`)

Write authorization rules in Rego for context-aware access control.

## Running the Examples

### Vault Example (Local)

```bash
# Start local Vault (requires Docker)
docker run -d --name vault -p 8200:8200 \
  -e 'VAULT_DEV_ROOT_TOKEN_ID=dev-token' \
  vault:latest

# Set environment
export VAULT_ADDR='http://127.0.0.1:8200'
export VAULT_TOKEN='dev-token'

# Run example
pip install -r requirements.txt
python vault_client.py
```

### OPA Example

```bash
# Install OPA
brew install opa  # macOS
# or download from https://www.openpolicyagent.org/

# Test policies
cd opa_policies
opa test . -v

# Run policy server
opa run --server .
```

## Architecture Patterns

| Pattern | When to Use | Key Benefit |
|---------|-------------|-------------|
| Service Principal | Every production agent | Unique identity, audit trail |
| Vault Dynamic Creds | Database/API access | No static secrets |
| OAuth Scopes | Third-party APIs | Fine-grained permissions |
| OPA Policies | Complex authorization | Context-aware rules |

## Key Takeaways

1. **Every agent needs its own identity** - No shared credentials
2. **Dynamic beats static** - Time-limited credentials limit blast radius
3. **Explicit scopes** - Request only what you need
4. **Policy as code** - Authorization rules should be versioned and tested
