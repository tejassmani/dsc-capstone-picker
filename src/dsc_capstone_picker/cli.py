from __future__ import annotations

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from dsc_capstone_picker.models import (
    CapstoneDomain,
    DOMAINS_PATH,
    Recommendation,
    load_domains,
    save_domains,
)
from dsc_capstone_picker.rank import parse_profile_file, rank_domains
from dsc_capstone_picker.scrape import fetch_domains
from dsc_capstone_picker.search import find_domain, search_domains

app = typer.Typer(help="Explore, compare, and rank UCSD DSC capstone domains.")
console = Console()
CACHE_MISSING_MESSAGE = "No cached capstone domains found. Run: dsc-capstone-picker fetch"


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
    profile: str = typer.Option(..., "--profile", "-p", help="Path to a plain-text profile."),
    top: int = typer.Option(10, "--top", "-n", help="Number of recommendations to show."),
) -> None:
    """Recommend capstone domains based on a student profile."""
    domains = _load_cached_domains()
    if domains is None:
        return

    student_profile = parse_profile_file(profile)
    recommendations = rank_domains(domains, student_profile, top=top)
    console.print(_recommendations_table(recommendations))

def _load_cached_domains() -> list[CapstoneDomain] | None:
    if not DOMAINS_PATH.exists():
        console.print(CACHE_MISSING_MESSAGE)
        return None
    return load_domains()


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
    table.add_column("Rank", justify="right")
    table.add_column("Title", overflow="fold")
    table.add_column("Score", justify="right")
    table.add_column("Reasons", overflow="fold")
    table.add_column("Concerns", overflow="fold")

    for index, recommendation in enumerate(recommendations, start=1):
        table.add_row(
            str(index),
            recommendation.domain.title,
            f"{recommendation.score:.2f}",
            "\n".join(recommendation.reasons),
            "\n".join(recommendation.concerns),
        )

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


if __name__ == "__main__":
    app()
