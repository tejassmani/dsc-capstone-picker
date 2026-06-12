import csv
from io import StringIO

from dsc_capstone_picker.export import (
    format_recommendations_csv,
    format_recommendations_txt,
)
from dsc_capstone_picker.models import CapstoneDomain, Recommendation


def sample_recommendations() -> list[Recommendation]:
    return [
        Recommendation(
            domain=CapstoneDomain(title="Safe Agentic AI", mentor="Babak Salimi"),
            score=9.5,
            reasons=["Interest match: LLMs", "Skill match: Python"],
            concerns=["Avoid-term penalty for: heavy systems"],
        ),
        Recommendation(
            domain=CapstoneDomain(title="Civic Analytics"),
            score=4.0,
            reasons=["Skill match: SQL"],
            concerns=[],
        ),
    ]


def test_format_recommendations_csv() -> None:
    csv_text = format_recommendations_csv(sample_recommendations())
    rows = list(csv.DictReader(StringIO(csv_text)))

    assert rows == [
        {
            "rank": "1",
            "title": "Safe Agentic AI",
            "mentor": "Babak Salimi",
            "score": "9.50",
            "reasons": "Interest match: LLMs; Skill match: Python",
            "concerns": "Avoid-term penalty for: heavy systems",
        },
        {
            "rank": "2",
            "title": "Civic Analytics",
            "mentor": "",
            "score": "4.00",
            "reasons": "Skill match: SQL",
            "concerns": "",
        },
    ]


def test_format_recommendations_txt() -> None:
    text = format_recommendations_txt(sample_recommendations())

    assert "Top Recommendations" in text
    assert "1. Safe Agentic AI" in text
    assert "Mentor: Babak Salimi" in text
    assert "Score: 9.50" in text
    assert "Reasons: Interest match: LLMs; Skill match: Python" in text
    assert "Concerns: Avoid-term penalty for: heavy systems" in text
    assert "2. Civic Analytics" in text
    assert "Concerns: None" in text
