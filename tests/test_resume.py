import pytest

from dsc_capstone_picker.models import StudentProfile
from dsc_capstone_picker.resume import (
    load_resume_text,
    merge_profiles,
    profile_from_resume_text,
)


def test_profile_from_resume_text_extracts_data_science_skills() -> None:
    resume_text = """
    Built Python data pipelines using pandas, NumPy, and SQL.
    Trained scikit-learn and PyTorch models for NLP dashboards.
    Used Git, Docker, REST APIs, and web scraping with BeautifulSoup.
    """

    profile = profile_from_resume_text(resume_text)

    assert profile.resume_text == resume_text
    assert profile.skills == [
        "Python",
        "pandas",
        "NumPy",
        "scikit-learn",
        "PyTorch",
        "SQL",
        "Git",
        "Docker",
        "APIs",
        "NLP",
        "visualization",
        "web scraping",
        "data engineering",
    ]


def test_profile_from_resume_text_infers_obvious_interests() -> None:
    resume_text = """
    Created healthcare NLP tools with large language models.
    Built dashboards for climate data visualization and geospatial mapping.
    """

    profile = profile_from_resume_text(resume_text)

    assert profile.interests == [
        "large language models",
        "natural language processing",
        "data visualization",
        "healthcare",
        "climate",
        "geospatial",
    ]


def test_load_resume_text_rejects_unsupported_files(tmp_path) -> None:
    resume_path = tmp_path / "resume.md"
    resume_path.write_text("Python and SQL", encoding="utf-8")

    with pytest.raises(ValueError, match="Only .txt and .pdf resumes are supported"):
        load_resume_text(resume_path)


def test_load_resume_text_pdf_failure_suggests_txt(tmp_path) -> None:
    resume_path = tmp_path / "resume.pdf"
    resume_path.write_bytes(b"not actually a pdf")

    with pytest.raises(ValueError, match="Try saving your resume as a .txt file"):
        load_resume_text(resume_path)


def test_merge_profiles_combines_resume_and_questionnaire_evidence() -> None:
    questionnaire = StudentProfile(
        interests=["healthcare"],
        preferences=["applied"],
        avoid=["heavy theory"],
        career_goals=["data scientist"],
        raw_text="Questionnaire text",
    )
    resume = StudentProfile(
        interests=["healthcare", "large language models"],
        skills=["Python", "SQL"],
        resume_text="Resume text",
        raw_text="Resume text",
    )

    merged = merge_profiles(questionnaire, resume)

    assert merged.interests == ["healthcare", "large language models"]
    assert merged.skills == ["Python", "SQL"]
    assert merged.preferences == ["applied"]
    assert merged.avoid == ["heavy theory"]
    assert merged.career_goals == ["data scientist"]
    assert merged.resume_text == "Resume text"
    assert "Questionnaire text" in merged.raw_text
    assert "Resume text" in merged.raw_text
