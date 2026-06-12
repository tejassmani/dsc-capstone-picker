from pathlib import Path
import re

from dsc_capstone_picker.models import CapstoneDomain, Recommendation, StudentProfile

PROFILE_HEADINGS = {
    "interests": "interests",
    "skills": "skills",
    "preferences": "preferences",
    "avoid": "avoid",
    "career goals": "career_goals",
    "career_goals": "career_goals",
}
SCORE_WEIGHTS = {
    "interests": 3.0,
    "skills": 2.0,
    "preferences": 1.5,
    "career_goals": 2.0,
    "prerequisite_skills": 1.0,
    "avoid": -4.0,
}


def parse_profile_file(path: str | Path) -> StudentProfile:
    """Parse a plain-text profile file with optional section headings."""
    source = Path(path)
    return parse_profile_text(source.read_text(encoding="utf-8"))


def parse_profile_text(text: str) -> StudentProfile:
    """Parse a plain-text student profile into structured local fields."""
    sections: dict[str, list[str]] = {
        "interests": [],
        "skills": [],
        "preferences": [],
        "avoid": [],
        "career_goals": [],
    }
    current_field: str | None = None

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        heading = _parse_heading(line)
        if heading is not None:
            current_field = heading
            remainder = line.split(":", 1)[1].strip()
            if remainder:
                sections[current_field].extend(_split_items(remainder))
            continue

        if current_field is not None:
            sections[current_field].extend(_split_items(line))

    return StudentProfile(
        interests=sections["interests"],
        skills=sections["skills"],
        preferences=sections["preferences"],
        avoid=sections["avoid"],
        career_goals=sections["career_goals"],
        raw_text=text,
    )


def rank_domains(
    domains: list[CapstoneDomain],
    profile: StudentProfile,
    top: int | None = None,
) -> list[Recommendation]:
    """Rank domains with an explainable local term-overlap score."""
    recommendations = [score_domain(domain, profile) for domain in domains]
    recommendations.sort(key=lambda recommendation: recommendation.score, reverse=True)
    if top is None:
        return recommendations
    return recommendations[:top]


def score_domain(domain: CapstoneDomain, profile: StudentProfile) -> Recommendation:
    """Score one domain against a parsed student profile."""
    reasons: list[str] = []
    concerns: list[str] = []
    score = 0.0

    domain_text = _domain_text(domain)
    prerequisite_text = _normalize(domain.prerequisites)

    score += _score_matches(
        "interest",
        profile.interests,
        domain_text,
        SCORE_WEIGHTS["interests"],
        reasons,
    )
    score += _score_matches(
        "skill",
        profile.skills,
        domain_text,
        SCORE_WEIGHTS["skills"],
        reasons,
    )
    score += _score_matches(
        "preference",
        profile.preferences,
        domain_text,
        SCORE_WEIGHTS["preferences"],
        reasons,
    )
    score += _score_matches(
        "career goal",
        profile.career_goals,
        domain_text,
        SCORE_WEIGHTS["career_goals"],
        reasons,
    )
    score += _score_matches(
        "prerequisite skill",
        profile.skills,
        prerequisite_text,
        SCORE_WEIGHTS["prerequisite_skills"],
        reasons,
    )

    avoid_matches = _matched_terms(profile.avoid, domain_text)
    if avoid_matches:
        penalty = len(avoid_matches) * abs(SCORE_WEIGHTS["avoid"])
        score -= penalty
        concerns.append(
            "Avoid-term penalty for: " + ", ".join(avoid_matches)
        )

    if not reasons:
        concerns.append("No clear profile overlap found.")

    return Recommendation(
        domain=domain,
        score=round(score, 2),
        reasons=reasons,
        concerns=concerns,
    )


def _score_matches(
    label: str,
    terms: list[str],
    text: str,
    weight: float,
    reasons: list[str],
) -> float:
    matches = _matched_terms(terms, text)
    if not matches:
        return 0.0

    reasons.append(f"{label.title()} match: {', '.join(matches)}")
    return len(matches) * weight


def _matched_terms(terms: list[str], text: str) -> list[str]:
    normalized_text = _normalize(text)
    matches = []
    for term in terms:
        normalized_term = _normalize(term)
        if normalized_term and normalized_term in normalized_text:
            matches.append(term)
    return matches


def _domain_text(domain: CapstoneDomain) -> str:
    values = [
        domain.title,
        domain.mentor or "",
        domain.topic_area or "",
        domain.description,
        domain.prerequisites,
        domain.mentor_style,
        domain.summer_tasks,
        domain.previous_projects,
        domain.raw_text,
    ]
    return _normalize(" ".join(values))


def _parse_heading(line: str) -> str | None:
    if ":" not in line:
        return None
    heading = line.split(":", 1)[0].strip().casefold()
    return PROFILE_HEADINGS.get(heading)


def _split_items(text: str) -> list[str]:
    cleaned = re.sub(r"^\s*[-*]\s*", "", text.strip())
    return [
        item.strip()
        for item in re.split(r"[,;]", cleaned)
        if item.strip()
    ]


def _normalize(text: str) -> str:
    return " ".join(text.casefold().split())
