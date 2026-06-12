from typer.testing import CliRunner

from dsc_capstone_picker import cli
from dsc_capstone_picker.llm import (
    MISSING_API_KEY_MESSAGE,
    MissingOpenAIAPIKeyError,
    add_llm_explanations,
)
from dsc_capstone_picker.models import CapstoneDomain, Recommendation, StudentProfile


runner = CliRunner()


def sample_recommendations() -> list[Recommendation]:
    return [
        Recommendation(
            domain=CapstoneDomain(title="Safe Agentic AI", mentor="Babak Salimi"),
            score=8.0,
            reasons=["Interest match: LLM"],
        )
    ]


def test_add_llm_explanations_requires_openai_api_key(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    try:
        add_llm_explanations(sample_recommendations(), StudentProfile())
    except MissingOpenAIAPIKeyError as error:
        assert str(error) == MISSING_API_KEY_MESSAGE
    else:
        raise AssertionError("Expected MissingOpenAIAPIKeyError")


def test_recommend_local_mode_does_not_call_llm(monkeypatch) -> None:
    monkeypatch.setattr(cli, "_load_cached_domains", lambda: [CapstoneDomain(title="A")])
    monkeypatch.setattr(
        cli,
        "_rank_from_inputs",
        lambda domains, profile, resume, top: sample_recommendations(),
    )

    def fail_if_called(*args, **kwargs):
        raise AssertionError("LLM should not be called without --llm")

    monkeypatch.setattr(cli, "add_llm_explanations", fail_if_called)

    result = runner.invoke(cli.app, ["recommend", "--profile", "profile.json", "--top", "1"])

    assert result.exit_code == 0
    assert "Safe Agentic AI" in result.output


def test_recommend_llm_flag_shows_friendly_error_without_key(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(cli, "_load_cached_domains", lambda: [CapstoneDomain(title="A")])
    monkeypatch.setattr(
        cli,
        "_rank_from_inputs",
        lambda domains, profile, resume, top: sample_recommendations(),
    )
    monkeypatch.setattr(
        cli,
        "_profile_from_inputs",
        lambda profile, resume: StudentProfile(interests=["LLM"]),
    )

    result = runner.invoke(
        cli.app,
        ["recommend", "--profile", "profile.json", "--top", "1", "--llm"],
    )

    assert result.exit_code == 0
    assert "LLM explanations require OPENAI_API_KEY" in result.output
    assert "without --llm" in result.output
