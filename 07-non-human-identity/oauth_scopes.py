"""
OAuth Scopes for Least Privilege

Demonstrates how to request only the permissions your agent needs.
The scopes travel with the token - the API enforces them automatically.
"""

from dataclasses import dataclass
from typing import Optional
import json


@dataclass
class TokenRequest:
    """Represents an OAuth token request with specific scopes."""
    client_id: str
    scopes: list[str]

    def display(self):
        print(f"Client ID: {self.client_id}")
        print(f"Requested Scopes:")
        for scope in self.scopes:
            print(f"  - {scope}")


@dataclass
class AccessToken:
    """Represents an issued access token."""
    token: str
    scopes: list[str]
    expires_in: int

    def has_scope(self, scope: str) -> bool:
        """Check if token has a specific scope."""
        return scope in self.scopes


def demonstrate_scope_patterns():
    """
    Demonstrate OAuth scope patterns for least privilege.

    Key principle: Request ONLY the scopes your agent needs.
    More scopes = more risk if the token is compromised.
    """
    print("=" * 60)
    print("OAuth Scopes for Least Privilege")
    print("=" * 60)

    # BAD: Over-privileged agent
    print("\n[BAD EXAMPLE] Over-privileged agent")
    print("-" * 40)

    bad_request = TokenRequest(
        client_id="agent-001",
        scopes=[
            "https://graph.microsoft.com/Mail.ReadWrite",      # Can read AND write
            "https://graph.microsoft.com/Calendars.ReadWrite", # Can read AND write
            "https://graph.microsoft.com/Files.ReadWrite.All", # ALL files!
            "https://graph.microsoft.com/User.ReadWrite.All",  # ALL users!
        ]
    )
    print("This agent requests:")
    bad_request.display()
    print("\nProblem: If compromised, attacker can:")
    print("  - Read and send emails as the agent")
    print("  - Modify anyone's calendar")
    print("  - Access and modify ALL files")
    print("  - Modify ALL user accounts")
    print("  This is NOT least privilege!")

    # GOOD: Least-privilege agent
    print("\n[GOOD EXAMPLE] Least-privilege agent")
    print("-" * 40)

    good_request = TokenRequest(
        client_id="invoice-processor-agent",
        scopes=[
            "https://graph.microsoft.com/Mail.Read",           # Read only
            "https://graph.microsoft.com/Calendars.Read",      # Read only
            # No file access - doesn't need it
            # No user management - doesn't need it
        ]
    )
    print("This agent requests:")
    good_request.display()
    print("\nBenefit: If compromised, attacker can ONLY:")
    print("  - Read emails (not send)")
    print("  - Read calendars (not modify)")
    print("  - Nothing else!")
    print("  Blast radius is contained.")

    # Scope verification at runtime
    print("\n[RUNTIME] API validates scopes on every request")
    print("-" * 40)

    # Simulate a token with limited scopes
    token = AccessToken(
        token="eyJ0eXAiOiJKV1...",
        scopes=["Mail.Read", "Calendars.Read"],
        expires_in=3600
    )

    # API checks scopes before allowing operations
    operations = [
        ("Mail.Read", "Read inbox"),
        ("Mail.Send", "Send email"),
        ("Calendars.Read", "Read calendar"),
        ("Calendars.ReadWrite", "Create meeting"),
        ("Files.Read", "Read files"),
    ]

    print("Token scopes:", token.scopes)
    print("\nOperation attempts:")
    for scope, description in operations:
        allowed = token.has_scope(scope) or token.has_scope(scope.replace(".Read", ".ReadWrite"))
        status = "ALLOWED" if allowed else "DENIED"
        symbol = "[OK]" if allowed else "[X] "
        print(f"  {symbol} {description}: {status}")


def show_scope_examples():
    """Show common scope patterns for different APIs."""
    print("\n" + "=" * 60)
    print("Common Scope Patterns by Service")
    print("=" * 60)

    scope_examples = {
        "Microsoft Graph": {
            "Read emails": "Mail.Read",
            "Send emails": "Mail.Send",
            "Read calendar": "Calendars.Read",
            "Manage calendar": "Calendars.ReadWrite",
            "Read files": "Files.Read",
            "Manage files": "Files.ReadWrite",
        },
        "Google APIs": {
            "Read Gmail": "gmail.readonly",
            "Send Gmail": "gmail.send",
            "Read Calendar": "calendar.readonly",
            "Manage Calendar": "calendar.events",
            "Read Drive": "drive.readonly",
            "Manage Drive": "drive.file",
        },
        "GitHub": {
            "Read repos": "repo:read",
            "Write repos": "repo:write",
            "Read user": "read:user",
            "Manage workflows": "workflow",
        },
        "Salesforce": {
            "API access": "api",
            "Read data": "readonly",
            "Full access": "full",
            "Refresh token": "refresh_token",
        }
    }

    for service, scopes in scope_examples.items():
        print(f"\n{service}:")
        for description, scope in scopes.items():
            print(f"  {description:20} -> {scope}")

    print("\n[Key Principle]")
    print("-" * 40)
    print("Always choose the MINIMUM scope that allows your agent to function.")
    print("'Read' is better than 'ReadWrite'")
    print("Specific resources are better than 'All'")
    print("Ask: 'What's the LEAST my agent needs to do its job?'")


if __name__ == "__main__":
    demonstrate_scope_patterns()
    show_scope_examples()
