from collections import defaultdict
from datetime import datetime, timezone


def compute_language_distribution(repos_languages: list[dict]) -> dict[str, float]:
    totals: dict[str, int] = defaultdict(int)
    for lang_map in repos_languages:
        for lang, bytes_count in lang_map.items():
            totals[lang] += bytes_count
    grand_total = sum(totals.values())
    if grand_total == 0:
        return {}
    return {
        lang: round(bytes_count / grand_total * 100, 2)
        for lang, bytes_count in sorted(totals.items(), key=lambda x: x[1], reverse=True)
    }


def compute_activity_score(repo: dict) -> float:
    stars: int = repo.get("stargazers_count", 0)
    forks: int = repo.get("forks_count", 0)
    updated_at: str | None = repo.get("updated_at")
    recency_bonus = 0.0
    if updated_at:
        try:
            updated = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
            days_since = (datetime.now(timezone.utc) - updated).days
            if days_since < 90:
                recency_bonus = 10.0
        except ValueError:
            pass
    return stars * 2.0 + forks + recency_bonus


def compute_top_repos(repos: list[dict], n: int = 5) -> list[dict]:
    scored = sorted(repos, key=compute_activity_score, reverse=True)
    return scored[:n]


def compute_commit_frequency(commits_by_repo: dict[str, list]) -> dict[str, int]:
    """Returns date (YYYY-MM-DD) -> commit count for building the contribution grid."""
    daily: dict[str, int] = defaultdict(int)
    for commits in commits_by_repo.values():
        for commit in commits:
            try:
                date_str = (
                    commit.get("commit", {})
                    .get("author", {})
                    .get("date", "")
                )
                if date_str:
                    dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                    daily[dt.strftime("%Y-%m-%d")] += 1
            except (ValueError, AttributeError):
                continue
    return dict(daily)


def _compute_monthly_counts(commits_by_repo: dict[str, list]) -> dict[str, int]:
    monthly: dict[str, int] = defaultdict(int)
    for commits in commits_by_repo.values():
        for commit in commits:
            try:
                date_str = (
                    commit.get("commit", {})
                    .get("author", {})
                    .get("date", "")
                )
                if date_str:
                    dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                    monthly[dt.strftime("%Y-%m")] += 1
            except (ValueError, AttributeError):
                continue
    return dict(monthly)


def compute_summary_stats(repos: list[dict], commits_by_repo: dict) -> dict:
    total_repos = len(repos)
    total_stars = sum(r.get("stargazers_count", 0) for r in repos)
    total_forks = sum(r.get("forks_count", 0) for r in repos)

    all_commits: list = []
    for commits in commits_by_repo.values():
        all_commits.extend(commits)
    total_commits_year = len(all_commits)

    monthly = _compute_monthly_counts(commits_by_repo)
    most_active_month = max(monthly, key=lambda k: monthly[k]) if monthly else None

    lang_bytes: dict[str, int] = defaultdict(int)
    for repo in repos:
        lang = repo.get("language")
        if lang:
            lang_bytes[lang] += 1
    primary_language = max(lang_bytes, key=lambda k: lang_bytes[k]) if lang_bytes else None

    return {
        "total_repos": total_repos,
        "total_stars": total_stars,
        "total_forks": total_forks,
        "total_commits_year": total_commits_year,
        "most_active_month": most_active_month,
        "primary_language": primary_language,
    }
