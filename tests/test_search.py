from dsc_capstone_picker.models import CapstoneDomain
from dsc_capstone_picker.search import find_domain, search_domains


def sample_domains() -> list[CapstoneDomain]:
    return [
        CapstoneDomain(
            title="Safe Agentic AI",
            mentor="Babak Salimi",
            section="D33",
            seats=4,
            topic_area="AI/ML Systems",
            description="Audit and harden LLM agents.",
            prerequisites="Python and machine learning.",
            mentor_style="Weekly research meetings.",
            summer_tasks="Read papers about agent safety.",
            raw_text="Data-centric safety for tool-using agents.",
        ),
        CapstoneDomain(
            title="Civic Analytics",
            mentor="Prof. Maps",
            section="D40",
            seats=8,
            topic_area="Applied Data Science",
            description="Analyze public-service data.",
            prerequisites="SQL and visualization.",
            mentor_style="Hands-on early, lighter later.",
            summer_tasks="Review open data portals.",
            raw_text="Urban planning and civic data.",
        ),
    ]


def test_search_domains_checks_required_fields_case_insensitively() -> None:
    domains = sample_domains()

    assert [domain.title for domain in search_domains(domains, "agent safety")] == [
        "Safe Agentic AI"
    ]
    assert [domain.title for domain in search_domains(domains, "PROF maps")] == [
        "Civic Analytics"
    ]
    assert [domain.title for domain in search_domains(domains, "visualization")] == [
        "Civic Analytics"
    ]
    assert [domain.title for domain in search_domains(domains, "weekly research")] == [
        "Safe Agentic AI"
    ]


def test_search_domains_returns_no_matches_when_any_term_is_missing() -> None:
    domains = sample_domains()

    assert search_domains(domains, "agent visualization") == []


def test_find_domain_matches_exact_or_partial_title() -> None:
    domains = sample_domains()

    assert find_domain(domains, "safe agentic ai") == domains[0]
    assert find_domain(domains, "civic") == domains[1]
    assert find_domain(domains, "missing") is None
