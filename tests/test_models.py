from dsc_capstone_picker.models import (
    CapstoneDomain,
    Recommendation,
    StudentProfile,
    load_domains,
    load_profile,
    save_domains,
    save_profile,
)


def test_model_creation() -> None:
    domain = CapstoneDomain(
        title="Health Data Science",
        mentor="Dr. Data",
        section="A00",
        seats=8,
        meeting_time="Tuesdays 2-3pm",
        industry_partner=True,
        topic_area="Healthcare",
        description="Analyze clinical datasets.",
        prerequisites="Python and statistics",
        mentor_style="Structured weekly check-ins",
        summer_tasks="Read background papers",
        previous_projects="Risk prediction dashboards",
        url="https://example.com/domain",
        raw_text="Full scraped text would go here.",
    )
    profile = StudentProfile(
        interests=["healthcare", "machine learning"],
        skills=["python", "pandas"],
        preferences=["structured mentorship"],
        avoid=["heavy frontend"],
        career_goals=["health tech"],
        resume_text="Built data apps.",
        raw_text="I want a healthcare project.",
    )
    recommendation = Recommendation(
        domain=domain,
        score=0.87,
        reasons=["Matches healthcare interest"],
        concerns=["May require domain reading"],
    )

    assert domain.raw_text == "Full scraped text would go here."
    assert profile.avoid == ["heavy frontend"]
    assert profile.career_goals == ["health tech"]
    assert recommendation.domain.title == "Health Data Science"
    assert recommendation.score == 0.87


def test_domains_save_load_round_trip(tmp_path) -> None:
    path = tmp_path / "domains.json"
    domains = [
        CapstoneDomain(
            title="Civic Data",
            mentor="Prof. Maps",
            seats=6,
            raw_text="Civic project text.",
        )
    ]

    save_domains(domains, path)
    loaded = load_domains(path)

    assert loaded == domains


def test_profile_save_load_round_trip(tmp_path) -> None:
    path = tmp_path / "profile.json"
    profile = StudentProfile(
        interests=["education"],
        skills=["sql"],
        preferences=["small team"],
        avoid=["hardware"],
        career_goals=["analytics"],
        resume_text="SQL project experience.",
        raw_text="Looking for analytics work.",
    )

    save_profile(profile, path)
    loaded = load_profile(path)

    assert loaded == profile
