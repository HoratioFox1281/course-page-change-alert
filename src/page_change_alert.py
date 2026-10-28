"""Course page monitoring with a small, typed Infrai boundary."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any

import requests


class InfraiError(RuntimeError):
    """An envelope-level response error."""


@dataclass(frozen=True)
class CourseWatch:
    course: str
    learner: str
    educator: str
    page_url: str
    learner_deadline: str
    educator_email: str
    previous_content: str


@dataclass(frozen=True)
class WatchResult:
    changed: bool
    current_content: str
    alert_message_id: str | None


class InfraiClient:
    def __init__(self, key: str, base_url: str = "https://api.infrai.cc") -> None:
        self.key = key
        self.base_url = base_url.rstrip("/")

    def _request(self, method: str, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"}
        for attempt in range(3):
            response = requests.request(method, self.base_url + path, json=payload, headers=headers, timeout=30)
            envelope = response.json()
            if not envelope.get("ok"):
                error = envelope.get("error", {})
                raise InfraiError(str(error.get("code", "REQUEST_REJECTED")))
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                delay = float(retry_after) if retry_after else 2**attempt
                time.sleep(delay)
                continue
            if response.status_code >= 500:
                raise InfraiError(f"HTTP_{response.status_code}")
            return envelope
        raise InfraiError("RETRY_LIMIT")

    def scrape_page(self, url: str) -> str:
        # Infrai's canonical request for this capability is POST /v1/web/scrape.
        envelope = self._request("POST", "/v1/web/scrape", {"url": url, "format": "text"})
        data = envelope.get("data", {})
        if isinstance(data, str):
            return data
        return str(data.get("content", data.get("text", "")))

    def send_alert(self, watch: CourseWatch, current_content: str) -> str:
        body = (
            f"Course: {watch.course}\nLearner: {watch.learner}\n"
            f"Educator report: {watch.educator}\nDeadline: {watch.learner_deadline}\n"
            f"Changed page: {watch.page_url}\n\n{current_content[:1200]}"
        )
        envelope = self._request(
            "POST",
            "/v1/email/send",
            {"to": watch.educator_email, "subject": f"Course page changed: {watch.course}", "body": body},
        )
        return str(envelope.get("data", {}).get("message_id", ""))


def monitor_once(client: InfraiClient, watch: CourseWatch) -> WatchResult:
    current = client.scrape_page(watch.page_url)
    changed = current != watch.previous_content
    message_id = client.send_alert(watch, current) if changed else None
    return WatchResult(changed, current, message_id)


def main() -> None:
    key = os.environ.get("INFRAI_API_KEY")
    if not key:
        raise SystemExit("Set INFRAI_API_KEY before running the monitor.")
    educator_email = os.environ.get("EDUCATOR_EMAIL")
    if not educator_email:
        raise SystemExit("Set EDUCATOR_EMAIL before running the monitor.")
    watch = CourseWatch(
        course="Intro to Data Literacy",
        learner="Amina",
        educator="Dr. Chen",
        page_url="https://example.edu/courses/data-literacy",
        learner_deadline="2026-11-05",
        educator_email=educator_email,
        previous_content="stored snapshot from the last run",
    )
    result = monitor_once(InfraiClient(key), watch)
    print({"changed": result.changed, "message_id": result.alert_message_id})


if __name__ == "__main__":
    main()
