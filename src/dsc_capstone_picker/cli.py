from __future__ import annotations

from difflib import get_close_matches
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from dsc_capstone_picker.models import (
    CapstoneDomain,
    DOMAINS_PATH,
    PROFILE_PATH,
    Recommendation,
    StudentProfile,
    load_domains,
    load_profile,
    save_domains,
    save_profile,
)
from dsc_capstone_picker.export import EXPORT_FORMATS, export_recommendations
from dsc_capstone_picker.llm import (
    MissingOpenAIAPIKeyError,
    add_llm_explanations,
)
from dsc_capstone_picker.rank import parse_profile_file, rank_domains
from dsc_capstone_picker.resume import merge_profiles, profile_from_resume
from dsc_capstone_picker.scrape import fetch_domains
from dsc_capstone_picker.search import find_domain, search_domains

app = typer.Typer(help="Explore, compare, and rank UCSD DSC capstone domains.")
profile_app = typer.Typer(help="Create and inspect a student preference profile.")
app.add_typer(profile_app, name="profile")
console = Console()
CACHE_MISSING_MESSAGE = "No cached capstone domains found. Run: dsc-capstone-picker fetch"
PROJECT_STYLES = ["research", "applied", "systems", "product", "theory", "open-ended"]
MENTOR_PREFERENCES = ["structured", "hands-off", "collaborative", "research-heavy"]
AVOID_OPTIONS = [
    "heavy theory",
    "heavy systems",
    "GPU-heavy",
    "lots of reading",
    "unclear deliverables",
]
NEUTRAL_CHOICES = {"", "any", "no preference", "none", "n/a", "na"}


@app.command()
def fetch() -> None:
    """Fetch and cache capstone domain information."""
    console.print("Fetching capstone data...")
    domains = fetch_domains()
    save_domains(domains)
    console.print(f"Saved {len(domains)} domains to {DOMAINS_PATH}.")


@app.command()
def list() -> None:
    """List available capstone domains."""
    domains = _load_cached_domains()
    if domains is None:
        return

    table = _domains_table(domains)
    console.print(table)


@app.command()
def show(title: str) -> None:
    """Show details for one capstone domain."""
    domains = _load_cached_domains()
    if domains is None:
        return

    domain = find_domain(domains, title)
    if domain is None:
        console.print(f'No domain found matching "{title}".')
        return

    console.print(_domain_panel(domain))


@app.command()
def search(query: str) -> None:
    """Search capstone domains by keyword."""
    domains = _load_cached_domains()
    if domains is None:
        return

    matches = search_domains(domains, query)
    if not matches:
        console.print(f'No domains found matching "{query}".')
        return

    console.print(_domains_table(matches, title=f'Search results for "{query}"'))


@app.command()
def recommend(
    profile: str | None = typer.Option(None, "--profile", "-p", help="Path to a text or JSON profile."),
    resume: str | None = typer.Option(None, "--resume", "-r", help="Path to a plain-text resume."),
    top: int = typer.Option(10, "--top", "-n", help="Number of recommendations to show."),
    llm: bool = typer.Option(False, "--llm", help="Add optional OpenAI-powered explanations."),
) -> None:
    """Recommend capstone domains based on a student profile."""
    domains = _load_cached_domains()
    if domains is None:
        return

    recommendations = _rank_from_inputs(domains, profile=profile, resume=resume, top=top)
    if recommendations is None:
        return
    if llm:
        student_profile = _profile_from_inputs(profile=profile, resume=resume)
        if student_profile is None:
            return
        try:
            recommendations = add_llm_explanations(recommendations, student_profile)
        except MissingOpenAIAPIKeyError as error:
            console.print(str(error))
            return
    console.print(_recommendations_table(recommendations))


@app.command("export")
def export_command(
    profile: str | None = typer.Option(None, "--profile", "-p", help="Path to a text or JSON profile."),
    resume: str | None = typer.Option(None, "--resume", "-r", help="Path to a resume file."),
    top: int = typer.Option(10, "--top", "-n", help="Number of recommendations to export."),
    output: Path = typer.Option(..., "--output", "-o", help="Output file path."),
    export_format: str = typer.Option("csv", "--format", "-f", help="Export format: csv or txt."),
) -> None:
    """Export ranked capstone recommendations."""
    if export_format.casefold() not in EXPORT_FORMATS:
        console.print("Unsupported export format. Use csv or txt.")
        return

    domains = _load_cached_domains()
    if domains is None:
        return

    recommendations = _rank_from_inputs(domains, profile=profile, resume=resume, top=top)
    if recommendations is None:
        return

    export_recommendations(recommendations, output, export_format=export_format)
    console.print(f"Exported {len(recommendations)} recommendations to {output}.")


