"""
Nexlog – Ziti Event Collector
Polls the OpenZiti Management API for audit events.
"""

import time
import logging
import requests
from datetime import datetime, timezone
from typing import Iterator, Optional

logger = logging.getLogger("nexlog.collector")


class ZitiCollector:
    def __init__(self, config: dict):
        self.base_url = config["ziti_url"].rstrip("/")
        self.username = config.get("username")
        self.password = config.get("password")
        self.api_token = config.get("api_token")
        self.verify_tls = config.get("verify_tls", True)
        self.poll_interval = config.get("poll_interval", 5)
        self._session = requests.Session()
        self._last_seen: Optional[str] = None

    def _authenticate(self) -> None:
        if self.api_token:
            self._session.headers.update({"zt-session": self.api_token})
            return
        resp = self._session.post(
            f"{self.base_url}/edge/client/v1/authenticate?method=password",
            json={"username": self.username, "password": self.password},
            verify=self.verify_tls,
            timeout=10,
        )
        resp.raise_for_status()
        token = resp.json()["data"]["token"]
        self._session.headers.update({"zt-session": token})
        logger.info("Authenticated against Ziti controller")

    def _fetch_events(self) -> list:
        params = {"limit": 500, "offset": 0}
        if self._last_seen:
            params["filter"] = f'createdAt > "{self._last_seen}"'
        resp = self._session.get(
            f"{self.base_url}/edge/management/v1/audit-log",
            params=params,
            verify=self.verify_tls,
            timeout=15,
        )
        if resp.status_code == 401:
            self._authenticate()
            return self._fetch_events()
        resp.raise_for_status()
        data = resp.json().get("data", [])
        if data:
            self._last_seen = data[0].get("createdAt")
        return data

    def stream(self) -> Iterator[dict]:
        self._authenticate()
        logger.info("Starting event stream (poll every %ds)", self.poll_interval)
        while True:
            try:
                events = self._fetch_events()
                for event in reversed(events):
                    yield event
            except requests.RequestException as exc:
                logger.error("Fetch error: %s", exc)
            time.sleep(self.poll_interval)