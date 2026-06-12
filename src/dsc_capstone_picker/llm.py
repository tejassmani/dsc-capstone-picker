import json
import os
from collections.abc import Callable

from openai import OpenAI

from dsc_capstone_picker.models import Recommendation, StudentProfile

DEFAULT_MODEL = "gpt-4o-mini"
MISSING_API_KEY_MESSAGE = (
    "LLM explanations require OPENAI_API_KEY. Set it in your environment, "
    "or run without --llm for fully local recommendations."
)


class MissingOpenAIAPIKeyError(RuntimeError):
    """Raised when optional OpenAI explanations are requested without an API key."""


def add_llm_explanations(
    recommendations: list[Recommendation],
    profile: StudentProfile,
    client_factory: Callable[..., OpenAI] = OpenAI,
) -> list[Recommendation]:
    """Add concise OpenAI-powered explanations to already-ranked recommendations."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise MissingOpenAIAPIKeyError(MISSING_API_KEY_MESSAGE)

    if not recommendations:
        return recommendations

    client = client_factory(api_key=api_key)
    response = client.responses.create(
        model=os.getenv("OPENAI_MODEL", DEFAULT_MODEL),
        instructions=(
            "You explain UCSD DSC capstone recommendations. Be concise and practical. "
            "Use only the provided profile and ranked domains. Return JSON only."
        ),
        input=_build_prompt(recommendations, profile),
        max_output_tokens=600,
        temperature=0.2,
    )
    explanations = _parse_explanations(getattr(response, "output_text", ""))

    for index, recommendation in enumerate(recommendations, start=1):
        explanation = explanations.get(str(index), "")
        if explanation:
            recommendation.llm_explanation = explanation

    return recommendations


def _build_prompt(recommendations: list[Recommendation], profile: StudentProfile) -> str:
    payload = {
        "student_profile": {
            "interests": profile.interests,
            "skills": profile.skills,
            "preferences": profile.preferences,
            "avoid": profile.avoid,
            "career_goals": profile.career_goals,
            "resume_excerpt": profile.resume_text[:1200],
        },
        "recommendations": [
            {
                "rank": index,
                "title": recommendation.domain.title,
                "mentor": recommendation.domain.mentor,
                "score": recommendation.score,
                "local_reasons": recommendation.reasons,
                "local_concerns": recommendation.concerns,
                "domain_summary": recommendation.domain.description[:900],
                "prerequisites": recommendation.domain.prerequisites[:600],
            }
            for index, recommendation in enumerate(recommendations, start=1)
        ],
        "format": {
            "1": "One sentence explaining why rank 1 fits, with any caveat.",
            "2": "One sentence explaining rank 2, etc.",
        },
    }
    return json.dumps(payload, ensure_ascii=True)


def _parse_explanations(output_text: str) -> dict[str, str]:
    try:
        data = json.loads(output_text)
    except json.JSONDecodeError:
        return {}

    if not isinstance(data, dict):
        return {}

    explanations = {}
    for key, value in data.items():
        if isinstance(value, str):
            explanations[str(key)] = value.strip()
    return explanations