@profile_app.command("create")
def create_profile(
    output: Path = typer.Option(PROFILE_PATH, "--output", "-o", help="Where to save the JSON profile."),
) -> None:
    """Create a student preference profile interactively."""
    interests = _prompt_list(
        "Topic interests",
        "comma-separated; examples: large language models, machine learning, "
        "climate, healthcare, education technology, data visualization",
    )
    skills = _prompt_list(
        "Technical skills",
        "comma-separated; examples: Python, pandas, PyTorch, SQL, web scraping, "
        "data visualization, Git",
    )
    career_goals = _prompt_list(
        "Career goals",
        "comma-separated; examples: data scientist, machine learning engineer, "
        "applied AI, health tech, product analytics",
    )
    project_styles = _prompt_choice_list(
        "Preferred project style",
        PROJECT_STYLES,
        "choose any number, comma-separated, or type any: research, applied, "
        "systems, product, theory, open-ended",
    )
    mentor_preferences = _prompt_choice_list(
        "Mentor preference",
        MENTOR_PREFERENCES,
        "choose any number, comma-separated, or type any: structured, hands-off, "
        "collaborative, research-heavy",
    )
    avoid = _prompt_choice_list(
        "Things to avoid",
        AVOID_OPTIONS,
        "choose any number, comma-separated, or type none: heavy theory, heavy systems, "
        "GPU-heavy, lots of reading, unclear deliverables",
    )

    student_profile = StudentProfile(
        interests=interests,
        skills=skills,
        preferences=[*project_styles, *mentor_preferences],
        avoid=avoid,
        career_goals=career_goals,
        raw_text=_profile_raw_text(
            interests=interests,
            skills=skills,
            preferences=[*project_styles, *mentor_preferences],
            avoid=avoid,
            career_goals=career_goals,
        ),
    )
    save_profile(student_profile, output)
    console.print(f"Saved profile to {output}.")


@profile_app.command("show")
def show_profile(
    path: Path = typer.Option(PROFILE_PATH, "--profile", "-p", help="Path to a JSON profile."),
) -> None:
    """Display the saved student preference profile."""
    if not path.exists():
        console.print(f"No saved profile found at {path}. Run: dsc-capstone-picker profile create")
        return

    student_profile = load_profile(path)
    console.print(_profile_panel(student_profile, title=str(path)))


def _load_cached_domains() -> list[CapstoneDomain] | None:
    if not DOMAINS_PATH.exists():
        console.print(CACHE_MISSING_MESSAGE)
        return None
    return load_domains()


def _rank_from_inputs(
    domains: list[CapstoneDomain],
    profile: str | None,
    resume: str | None,
    top: int,
) -> list[Recommendation] | None:
    if profile is None and resume is None:
        console.print("Provide --profile, --resume, or both.")
        return None

    student_profile = _profile_from_inputs(profile=profile, resume=resume)
    if student_profile is None:
        return None
    return rank_domains(domains, student_profile, top=top)


def _profile_from_inputs(
    profile: str | None,
    resume: str | None,
) -> StudentProfile | None:
    if profile is None and resume is None:
        console.print("Provide --profile, --resume, or both.")
        return None

    questionnaire_profile = parse_profile_file(profile) if profile is not None else None
    try:
        resume_profile = profile_from_resume(resume) if resume is not None else None
    except ValueError as error:
        console.print(str(error))
        return None

    return merge_profiles(questionnaire_profile, resume_profile)


def _domains_table(domains: list[CapstoneDomain], title: str = "Capstone Domains") -> Table:
    table = Table(title=title)
    table.add_column("Title", overflow="fold")
    table.add_column("Mentor")
    table.add_column("Section")
    table.add_column("Seats", justify="right")
    table.add_column("Meeting Time")
    table.add_column("Industry Partner")
    table.add_column("Topic Area")

    for domain in domains:
        table.add_row(
            domain.title,
            domain.mentor or "",
            domain.section or "",
            str(domain.seats) if domain.seats is not None else "",
            domain.meeting_time or "",
            "Yes" if domain.industry_partner else "No",
            domain.topic_area or "",
        )

    return table


