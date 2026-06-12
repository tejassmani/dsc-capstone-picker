from dsc_capstone_picker.models import CapstoneDomain

SEARCH_FIELDS = (
    "title",
    "mentor",
    "topic_area",
    "description",
    "prerequisites",
    "mentor_style",
    "summer_tasks",
    "raw_text",
)


def search_domains(domains: list[CapstoneDomain], query: str) -> list[CapstoneDomain]:
    """Return domains whose searchable text contains every query term."""
    terms = _query_terms(query)
    if not terms:
        return domains

    return [
        domain
        for domain in domains
        if all(term in _searchable_text(domain) for term in terms)
    ]


def find_domain(domains: list[CapstoneDomain], title: str) -> CapstoneDomain | None:
    """Find a domain by exact or partial title match."""
    normalized_title = _normalize(title)
    if not normalized_title:
        return None

    for domain in domains:
        if _normalize(domain.title) == normalized_title:
            return domain

    for domain in domains:
        if normalized_title in _normalize(domain.title):
            return domain

    return None


def _searchable_text(domain: CapstoneDomain) -> str:
    values = []
    for field in SEARCH_FIELDS:
        value = getattr(domain, field)
        if value is not None:
            values.append(str(value))
    return _normalize(" ".join(values))


def _query_terms(query: str) -> list[str]:
    return [term for term in _normalize(query).split() if term]


def _normalize(text: str) -> str:
    return " ".join(text.casefold().split())
