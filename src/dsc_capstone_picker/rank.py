import re
from pathlib import Path

from dsc_capstone_picker.models import (
    CapstoneDomain,
    Recommendation,
    StudentProfile,
    load_profile,
)

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
ABBREVIATION_ALIASES = {
    "ai": ["artificial intelligence"],
    "api": ["application programming interface"],
    "aws": ["amazon web services"],
    "bi": ["business intelligence"],
    "cse": ["computer science", "computer science and engineering"],
    "cpu": ["central processing unit", "processor"],
    "crm": ["customer relationship management"],
    "dsc": ["data science"],
    "ece": ["electrical engineering", "electrical and computer engineering"],
    "gis": ["geographic information system", "geospatial"],
    "gpu": ["graphics processing unit", "accelerator"],
    "gwas": ["genome wide association study", "genomics"],
    "hdsi": ["halicioglu data science institute", "data science institute"],
    "hpc": ["high performance computing"],
    "irb": ["institutional review board"],
    "llm": ["large language model", "large language models"],
    "lm": ["language model", "language models"],
    "ml": ["machine learning"],
    "mmd": ["maximum mean discrepancy"],
    "nlp": ["natural language processing"],
    "rag": ["retrieval augmented generation"],
    "rl": ["reinforcement learning"],
    "rlhf": ["reinforcement learning from human feedback"],
    "sdk": ["software development kit"],
    "seo": ["search engine optimization"],
    "sql": ["structured query language", "database"],
    "ui": ["user interface"],
    "ucsd": ["uc san diego", "university of california san diego"],
}


def parse_profile_file(path: str | Path) -> StudentProfile:
    """Load a JSON profile or parse a plain-text profile file."""
    source = Path(path)
    if source.suffix.casefold() == ".json":
        return load_profile(source)
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
    score_breakdown = {
        "interest_overlap": 0.0,
        "skill_overlap": 0.0,
        "preference_overlap": 0.0,
        "career_goal_overlap": 0.0,
        "prerequisite_skill_match": 0.0,
        "avoid_term_penalty": 0.0,
    }

    domain_text = _domain_text(domain)
    prerequisite_text = _expanded_text(domain.prerequisites)

    score_breakdown["interest_overlap"] = _score_matches(
        "interest",
        profile.interests,
        domain_text,
        SCORE_WEIGHTS["interests"],
        reasons,
    )
    score_breakdown["skill_overlap"] = _score_matches(
        "skill",
        profile.skills,
        domain_text,
        SCORE_WEIGHTS["skills"],
        reasons,
    )
    score_breakdown["preference_overlap"] = _score_matches(
        "preference",
        profile.preferences,
        domain_text,
        SCORE_WEIGHTS["preferences"],
        reasons,
    )
    score_breakdown["career_goal_overlap"] = _score_matches(
        "career goal",
        profile.career_goals,
        domain_text,
        SCORE_WEIGHTS["career_goals"],
        reasons,
    )
    score_breakdown["prerequisite_skill_match"] = _score_matches(
        "prerequisite skill",
        profile.skills,
        prerequisite_text,
        SCORE_WEIGHTS["prerequisite_skills"],
        reasons,
    )

    avoid_matches = _matched_terms(profile.avoid, domain_text)
    if avoid_matches:
        penalty = len(avoid_matches) * abs(SCORE_WEIGHTS["avoid"])
        score_breakdown["avoid_term_penalty"] = -penalty
        concerns.append("Avoid-term penalty for: " + ", ".join(avoid_matches))

    if not reasons:
        concerns.append("No clear profile overlap found.")

    score = sum(score_breakdown.values())
    return Recommendation(
        domain=domain,
        score=round(score, 2),
        score_breakdown={
            key: round(value, 2)
            for key, value in score_breakdown.items()
            if value != 0
        },
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
    normalized_text = _expanded_text(text)
    matches = []
    for term in terms:
        if any(variant in normalized_text for variant in _term_variants(term)):
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
    return _expanded_text(" ".join(values))


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


def _expanded_text(text: str) -> str:
    normalized = _normalize(text)
    expansions = []
    for token in _tokens(normalized):
        expansions.extend(ABBREVIATION_ALIASES.get(token, []))
    expansions.extend(_acronyms_for_phrases(normalized))
    return _normalize(" ".join([normalized, *expansions]))


def _term_variants(term: str) -> list[str]:
    normalized = _normalize(term)
    if not normalized:
        return []

    variants = {normalized}
    variants.update(ABBREVIATION_ALIASES.get(normalized, []))
    for abbreviation, aliases in ABBREVIATION_ALIASES.items():
        if normalized in aliases:
            variants.add(abbreviation)
    variants.update(_acronyms_for_phrases(normalized))
    return [_normalize(variant) for variant in variants if variant]


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+(?:/[a-z0-9]+)?", text)


def _acronyms_for_phrases(text: str) -> list[str]:
    acronyms = []
    stopwords = {"and", "for", "of", "the", "to", "with", "from", "in", "on"}
    words = [word for word in _tokens(text) if word not in stopwords]
    for size in range(2, 6):
        for start in range(0, len(words) - size + 1):
            acronyms.append("".join(word[0] for word in words[start : start + size]))
    return acronyms
