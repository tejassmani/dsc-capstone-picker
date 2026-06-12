from dsc_capstone_picker.models import CapstoneDomain, StudentProfile, save_profile
from dsc_capstone_picker.rank import (
    parse_profile_file,
    parse_profile_text,
    rank_domains,
    score_domain,
)


def test_parse_profile_text_with_supported_headings() -> None:
    profile = parse_profile_text(
        """
        Interests:
        - machine learning
        - education technology

        Skills: Python, pandas

        Preferences:
        - structured guidance

        Avoid:
        - hardware

        Career Goals:
        - data scientist
        """
    )

    assert profile.interests == ["machine learning", "education technology"]
    assert profile.skills == ["Python", "pandas"]
    assert profile.preferences == ["structured guidance"]
    assert profile.avoid == ["hardware"]
    assert profile.career_goals == ["data scientist"]
    assert "Interests:" in profile.raw_text


def test_parse_profile_file_loads_json_profile(tmp_path) -> None:
    path = tmp_path / "profile.json"
    expected = StudentProfile(
        interests=["machine learning"],
        skills=["Python"],
        preferences=["applied", "structured"],
        avoid=["heavy theory"],
        career_goals=["data scientist"],
        raw_text="Created interactively.",
    )

    save_profile(expected, path)
    loaded = parse_profile_file(path)

    assert loaded == expected


def test_rank_domains_orders_by_local_score() -> None:
    profile = parse_profile_text(
        """
        Interests:
        - machine learning
        Skills:
        - Python
        Preferences:
        - structured guidance
        Career Goals:
        - data scientist
        """
    )
    strong_match = CapstoneDomain(
        title="Machine Learning for Education",
        description="Build machine learning systems for student success.",
        prerequisites="Python and pandas.",
        mentor_style="Structured guidance every week.",
        raw_text="Good fit for a data scientist.",
    )
    weak_match = CapstoneDomain(
        title="City Permits Dashboard",
        description="Analyze municipal workflow data.",
        prerequisites="SQL.",
        mentor_style="Independent work.",
    )

    recommendations = rank_domains([weak_match, strong_match], profile)

    assert recommendations[0].domain == strong_match
    assert recommendations[0].score > recommendations[1].score


def test_avoid_term_penalty_lowers_score_and_adds_concern() -> None:
    profile = parse_profile_text(
        """
        Interests:
        - machine learning
        Avoid:
        - blockchain
        """
    )
    domain = CapstoneDomain(
        title="Blockchain Machine Learning",
        description="Use machine learning for blockchain analysis.",
    )

    recommendation = score_domain(domain, profile)

    assert recommendation.score < 3.0
    assert recommendation.score_breakdown["interest_overlap"] == 3.0
    assert recommendation.score_breakdown["avoid_term_penalty"] == -4.0
    assert recommendation.concerns == ["Avoid-term penalty for: blockchain"]


def test_score_domain_generates_explainable_reasons() -> None:
    profile = parse_profile_text(
        """
        Interests:
        - large language models
        Skills:
        - PyTorch
        Preferences:
        - clear deliverables
        Career Goals:
        - applied AI
        """
    )
    domain = CapstoneDomain(
        title="Applied AI with Large Language Models",
        description="Build applied AI tools with clear deliverables.",
        prerequisites="PyTorch experience is helpful.",
    )

    recommendation = score_domain(domain, profile)

    assert "Interest match: large language models" in recommendation.reasons
    assert "Skill match: PyTorch" in recommendation.reasons
    assert "Preference match: clear deliverables" in recommendation.reasons
    assert "Career Goal match: applied AI" in recommendation.reasons
    assert "Prerequisite Skill match: PyTorch" in recommendation.reasons
    assert recommendation.score_breakdown == {
        "interest_overlap": 3.0,
        "skill_overlap": 2.0,
        "preference_overlap": 1.5,
        "career_goal_overlap": 2.0,
        "prerequisite_skill_match": 1.0,
    }


def test_abbreviation_matching_works_in_both_directions() -> None:
    profile = parse_profile_text(
        """
        Interests:
        - LLM
        - natural language processing
        Skills:
        - graphics processing unit
        """
    )
    domain = CapstoneDomain(
        title="Large Language Models for NLP",
        description="Train LLM systems with GPU acceleration.",
    )

    recommendation = score_domain(domain, profile)

    assert "Interest match: LLM, natural language processing" in recommendation.reasons
    assert "Skill match: graphics processing unit" in recommendation.reasons
