# Azure Key Vault access
# NOTE: This module is maintained in the CS-DOCUMENT-GENERATOR app, do not edit elsewhere.

import os
from typing import Optional
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient


def get_kv_client() -> Optional[SecretClient]:
    """Return a SecretClient if KEY_VAULT_NAME is configured, else None."""
    kv_name = os.environ.get("KEY_VAULT_NAME")
    if not kv_name:
        return None
    vault_uri = f"https://{kv_name}.vault.azure.net"
    
    # Configure region for Azure - explicitly set region for better performance
    credential = DefaultAzureCredential(
        additionally_allowed_tenants=["*"],
        azure_region="uksouth",
        # Add exclude options to speed up credential resolution
        exclude_visual_studio_code_credential=True,
        exclude_shared_token_cache_credential=True,
        exclude_powershell_credential=True
    )
    return SecretClient(vault_url=vault_uri, credential=credential)


def get_secret(env_name: str, kv_secret_name: Optional[str] = None) -> str:
    """
    Fetch a secret from environment, or (if not set) from Azure Key Vault.
    kv_secret_name defaults to env_name if not supplied.
    """
    val = os.environ.get(env_name)
    if val:
        return val

    client = get_kv_client()
    if not client:
        raise KeyError(
            f"Required secret '{env_name}' not set and KEY_VAULT_NAME is not configured."
        )

    secret_name = kv_secret_name or env_name
    try:
        result = client.get_secret(secret_name).value 
        return result if result is not None else ""
    except Exception as exc:
        raise KeyError(
            f"Failed to retrieve '{secret_name}' from Azure Key Vault."
        ) from exc