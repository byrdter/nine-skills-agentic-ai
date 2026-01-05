"""
Dynamic Credentials with HashiCorp Vault

Demonstrates requesting time-limited credentials instead of using static secrets.
This is the pattern that eliminates hardcoded API keys and passwords.

Prerequisites:
- HashiCorp Vault running (see README for local setup)
- VAULT_ADDR and VAULT_TOKEN environment variables set
"""

import os
import hvac
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Optional


@dataclass
class DynamicCredential:
    """Represents a time-limited credential."""
    username: str
    password: str
    issued_at: datetime
    expires_at: datetime
    lease_id: str

    @property
    def is_expired(self) -> bool:
        return datetime.now() >= self.expires_at

    @property
    def time_remaining(self) -> timedelta:
        return self.expires_at - datetime.now()


class VaultCredentialManager:
    """
    Manages dynamic credentials from HashiCorp Vault.

    Key principles:
    - Never store credentials in code or config files
    - Request credentials on-demand
    - Credentials auto-expire (typically 1 hour)
    - Rotate credentials before expiration
    """

    def __init__(self, vault_addr: str = None, vault_token: str = None):
        self.vault_addr = vault_addr or os.environ.get("VAULT_ADDR", "http://127.0.0.1:8200")
        self.vault_token = vault_token or os.environ.get("VAULT_TOKEN")

        if not self.vault_token:
            raise ValueError("VAULT_TOKEN environment variable required")

        self.client = hvac.Client(url=self.vault_addr, token=self.vault_token)
        self._cached_creds: dict[str, DynamicCredential] = {}

    def get_database_credentials(
        self,
        role: str,
        mount_point: str = "database",
        force_new: bool = False
    ) -> DynamicCredential:
        """
        Get database credentials for a specific role.

        The Vault database secrets engine generates unique credentials
        for each request with a built-in TTL.

        Args:
            role: The Vault role (e.g., 'readonly-invoices')
            mount_point: Vault mount point for database engine
            force_new: Force new credentials even if cached ones valid

        Returns:
            DynamicCredential with username, password, and expiration
        """
        cache_key = f"{mount_point}/{role}"

        # Check cache first (don't request new creds if we have valid ones)
        if not force_new and cache_key in self._cached_creds:
            cached = self._cached_creds[cache_key]
            # Renew if less than 5 minutes remaining
            if cached.time_remaining > timedelta(minutes=5):
                print(f"Using cached credentials ({cached.time_remaining} remaining)")
                return cached

        # Request new credentials from Vault
        print(f"Requesting new credentials for role: {role}")

        try:
            response = self.client.secrets.database.generate_credentials(
                name=role,
                mount_point=mount_point
            )
        except Exception as e:
            raise RuntimeError(f"Failed to get credentials from Vault: {e}")

        # Parse response
        lease_duration = response["lease_duration"]  # seconds
        creds = DynamicCredential(
            username=response["data"]["username"],
            password=response["data"]["password"],
            issued_at=datetime.now(),
            expires_at=datetime.now() + timedelta(seconds=lease_duration),
            lease_id=response["lease_id"]
        )

        # Cache the credentials
        self._cached_creds[cache_key] = creds

        print(f"New credentials issued, valid for {lease_duration} seconds")
        return creds

    def revoke_credentials(self, credential: DynamicCredential):
        """
        Revoke credentials before expiration.

        Use this for emergency revocation if a credential is compromised.
        """
        print(f"Revoking credential: {credential.lease_id}")
        self.client.sys.revoke_lease(credential.lease_id)
        print("Credential revoked successfully")


def demonstrate_vault_pattern():
    """
    Demonstrate the dynamic credentials pattern.

    This is the pattern you should use instead of:
    - Hardcoded passwords in code
    - API keys in environment variables
    - Shared credentials across agents
    """
    print("=" * 60)
    print("Dynamic Credentials Pattern with HashiCorp Vault")
    print("=" * 60)

    # In production, the agent authenticates to Vault using its
    # service principal (e.g., Kubernetes service account, AWS IAM role)
    # For this demo, we use a token directly.

    try:
        manager = VaultCredentialManager()
    except ValueError as e:
        print(f"\nSetup required: {e}")
        print("\nTo run this example:")
        print("1. Start Vault: docker run -d --name vault -p 8200:8200 -e 'VAULT_DEV_ROOT_TOKEN_ID=dev-token' vault:latest")
        print("2. Set env vars: export VAULT_ADDR='http://127.0.0.1:8200' VAULT_TOKEN='dev-token'")
        print("3. Configure database secrets engine in Vault")
        return

    # In a real scenario, you would:
    # 1. Configure the database secrets engine in Vault
    # 2. Create a role that maps to database permissions
    # 3. Your agent requests credentials using that role

    print("\n[Step 1] Agent requests database credentials")
    print("-" * 40)

    # Simulated credential request (would work with real Vault setup)
    print("# In production, this would call Vault:")
    print("# creds = manager.get_database_credentials('readonly-invoices')")
    print("#")
    print("# Returns:")
    print("#   username: v-token-readonly-abc123")
    print("#   password: <random-generated>")
    print("#   expires_at: <1 hour from now>")

    print("\n[Step 2] Agent uses credentials for database operation")
    print("-" * 40)
    print("# connection = psycopg2.connect(")
    print("#     host='db.example.com',")
    print("#     database='invoices',")
    print("#     user=creds.username,")
    print("#     password=creds.password")
    print("# )")
    print("#")
    print("# Note: These credentials auto-expire in 1 hour")
    print("# Even if leaked, the window of exposure is limited")

    print("\n[Step 3] Credentials expire automatically")
    print("-" * 40)
    print("# After TTL (e.g., 1 hour):")
    print("# - Credentials stop working")
    print("# - No manual rotation needed")
    print("# - Agent requests new credentials when needed")

    print("\n[Key Benefits]")
    print("-" * 40)
    print("- No static secrets in code or config")
    print("- Each credential is unique and time-limited")
    print("- Automatic expiration limits blast radius")
    print("- Full audit trail of who requested what credentials")
    print("- Emergency revocation if compromise detected")


if __name__ == "__main__":
    demonstrate_vault_pattern()
