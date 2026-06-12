import re
from pathlib import Path

from dsc_capstone_picker.models import StudentProfile

KNOWN_SKILLS = {
    "Python": [r"\bpython\b"],
    "pandas": [r"\bpandas\b"],
    "NumPy": [r"\bnumpy\b", r"\bnum\s*py\b"],
    "scikit-learn": [r"\bscikit[- ]learn\b", r"\bsklearn\b"],
    "PyTorch": [r"\bpytorch\b", r"\btorch\b"],
    "TensorFlow": [r"\btensorflow\b"],
    "SQL": [r"\bsql\b", r"\bpostgres(?:ql)?\b", r"\bmysql\b", r"\bsqlite\b"],
    "R": [r"\br\b", r"\brstudio\b"],
    "Git": [r"\bgit\b", r"\bgithub\b"],
    "Docker": [r"\bdocker\b", r"\bcontainer(?:s|ization)?\b"],
    "APIs": [r"\bapi(?:s)?\b", r"\brest\b", r"\bgraphql\b"],
    "NLP": [r"\bnlp\b", r"\bnatural language processing\b"],
    "LLMs": [r"\bllm(?:s)?\b", r"\blarge language model(?:s)?\b"],
    "visualization": [
        r"\bvisuali[sz]ation\b",
        r"\bdashboard(?:s)?\b",
        r"\btableau\b",
        r"\bmatplotlib\b",
        r"\bseaborn\b",
        r"\bplotly\b",
    ],
    "statistics": [r"\bstatistics?\b", r"\bstatistical\b", r"\binference\b", r"\bregression\b"],
    "machine learning": [r"\bmachine learning\b", r"\bml\b"],
    "deep learning": [r"\bdeep learning\b", r"\bneural network(?:s)?\b"],
    "web scraping": [r"\bweb scraping\b", r"\bscrap(?:e|ing|ed)\b", r"\bbeautifulsoup\b", r"\bselenium\b"],
    "data cleaning": [r"\bdata cleaning\b", r"\bdata wrangling\b", r"\betl\b"],
    "data engineering": [r"\bdata engineering\b", r"\bpipeline(?:s)?\b", r"\bairflow\b", r"\bspark\b"],
    "cloud": [r"\baws\b", r"\bgcp\b", r"\bazure\b", r"\bcloud\b"],
    "GIS": [r"\bgis\b", r"\bgeospatial\b"],
}
INTEREST_KEYWORDS = {
    "large language models": [r"\bllm(?:s)?\b", r"\blarge language model(?:s)?\b"],
    "natural language processing": [r"\bnlp\b", r"\bnatural language processing\b", r"\btext\b"],
    "machine learning": [r"\bmachine learning\b", r"\bml\b"],
    "deep learning": [r"\bdeep learning\b", r"\bneural network(?:s)?\b"],
    "data visualization": [r"\bvisuali[sz]ation\b", r"\bdashboard(?:s)?\b"],
    "healthcare": [r"\bhealth(?:care)?\b", r"\bclinical\b", r"\bmedical\b"],
    "climate": [r"\bclimate\b", r"\bweather\b", r"\benvironment(?:al)?\b"],
    "education technology": [r"\beducation\b", r"\bedtech\b", r"\bstudent(?:s)?\b"],
    "finance": [r"\bfinance\b", r"\bfinancial\b", r"\bmarket(?:s)?\b"],
    "marketing": [r"\bmarketing\b", r"\bcustomer(?:s)?\b", r"\bcrm\b"],
    "geospatial": [r"\bgeospatial\b", r"\bgis\b", r"\bmap(?:s|ping)?\b"],
    "bioinformatics": [r"\bbioinformatics\b", r"\bgenomics\b", r"\bdna\b", r"\brna\b"],
    "cybersecurity": [r"\bcybersecurity\b", r"\bsecurity\b", r"\badversarial\b"],
}


def load_resume_text(path: str | Path) -> str:
    """Load a plain-text resume."""
    source = Path(path)
    if source.suffix.casefold() != ".txt":
        raise ValueError("Only plain text .txt resumes are supported.")
    return source.read_text(encoding="utf-8")


def profile_from_resume(path: str | Path) -> StudentProfile:
    """Infer a student profile from a plain-text resume file."""
    text = load_resume_text(path)
    return profile_from_resume_text(text)


def profile_from_resume_text(text: str) -> StudentProfile:
    """Infer skills and obvious interests from resume text using local rules."""
    return StudentProfile(
        interests=_extract_terms(text, INTEREST_KEYWORDS),
        skills=_extract_terms(text, KNOWN_SKILLS),
        resume_text=text,
        raw_text=text,
    )


def merge_profiles(*profiles: StudentProfile | None) -> StudentProfile:
    """Merge questionnaire and resume-derived profile evidence."""
    present_profiles = [profile for profile in profiles if profile is not None]
    return StudentProfile(
        interests=_merge_lists(profile.interests for profile in present_profiles),
        skills=_merge_lists(profile.skills for profile in present_profiles),
        preferences=_merge_lists(profile.preferences for profile in present_profiles),
        avoid=_merge_lists(profile.avoid for profile in present_profiles),
        career_goals=_merge_lists(profile.career_goals for profile in present_profiles),
        resume_text="\n\n".join(profile.resume_text for profile in present_profiles if profile.resume_text),
        raw_text="\n\n".join(profile.raw_text for profile in present_profiles if profile.raw_text),
    )


def _extract_terms(text: str, patterns_by_term: dict[str, list[str]]) -> list[str]:
    matches = []
    for term, patterns in patterns_by_term.items():
        if any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns):
            matches.append(term)
    return matches


def _merge_lists(lists: object) -> list[str]:
    merged = []
    seen = set()
    for values in lists:
        for value in values:
            normalized = value.casefold()
            if normalized not in seen:
                merged.append(value)
                seen.add(normalized)
    return merged
