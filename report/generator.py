import math
import os
from datetime import date, timedelta
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

_LINGUIST: dict[str, str] = {
    "JavaScript": "#f1e05a",
    "TypeScript": "#3178c6",
    "Python": "#3572A5",
    "Java": "#b07219",
    "C#": "#178600",
    "HTML": "#e34c26",
    "CSS": "#563d7c",
    "Go": "#00ADD8",
    "Rust": "#dea584",
    "Ruby": "#701516",
    "PHP": "#4F5D95",
    "Swift": "#F05138",
    "Kotlin": "#A97BFF",
    "C++": "#f34b7d",
    "C": "#555555",
    "Shell": "#89e051",
    "Vue": "#41b883",
    "Dart": "#00B4AB",
    "Scala": "#c22d40",
    "R": "#198CE7",
    "SCSS": "#c6538c",
    "Sass": "#a53b70",
    "Jupyter Notebook": "#DA5B0B",
    "Dockerfile": "#384d54",
    "Makefile": "#427819",
    "PowerShell": "#012456",
    "Lua": "#000080",
    "Haskell": "#5e5086",
    "Elixir": "#6e4a7e",
    "Clojure": "#db5855",
}

_FALLBACK_COLORS = [
    "#8b949e", "#6e7681", "#58a6ff", "#3fb950", "#d29922",
    "#f78166", "#bc8cff", "#79c0ff", "#56d364", "#ffa657",
]

_DONUT_R = 70.0
_DONUT_C = 2 * math.pi * _DONUT_R  # ≈ 439.82


def _build_lang_color_map(language_distribution: dict[str, float]) -> dict[str, str]:
    return {
        lang: _LINGUIST.get(lang, _FALLBACK_COLORS[i % len(_FALLBACK_COLORS)])
        for i, lang in enumerate(language_distribution.keys())
    }


def _build_donut_segments(
    language_distribution: dict[str, float],
    lang_color_map: dict[str, str],
) -> list[dict]:
    segments: list[dict] = []
    cumulative = 0.0
    for lang, pct in list(language_distribution.items())[:8]:
        length = pct / 100.0 * _DONUT_C
        segments.append(
            {
                "lang": lang,
                "pct": pct,
                "color": lang_color_map.get(lang, "#8b949e"),
                "dasharray": f"{length:.2f} {_DONUT_C:.2f}",
                "dashoffset": f"{-cumulative:.2f}",
            }
        )
        cumulative += length
    return segments


def _build_contrib_grid(
    daily_commits: dict[str, int],
) -> tuple[list[list], list[str]]:
    """
    Returns (weeks, month_labels).
    weeks: 52 items, each a list of 7 day-dicts (Sun→Sat) or None for future days.
    month_labels: 52 strings — abbreviated month name at first column of each month, else "".
    """
    today = date.today()
    days_since_sunday = (today.weekday() + 1) % 7
    current_week_sunday = today - timedelta(days=days_since_sunday)
    start_sunday = current_week_sunday - timedelta(weeks=51)

    max_count = max(daily_commits.values()) if daily_commits else 1

    weeks: list[list] = []
    month_labels: list[str] = []
    prev_month: str | None = None

    for week_idx in range(52):
        week_start = start_sunday + timedelta(weeks=week_idx)
        month_abbr = week_start.strftime("%b")
        month_labels.append(month_abbr if month_abbr != prev_month else "")
        prev_month = month_abbr

        week: list = []
        for day_offset in range(7):
            d = week_start + timedelta(days=day_offset)
            if d > today:
                week.append(None)
            else:
                count = daily_commits.get(d.isoformat(), 0)
                ratio = count / max_count if max_count > 0 and count > 0 else 0
                if count == 0:
                    level = 0
                elif ratio < 0.25:
                    level = 1
                elif ratio < 0.50:
                    level = 2
                elif ratio < 0.75:
                    level = 3
                else:
                    level = 4
                week.append({"date": d.isoformat(), "count": count, "level": level})
        weeks.append(week)

    return weeks, month_labels


class ReportGenerator:
    def __init__(self) -> None:
        templates_dir = Path(__file__).parent / "templates"
        self._env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            autoescape=False,
        )

    def generate(
        self,
        username: str,
        user_data: dict,
        summary_stats: dict,
        language_distribution: dict,
        top_repos: list[dict],
        commit_frequency: dict[str, int],
        output_path: str,
    ) -> str:
        template = self._env.get_template("report.html")

        lang_color_map = _build_lang_color_map(language_distribution)
        donut_segments = _build_donut_segments(language_distribution, lang_color_map)
        contrib_weeks, contrib_month_labels = _build_contrib_grid(commit_frequency)

        # Primary language color for JS drop-shadow
        primary_lang_color = lang_color_map.get(
            summary_stats.get("primary_language", ""), "#8b949e"
        )

        html = template.render(
            username=username,
            user=user_data,
            stats=summary_stats,
            language_distribution=language_distribution,
            lang_color_map=lang_color_map,
            donut_segments=donut_segments,
            donut_c=round(_DONUT_C, 2),
            top_repos=top_repos,
            contrib_weeks=contrib_weeks,
            contrib_month_labels=contrib_month_labels,
            primary_lang_color=primary_lang_color,
        )

        output_path = os.path.abspath(output_path)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)

        return output_path
