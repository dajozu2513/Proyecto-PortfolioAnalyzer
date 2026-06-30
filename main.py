import argparse
import os
import sys

from dotenv import load_dotenv
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from analyzer.github_client import GitHubClient
from analyzer.metrics import (
    compute_commit_frequency,
    compute_language_distribution,
    compute_summary_stats,
    compute_top_repos,
)
from report.generator import ReportGenerator

load_dotenv()
console = Console()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a GitHub portfolio report."
    )
    parser.add_argument("--username", required=True, help="GitHub username to analyze")
    parser.add_argument(
        "--output",
        default="./output/report.html",
        help="Output path for the HTML report (default: ./output/report.html)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    github_token = os.getenv("GITHUB_TOKEN", "").strip() or None
    client = GitHubClient(token=github_token)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:

        # ── 1. Fetch user profile ──
        task = progress.add_task("Fetching user profile…", total=None)
        try:
            user_data = client.get_user(args.username)
        except ValueError:
            console.print(
                f"[bold red]Error:[/bold red] GitHub user '{args.username}' not found."
            )
            sys.exit(1)
        except PermissionError as exc:
            console.print(f"[bold red]Error:[/bold red] {exc}")
            sys.exit(1)
        progress.update(task, description="[green]✓[/green] User profile fetched")

        # ── 2. Fetch repos ──
        progress.update(task, description="Fetching repositories…")
        repos = client.get_repos(args.username)

        # Filter the GitHub profile repo (same name as username — not a real project)
        repos = [r for r in repos if r["name"].lower() != args.username.lower()]

        if not repos:
            console.print(
                f"[yellow]Warning:[/yellow] No public repositories found for '{args.username}'."
            )
        progress.update(task, description=f"[green]✓[/green] {len(repos)} repositories fetched")

        # ── 3. Fetch languages per repo ──
        progress.update(task, description="Fetching language data…")
        repos_languages: list[dict] = []
        for repo in repos:
            langs = client.get_languages(args.username, repo["name"])
            repos_languages.append(langs)
        progress.update(task, description="[green]✓[/green] Language data fetched")

        # ── 4. Fetch commits (top 10 repos by stars to stay under rate limits) ──
        progress.update(task, description="Fetching commit history…")
        sorted_by_stars = sorted(repos, key=lambda r: r.get("stargazers_count", 0), reverse=True)
        commits_by_repo: dict[str, list] = {}
        for repo in sorted_by_stars[:10]:
            commits = client.get_commits(args.username, repo["name"])
            if commits:
                commits_by_repo[repo["name"]] = commits
        progress.update(task, description="[green]✓[/green] Commit history fetched")

        # ── 5. Compute metrics ──
        progress.update(task, description="Computing metrics…")
        language_distribution = compute_language_distribution(repos_languages)
        top_repos = compute_top_repos(repos, n=5)
        commit_frequency = compute_commit_frequency(commits_by_repo)
        summary_stats = compute_summary_stats(repos, commits_by_repo)
        progress.update(task, description="[green]✓[/green] Metrics computed")

        # ── 6. Render HTML report ──
        progress.update(task, description="Rendering HTML report…")
        generator = ReportGenerator()
        output_path = generator.generate(
            username=args.username,
            user_data=user_data,
            summary_stats=summary_stats,
            language_distribution=language_distribution,
            top_repos=top_repos,
            commit_frequency=commit_frequency,
            output_path=args.output,
        )
        progress.update(task, description="[green]✓[/green] Report rendered")

    console.print()
    console.print(f"[bold green]Report generated:[/bold green] {output_path}")
    console.print(f"[dim]Open in a browser to view your portfolio.[/dim]")


if __name__ == "__main__":
    main()
