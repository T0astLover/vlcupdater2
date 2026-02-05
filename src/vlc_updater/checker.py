from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from html import unescape
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DEFAULT_SOURCE_URL = "https://www.videolan.org/vlc/"
VERSION_REGEX = re.compile(r"\b(\d+\.\d+(?:\.\d+){0,2})\b")


@dataclass(slots=True)
class CheckResult:
    created_at: str
    product: str
    installed_version: str | None
    latest_version: str | None
    update_available: int | None
    source_url: str
    status: str
    error_message: str | None

    def as_dict(self) -> dict[str, str | int | None]:
        return {
            "created_at": self.created_at,
            "product": self.product,
            "installed_version": self.installed_version,
            "latest_version": self.latest_version,
            "update_available": self.update_available,
            "source_url": self.source_url,
            "status": self.status,
            "error_message": self.error_message,
        }


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_version(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in version.split("."))


def _extract_version(text: str) -> str | None:
    text = unescape(text)

    # Prioriter tekst med VLC rundt versjonstallet.
    candidates = []
    for match in VERSION_REGEX.finditer(text):
        value = match.group(1)
        start = max(0, match.start() - 40)
        end = min(len(text), match.end() + 40)
        context = text[start:end].lower()
        score = 1
        if "vlc" in context:
            score += 2
        if "media player" in context or "release" in context:
            score += 1
        candidates.append((score, _normalize_version(value), value))

    if not candidates:
        return None

    candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return candidates[0][2]


def fetch_latest_version(source_url: str = DEFAULT_SOURCE_URL, timeout: int = 15) -> str:
    request = Request(source_url, headers={"User-Agent": "vlc-updater/0.1"})
    with urlopen(request, timeout=timeout) as response:  # nosec B310
        body = response.read().decode("utf-8", errors="replace")

    version = _extract_version(body)
    if not version:
        raise ValueError("Fant ingen versjon i svaret fra kilde-URL.")
    return version


def compare_versions(installed_version: str | None, latest_version: str | None) -> int | None:
    if not installed_version or not latest_version:
        return None
    return int(_normalize_version(latest_version) > _normalize_version(installed_version))


def run_check(installed_version: str | None, source_url: str = DEFAULT_SOURCE_URL) -> CheckResult:
    created_at = _now_iso()
    try:
        latest = fetch_latest_version(source_url)
        update_available = compare_versions(installed_version, latest)
        return CheckResult(
            created_at=created_at,
            product="vlc",
            installed_version=installed_version,
            latest_version=latest,
            update_available=update_available,
            source_url=source_url,
            status="ok",
            error_message=None,
        )
    except (HTTPError, URLError, TimeoutError, ValueError) as exc:
        return CheckResult(
            created_at=created_at,
            product="vlc",
            installed_version=installed_version,
            latest_version=None,
            update_available=None,
            source_url=source_url,
            status="error",
            error_message=str(exc),
        )


def format_row_json(row: dict[str, str | int | None]) -> str:
    return json.dumps(row, ensure_ascii=False, indent=2)
