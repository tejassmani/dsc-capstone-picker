import csv
from io import StringIO
from pathlib import Path

from dsc_capstone_picker.models import Recommendation

EXPORT_FORMATS = {"csv", "txt"}


def export_recommendations(
    recommendations: list[Recommendation],
    output: str | Path,
    export_format: str = "csv",
) -> None:
    """Write recommendations to a CSV or plain-text file."""
    destination = Path(output)
    destination.write_text(
        format_recommendations(recommendations, export_format),
        encoding="utf-8",
    )


def format_recommendations(
    recommendations: list[Recommendation],
    export_format: str = "csv",
) -> str:
    """Format recommendations for export."""
    normalized_format = export_format.casefold()
    if normalized_format == "csv":
        return format_recommendations_csv(recommendations)
    if normalized_format == "txt":
        return format_recommendations_txt(recommendations)
    raise ValueError("Unsupported export format. Use csv or txt.")


def format_recommendations_csv(recommendations: list[Recommendation]) -> str:
    """Format recommendations as CSV."""
    output = StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=["rank", "title", "mentor", "score", "reasons", "concerns"],
    )
    writer.writeheader()
    for rank, recommendation in enumerate(recommendations, start=1):
        writer.writerow(
            {
                "rank": rank,
                "title": recommendation.domain.title,
                "mentor": recommendation.domain.mentor or "",
                "score": f"{recommendation.score:.2f}",
                "reasons": "; ".join(recommendation.reasons),
                "concerns": "; ".join(recommendation.concerns),
            }
        )
    return output.getvalue()


def format_recommendations_txt(recommendations: list[Recommendation]) -> str:
    """Format recommendations as a readable plain-text list."""
    lines = ["Top Recommendations", ""]
    for rank, recommendation in enumerate(recommendations, start=1):
        lines.extend(
            [
                f"{rank}. {recommendation.domain.title}",
                f"   Mentor: {recommendation.domain.mentor or 'Unknown'}",
                f"   Score: {recommendation.score:.2f}",
                f"   Reasons: {_join_or_none(recommendation.reasons)}",
                f"   Concerns: {_join_or_none(recommendation.concerns)}",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def _join_or_none(values: list[str]) -> str:
    if not values:
        return "None"
    return "; ".join(values)
