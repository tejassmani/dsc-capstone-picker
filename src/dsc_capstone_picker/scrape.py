import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag

from dsc_capstone_picker.models import CapstoneDomain

ENROLLMENT_URL = "https://dsc-capstone.org/enrollment/"
SECTION_RE = re.compile(
    r"^(?P<section>[A-Z]\d{1,3})\s+"
    r"(?P<seats>\d+)\s+seats?\s*"
    r"(?P<meeting>.*?)(?:\s+Industry Partner)?$",
    re.IGNORECASE,
)
EMAIL_RE = re.compile(r"[\w.+-]+@[\w.-]+\.\w+")
DETAIL_LABELS = {
    "about": "description",
    "mentoring style": "mentor_style",
    "suggested prerequisites": "prerequisites",
    "prerequisites": "prerequisites",
    "summer tasks": "summer_tasks",
    "previous project": "previous_projects",
    "previous projects": "previous_projects",
}
TOPIC_HEADINGS_TO_SKIP = {"overview", "enrollment"}


def fetch_domains(url: str = ENROLLMENT_URL) -> list[CapstoneDomain]:
    """Download and parse DSC capstone domains from the enrollment page."""
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return parse_domains(response.text, base_url=url)


def parse_domains(html: str, base_url: str = ENROLLMENT_URL) -> list[CapstoneDomain]:
    """Parse capstone domains from an enrollment page HTML document."""
    soup = BeautifulSoup(html, "html.parser")
    domains: list[CapstoneDomain] = []

    for heading in soup.find_all("h3"):
        try:
            domain = _parse_domain_heading(heading, base_url)
        except Exception:
            continue
        if domain is not None:
            domains.append(domain)

    return domains


def _parse_domain_heading(heading: Tag, base_url: str) -> CapstoneDomain | None:
    title = _extract_title(heading)
    if not title:
        return None

    siblings = _domain_siblings(heading)
    raw_text = _clean_text(
        "\n".join(
            sibling.get_text(" ", strip=True)
            for sibling in [heading, *siblings]
            if isinstance(sibling, Tag)
        )
    )
    lines = _domain_lines(heading, siblings)
    section_line = _first_matching_line(lines, SECTION_RE)
    if section_line is None:
        return None

    section, seats, meeting_time = _parse_section_line(section_line)
    details = _extract_details(lines)
    previous_projects = details.get("previous_projects", "")
    if not previous_projects:
        previous_projects = _extract_previous_project_links(siblings, base_url)

    return CapstoneDomain(
        title=title,
        mentor=_extract_mentor(lines, section_line),
        section=section,
        seats=seats,
        meeting_time=meeting_time,
        industry_partner="industry partner" in raw_text.lower(),
        topic_area=_extract_topic_area(heading),
        description=_extract_description(lines, section_line, details),
        prerequisites=details.get("prerequisites", ""),
        mentor_style=details.get("mentor_style", ""),
        summer_tasks=details.get("summer_tasks", ""),
        previous_projects=previous_projects,
        url=_extract_url(heading, base_url),
        raw_text=raw_text,
    )


def _domain_siblings(heading: Tag) -> list[Tag]:
    siblings: list[Tag] = []
    for sibling in heading.find_next_siblings():
        if not isinstance(sibling, Tag):
            continue
        if sibling.name in {"h2", "h3"}:
            break
        siblings.append(sibling)
    return siblings


def _domain_lines(heading: Tag, siblings: list[Tag]) -> list[str]:
    if _is_staffer_heading(heading):
        lines = _staffer_heading_lines(heading)
    else:
        lines = [_clean_text(heading.get_text(" ", strip=True))]

    for sibling in siblings:
        for text in sibling.stripped_strings:
            line = _clean_text(text)
            if line:
                lines.append(line)
    return lines


def _extract_title(heading: Tag) -> str:
    if _is_staffer_heading(heading):
        for text in heading.stripped_strings:
            title = _clean_text(text)
            if title:
                return title
        return ""
    return _clean_text(heading.get_text(" ", strip=True))


def _is_staffer_heading(heading: Tag) -> bool:
    classes = heading.get("class", [])
    return "staffer-name" in classes


