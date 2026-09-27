from __future__ import annotations

import time

import requests

USER_AGENT = "agent-boards/0.1 (+https://github.com/Nissan-Dutta/Grok-Bot-Setup)"


class FetchError(RuntimeError):
    pass


_session: requests.Session | None = None


def session() -> requests.Session:
    global _session
    if _session is None:
        _session = requests.Session()
        _session.headers["User-Agent"] = USER_AGENT
    return _session


def get_json(url: str, *, params: dict | None = None, timeout: float = 30, retries: int = 2):
    """GET a JSON document. Retries 5xx and network errors; a 404 raises at once."""
    last: Exception | None = None
    for attempt in range(retries + 1):
        try:
            resp = session().get(url, params=params, timeout=timeout)
            if resp.status_code == 404:
                raise FetchError(f"404 {url}")
            if resp.status_code >= 500 or resp.status_code == 429:
                raise requests.HTTPError(f"{resp.status_code} {url}")
            resp.raise_for_status()
            return resp.json()
        except FetchError:
            raise
        except (requests.RequestException, ValueError) as exc:
            last = exc
            if attempt < retries:
                time.sleep(2 ** attempt)
    raise FetchError(str(last))
