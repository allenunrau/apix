"""
Auth module - specifies authentication method and credentials for each host.

Accepts a YAML config listing hosts with their auth method and credentials.
Supports: basic, bearer, api-key, oauth2-client-credentials
"""

from __future__ import annotations

import base64
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional

import yaml


class AuthMethod(str, Enum):
    BASIC = "basic"
    BEARER = "bearer"
    API_KEY = "api-key"
    OAUTH2_CLIENT_CREDENTIALS = "oauth2-client-credentials"


@dataclass
class AuthConfig:
    """Authentication configuration for a single host."""

    host: str
    method: AuthMethod
    credentials: Dict[str, str] = field(default_factory=dict)

    def get_headers(self, client: Optional[Any] = None) -> Dict[str, str]:
        """Generate HTTP headers for this auth method."""
        headers: Dict[str, str] = {}

        if self.method == AuthMethod.BASIC:
            username = self.credentials.get("username", "")
            password = self.credentials.get("password", "")
            encoded = base64.b64encode(f"{username}:{password}".encode()).decode()
            headers["Authorization"] = f"Basic {encoded}"

        elif self.method == AuthMethod.BEARER:
            token = self.credentials.get("token", "")
            headers["Authorization"] = f"Bearer {token}"

        elif self.method == AuthMethod.API_KEY:
            key_name = self.credentials.get("key_name", "X-API-Key")
            key_value = self.credentials.get("key_value", "")
            headers[key_name] = key_value

        elif self.method == AuthMethod.OAUTH2_CLIENT_CREDENTIALS:
            # Fetch token via client credentials grant
            token_url = self.credentials.get("token_url", f"https://{self.host}/oauth/token")
            client_id = self.credentials.get("client_id", "")
            client_secret = self.credentials.get("client_secret", "")
            scope = self.credentials.get("scope", "")

            import httpx

            data = {
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
            }
            if scope:
                data["scope"] = scope

            resp = httpx.post(token_url, data=data)
            resp.raise_for_status()
            token = resp.json().get("access_token", "")
            headers["Authorization"] = f"Bearer {token}"

        return headers


def load_auth_config(path: str) -> Dict[str, AuthConfig]:
    """Load auth configuration from a YAML file.

    Expected YAML format:
    ```yaml
    - host: api.example.com
      method: bearer
      credentials:
        token: your-token-here
    - host: another-api.com
      method: basic
      credentials:
        username: user
        password: pass
    ```
    """
    with open(path) as f:
        data = yaml.safe_load(f)

    if not data:
        return {}

    configs: Dict[str, AuthConfig] = {}
    for entry in data:
        host = entry.get("host", "")
        method = AuthMethod(entry.get("method", "bearer"))
        creds = entry.get("credentials", {})
        configs[host] = AuthConfig(host=host, method=method, credentials=creds)

    return configs