def _staffer_heading_lines(heading: Tag) -> list[str]:
    strings = [_clean_text(text) for text in heading.stripped_strings]
    strings = [text for text in strings if text]
    if not strings:
        return []

    lines = [strings[0]]
    section_index = _find_section_index(strings)

    if section_index is not None:
        mentor = _clean_text(" ".join(strings[1:section_index]))
        if mentor:
            lines.append(mentor)
        section_line = _clean_text(" ".join(strings[section_index:]))
        if section_line:
            lines.append(section_line)
    elif len(strings) > 1:
        lines.append(_clean_text(" ".join(strings[1:])))

    return lines


def _find_section_index(strings: list[str]) -> int | None:
    for index, text in enumerate(strings):
        if re.fullmatch(r"[A-Z]\d{1,3}", text):
            return index
    return None


def _parse_section_line(line: str) -> tuple[str | None, int | None, str | None]:
    match = SECTION_RE.match(line)
    if match is None:
        return None, None, None

    meeting_time = _clean_text(match.group("meeting"))
    meeting_time = re.sub(r"\s*Industry Partner\s*$", "", meeting_time, flags=re.I)
    return (
        match.group("section"),
        int(match.group("seats")),
        meeting_time or None,
    )


def _extract_mentor(lines: list[str], section_line: str) -> str | None:
    try:
        section_index = lines.index(section_line)
    except ValueError:
        section_index = len(lines)

    mentor_text = _clean_text(" ".join(lines[1:section_index]))
    if not mentor_text:
        return None

    mentor = mentor_text.split("•", 1)[0]
    mentor = EMAIL_RE.sub("", mentor)
    mentor = _clean_text(mentor.strip(" ,;:-"))
    if mentor:
        return mentor
    return None


def _extract_topic_area(heading: Tag) -> str | None:
    for previous in heading.find_all_previous(["h2"]):
        topic = _clean_text(previous.get_text(" ", strip=True))
        if topic and topic.lower() not in TOPIC_HEADINGS_TO_SKIP:
            return topic
    return None


def _extract_url(heading: Tag, base_url: str) -> str | None:
    if heading.get("id"):
        return f"{base_url.rstrip('/')}#{heading['id']}"

    for anchor in heading.find_all("a", href=True):
        if "anchor-heading" in anchor.get("class", []):
            continue
        if anchor["href"].startswith("#"):
            return urljoin(base_url, anchor["href"])

    parent = heading.parent
    if isinstance(parent, Tag) and parent.get("id"):
        return f"{base_url.rstrip('/')}#{parent['id']}"

    return base_url


def _extract_previous_project_links(siblings: list[Tag], base_url: str) -> str:
    projects = []
    for sibling in siblings:
        for anchor in sibling.find_all("a", href=True):
            text = _clean_text(anchor.get_text(" ", strip=True))
            if "previous project" not in text.lower():
                continue
            projects.append(f"{text}: {urljoin(base_url, anchor['href'])}")
    return _clean_text("; ".join(projects))


def _extract_description(
    lines: list[str],
    section_line: str,
    details: dict[str, str],
) -> str:
    try:
        start = lines.index(section_line) + 1
    except ValueError:
        start = 1

    description_lines = []
    for line in lines[start:]:
        if line.lower() == "read more":
            break
        if _split_detail_label(line)[0] is not None:
            break
        description_lines.append(line)

    description = _clean_text(" ".join(description_lines))
    if description:
        return description
    return details.get("description", "")


def _extract_details(lines: list[str]) -> dict[str, str]:
    details: dict[str, str] = {}
    current_key: str | None = None

    for line in lines:
        label, value = _split_detail_label(line)
        if label is not None:
            current_key = DETAIL_LABELS[label]
            if value:
                details[current_key] = _append_text(details.get(current_key, ""), value)
            continue

        if line.lower() == "read more":
            current_key = None
            continue

        if "previous project" in line.lower():
            current_key = None
            continue

        if current_key is not None:
            details[current_key] = _append_text(details.get(current_key, ""), line)

    return details


def _split_detail_label(line: str) -> tuple[str | None, str]:
    for label in DETAIL_LABELS:
        prefix = f"{label}:"
        if line.lower().startswith(prefix):
            return label, line[len(prefix) :].strip()
    return None, ""


def _first_matching_line(lines: list[str], pattern: re.Pattern[str]) -> str | None:
    for line in lines:
        if pattern.match(line):
            return line
    return None


def _append_text(existing: str, new_text: str) -> str:
    if not existing:
        return _clean_text(new_text)
    return _clean_text(f"{existing} {new_text}")


def _clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()
