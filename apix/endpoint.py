"""
Endpoint module - processes a YAML list of endpoints and calls them.

Input is a YAML list of:
  - host: api.example.com
    method: GET
    uri: /users
    body: {}  # optional, required for POST/PUT/PATCH
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import httpx
import yaml

from .auth import AuthConfig


@dataclass
class Endpoint:
    """A single API endpoint call definition."""

    host: str
    method: str
    uri: str
    body: Optional[Dict[str, Any]] = None


@dataclass
class EndpointResult:
    """Result from calling an endpoint."""

    host: str
    method: str
    uri: str
    status_code: int
    data: Any  # parsed JSON response
    raw_text: str


def load_endpoints(path: str) -> List[Endpoint]:
    """Load endpoint list from a YAML file.

    Expected YAML format:
    ```yaml
    - host: api.example.com
      method: GET
      uri: /users
    - host: api.example.com
      method: POST
      uri: /users
      body:
        name: John
        email: john@example.com
    ```
    """
    with open(path) as f:
        data = yaml.safe_load(f)

    if not data:
        return []

    endpoints: List[Endpoint] = []
    for entry in data:
        endpoints.append(
            Endpoint(
                host=entry.get("host", ""),
                method=entry.get("method", "GET").upper(),
                uri=entry.get("uri", "/"),
                body=entry.get("body"),
            )
        )
    return endpoints


def call_endpoints(
    endpoints: List[Endpoint],
    auth_configs: Dict[str, AuthConfig],
    base_url: Optional[str] = None,
) -> List[EndpointResult]:
    """Call all endpoints sequentially, collecting results.

    Returns a list of EndpointResult objects for use in the pipeline.
    """
    results: List[EndpointResult] = []

    with httpx.Client() as client:
        for ep in endpoints:
            # Determine the full URL
            if base_url:
                url = f"{base_url.rstrip('/')}/{ep.uri.lstrip('/')}"
            else:
                # Detect scheme — default to http for localhost, otherwise https
                host = ep.host
                if "localhost" in host or "127.0.0.1" in host or "0.0.0.0" in host:
                    scheme = "http"
                else:
                    scheme = "https"
                url = f"{scheme}://{host}/{ep.uri.lstrip('/')}"

            # Collect auth headers for this host
            headers: Dict[str, str] = {}
            if ep.host in auth_configs:
                headers.update(auth_configs[ep.host].get_headers(client))

            # Make the request
            method = ep.method.lower()
            body = ep.body

            try:
                if method in ("get", "delete", "head", "options"):
                    resp = client.request(method, url, headers=headers)
                else:
                    resp = client.request(method, url, headers=headers, json=body)

                resp.raise_for_status()

                # Try to parse JSON; fall back to raw text
                try:
                    data = resp.json()
                except Exception:
                    data = resp.text

                results.append(
                    EndpointResult(
                        host=ep.host,
                        method=ep.method,
                        uri=ep.uri,
                        status_code=resp.status_code,
                        data=data,
                        raw_text=resp.text,
                    )
                )
            except Exception as e:
                results.append(
                    EndpointResult(
                        host=ep.host,
                        method=ep.method,
                        uri=ep.uri,
                        status_code=0,
                        data={"error": str(e)},
                        raw_text=str(e),
                    )
                )

    return results