"""HTTP transport shared by the restoration CLI and stdio MCP adapter.

Domain validation and mutations belong to the running project server. This
client deliberately has no local analysis cache or alternate mutation path.
"""

from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen


class RestorationClientError(RuntimeError):
    """A transport or domain refusal, preserving the server response."""

    def __init__(self, payload: dict[str, object], status: int = 0) -> None:
        self.payload = payload
        self.status = status
        super().__init__(str(payload.get("error", payload)))


class RestorationClient:
    def __init__(
        self, base_url: str = "http://127.0.0.1:8123", timeout: float = 180
    ) -> None:
        parsed = urlparse(base_url)
        if parsed.scheme != "http" or parsed.hostname not in {
            "127.0.0.1",
            "localhost",
            "::1",
        }:
            raise ValueError(
                "Restoration adapters connect only to a local HTTP project server"
            )
        if (
            parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
            or parsed.path not in {"", "/"}
        ):
            raise ValueError(
                "Use the local server origin without credentials or a path"
            )
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._contract: str | None = None

    def _request(
        self, path: str, body: dict[str, object] | None = None
    ) -> dict[str, object]:
        headers = {"Accept": "application/json"}
        if self._contract is not None:
            headers["X-Amiga-Web-App-Contract"] = self._contract
        data = None if body is None else json.dumps(body).encode("utf-8")
        if data is not None:
            headers["Content-Type"] = "application/json"
        request = Request(self.base_url + path, data=data, headers=headers)
        try:
            with urlopen(request, timeout=self.timeout) as response:
                payload = json.load(response)
        except HTTPError as exc:
            try:
                payload = json.load(exc)
            except ValueError, OSError:
                payload = {"error": str(exc)}
            raise RestorationClientError(payload, exc.code) from exc
        except (URLError, TimeoutError) as exc:
            raise RestorationClientError(
                {"error": f"Project server unavailable: {exc}"}
            ) from exc
        if not isinstance(payload, dict):
            raise RestorationClientError(
                {"error": "Expected a JSON object from project server"}
            )
        if payload.get("ok") is False:
            raise RestorationClientError(payload)
        return payload

    def call(
        self, project: str, operation: str, **parameters: object
    ) -> dict[str, object]:
        if self._contract is None:
            contract = self._request("/api/app-contract")
            data = contract.get("data", {})
            if not isinstance(data, dict):
                raise RestorationClientError({"error": "Invalid server contract"})
            self._contract = str(data["web_app_contract_version"])
        response = self._request(
            f"/api/projects/{quote(project, safe='')}/restoration",
            {"operation": operation, **parameters},
        )
        data = response.get("data")
        if not isinstance(data, dict):
            raise RestorationClientError({"error": "Invalid restoration response"})
        return data