def _recommendations_table(recommendations: list[Recommendation]) -> Table:
    table = Table(title="Recommendations")
    has_llm_explanations = any(recommendation.llm_explanation for recommendation in recommendations)
    table.add_column("Rank", justify="right")
    table.add_column("Title", overflow="fold")
    table.add_column("Score", justify="right")
    table.add_column("Breakdown", overflow="fold")
    table.add_column("Reasons", overflow="fold")
    table.add_column("Concerns", overflow="fold")
    if has_llm_explanations:
        table.add_column("LLM Explanation", overflow="fold")

    for index, recommendation in enumerate(recommendations, start=1):
        row = [
            str(index),
            recommendation.domain.title,
            f"{recommendation.score:.2f}",
            _format_score_breakdown(recommendation.score_breakdown),
            "\n".join(recommendation.reasons),
            "\n".join(recommendation.concerns),
        ]
        if has_llm_explanations:
            row.append(recommendation.llm_explanation)
        table.add_row(*row)

    return table


def _domain_panel(domain: CapstoneDomain) -> Panel:
    lines = [
        f"[bold]Mentor:[/bold] {domain.mentor or 'Unknown'}",
        f"[bold]Section:[/bold] {domain.section or 'Unknown'}",
        f"[bold]Seats:[/bold] {domain.seats if domain.seats is not None else 'Unknown'}",
        f"[bold]Meeting Time:[/bold] {domain.meeting_time or 'Unknown'}",
        f"[bold]Industry Partner:[/bold] {'Yes' if domain.industry_partner else 'No'}",
        f"[bold]Topic Area:[/bold] {domain.topic_area or 'Unknown'}",
    ]

    sections = [
        ("Description", domain.description),
        ("Prerequisites", domain.prerequisites),
        ("Mentor Style", domain.mentor_style),
        ("Summer Tasks", domain.summer_tasks),
        ("Previous Projects", domain.previous_projects),
        ("URL", domain.url or ""),
    ]
    for label, value in sections:
        if value:
            lines.extend(["", f"[bold]{label}:[/bold]", value])

    return Panel("\n".join(lines), title=domain.title, expand=False)


def _profile_panel(profile: StudentProfile, title: str = "Student Profile") -> Panel:
    sections = [
        ("Interests", profile.interests),
        ("Skills", profile.skills),
        ("Preferences", profile.preferences),
        ("Avoid", profile.avoid),
        ("Career Goals", profile.career_goals),
    ]
    lines = []
    for label, values in sections:
        lines.append(f"[bold]{label}:[/bold] {_format_list(values)}")
    if profile.resume_text:
        lines.extend(["", "[bold]Resume Text:[/bold]", profile.resume_text])
    return Panel("\n".join(lines), title=title, expand=False)


def _prompt_list(label: str, guidance: str) -> list[str]:
    value = typer.prompt(f"{label} ({guidance})", default="")
    return _split_prompt_items(value)


def _prompt_choice_list(label: str, choices: list[str], examples: str) -> list[str]:
    value = typer.prompt(f"{label} ({examples})", default="")
    items = _split_prompt_items(value)
    if any(item.casefold() in NEUTRAL_CHOICES for item in items):
        return []
    return [_canonical_choice(item, choices) for item in items]


def _split_prompt_items(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _canonical_choice(value: str, choices: list[str]) -> str:
    normalized_choices = {choice.casefold(): choice for choice in choices}
    normalized_value = value.casefold().strip()
    if normalized_value in normalized_choices:
        return normalized_choices[normalized_value]

    matches = get_close_matches(normalized_value, normalized_choices, n=1, cutoff=0.72)
    if matches:
        return normalized_choices[matches[0]]
    return value.strip()


def _profile_raw_text(
    interests: list[str],
    skills: list[str],
    preferences: list[str],
    avoid: list[str],
    career_goals: list[str],
) -> str:
    sections = {
        "Interests": interests,
        "Skills": skills,
        "Preferences": preferences,
        "Avoid": avoid,
        "Career Goals": career_goals,
    }
    lines = []
    for heading, values in sections.items():
        lines.append(f"{heading}:")
        lines.extend(f"- {value}" for value in values)
        lines.append("")
    return "\n".join(lines).strip()


def _format_list(values: list[str]) -> str:
    if not values:
        return "None"
    return ", ".join(values)


def _format_score_breakdown(score_breakdown: dict[str, float]) -> str:
    if not score_breakdown:
        return "0"
    return "\n".join(
        f"{key.replace('_', ' ')}: {value:+.2f}"
        for key, value in score_breakdown.items()
    )


if __name__ == "__main__":
    app()
