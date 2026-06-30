import time
from datetime import datetime, timedelta, timezone

import requests


class GitHubClient:
    BASE_URL = "https://api.github.com"

    def __init__(self, token: str | None = None) -> None:
        self._token = token
        self._session = requests.Session()
        self._session.headers.update({"Accept": "application/vnd.github+json"})
        if self._token:
            self._session.headers.update({"Authorization": f"Bearer {self._token}"})

    @property
    def token(self) -> str | None:
        return self._token

    @token.setter
    def token(self, value: str | None) -> None:
        self._token = value
        if value:
            self._session.headers.update({"Authorization": f"Bearer {value}"})
        else:
            self._session.headers.pop("Authorization", None)

    def _request(self, url: str, params: dict | None = None) -> requests.Response:
        for attempt in range(2):
            response = self._session.get(url, params=params, timeout=30)
            if response.status_code == 403:
                raise PermissionError(
                    "GitHub API rate limit exceeded. Add GITHUB_TOKEN to your .env to increase limits."
                )
            if response.status_code == 404:
                raise ValueError(f"Resource not found: {url}")
            if response.status_code >= 500 and attempt == 0:
                time.sleep(2)
                continue
            response.raise_for_status()
            return response
        response.raise_for_status()
        return response

    def get_user(self, username: str) -> dict:
        return self._request(f"{self.BASE_URL}/users/{username}").json()

    def get_repos(self, username: str) -> list[dict]:
        repos: list[dict] = []
        page = 1
        while True:
            batch = self._request(
                f"{self.BASE_URL}/users/{username}/repos",
                params={"type": "public", "per_page": 100, "page": page},
            ).json()
            if not batch:
                break
            repos.extend(batch)
            if len(batch) < 100:
                break
            page += 1
        return repos

    def get_languages(self, username: str, repo_name: str) -> dict:
        try:
            return self._request(
                f"{self.BASE_URL}/repos/{username}/{repo_name}/languages"
            ).json()
        except Exception:
            return {}

    def get_commits(
        self, username: str, repo_name: str, since_days: int = 365
    ) -> list[dict]:
        since = (datetime.now(timezone.utc) - timedelta(days=since_days)).isoformat()
        commits: list[dict] = []
        page = 1
        while True:
            try:
                batch = self._request(
                    f"{self.BASE_URL}/repos/{username}/{repo_name}/commits",
                    params={
                        "author": username,
                        "since": since,
                        "per_page": 100,
                        "page": page,
                    },
                ).json()
            except Exception:
                break
            if not isinstance(batch, list) or not batch:
                break
            commits.extend(batch)
            if len(batch) < 100:
                break
            page += 1
        return commits
