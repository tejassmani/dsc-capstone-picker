import typer
from pathlib import Path
from rich.console import Console

app = typer.Typer(help="Explore, compare, and rank UCSD DSC capstone domains.")
console = Console()
DOMAINS_PATH = Path("domains.json")


@app.command()
def fetch() -> None:
    """Fetch and cache capstone domain information."""
    console.print("Fetching capstone data...")


@app.command()
def list() -> None:
    """List available capstone domains."""
    if not DOMAINS_PATH.exists():
        console.print("No cached capstone domains found yet. Run fetch after data support is added.")
        return

    console.print("Listing capstone domains...")


@app.command()
def search(query: str) -> None:
    """Search capstone domains by keyword."""
    console.print(f"Searching for: {query}")


@app.command()
def recommend(profile: str, top: int = 10, llm: bool = False) -> None:
    """Recommend capstone domains based on a student profile."""
    console.print(f"Ranking top {top} domains using profile: {profile}")
    if llm:
        console.print("LLM explanations enabled.")


if __name__ == "__main__":
    app()
