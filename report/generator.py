import math
import os
from datetime import date
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

_MONTH_ES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun",
             "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
_MONTH_EN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
             "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


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


def _build_monthly_bars(daily_commits: dict[str, int]) -> list[dict]:
    """
    Returns 12 dicts (oldest → newest month) with bar chart data.
    Each dict: year, month, key (YYYY-MM), count, height_pct, is_zero, month_es, month_en.
    """
    today = date.today()

    # Last 12 calendar months in chronological order
    months: list[tuple[int, int]] = []
    for i in range(11, -1, -1):
        m = today.month - i
        y = today.year
        if m <= 0:
            m += 12
            y -= 1
        months.append((y, m))

    # Aggregate daily commits into monthly buckets
    monthly_counts: dict[str, int] = {}
    for date_str, count in daily_commits.items():
        key = date_str[:7]  # YYYY-MM
        monthly_counts[key] = monthly_counts.get(key, 0) + count

    bars: list[dict] = []
    for y, m in months:
        key = f"{y:04d}-{m:02d}"
        count = monthly_counts.get(key, 0)
        bars.append({"year": y, "month": m, "key": key, "count": count})

    max_count = max((b["count"] for b in bars), default=0)
    if max_count == 0:
        max_count = 1  # avoid division by zero

    for bar in bars:
        bar["height_pct"] = round(bar["count"] / max_count * 100, 1)
        bar["is_zero"] = bar["count"] == 0
        bar["month_es"] = _MONTH_ES[bar["month"] - 1]
        bar["month_en"] = _MONTH_EN[bar["month"] - 1]

    return bars


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
        monthly_bars = _build_monthly_bars(commit_frequency)

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
            monthly_bars=monthly_bars,
            primary_lang_color=primary_lang_color,
        )

        output_path = os.path.abspath(output_path)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)

        return output_path
