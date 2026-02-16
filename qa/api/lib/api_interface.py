from __future__ import annotations

from dataclasses import dataclass

import requests


@dataclass
class ApiInterface:
    base_url: str
    verify_ssl: bool = True
    timeout: int = 10

    def get(self, path: str) -> requests.Response:
        return requests.get(
            f"{self.base_url.rstrip('/')}{path}",
            timeout=self.timeout,
            verify=self.verify_ssl,
        )
