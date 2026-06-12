from dsc_capstone_picker.scrape import parse_domains


def test_parse_domains_from_fake_html() -> None:
    html = """
    <main>
      <h2>Overview</h2>
      <h3>How should I choose a domain?</h3>
      <p>This is not a domain.</p>

      <h2>AI/ML Systems</h2>
      <h3 id="safe-ai">Safe Agentic AI</h3>
      <p><a href="https://example.com/mentor">Babak Salimi</a> • mentor@ucsd.edu</p>
      <p>D33 4 seats Fridays, 11am-12pm Industry Partner</p>
      <p>Students will audit and harden LLM agents.</p>
      <p>Read more</p>
      <ul>
        <li>About: The mentor studies trustworthy machine learning.</li>
        <li>Mentoring Style: Weekly research meetings.</li>
        <li>Suggested Prerequisites: Python and ML fundamentals.</li>
        <li>Summer Tasks: Read papers and reproduce a baseline.</li>
        <li><a href="/showcase/safe-ai">Previous Project</a></li>
      </ul>

      <h2>Applied Data Science</h2>
      <h3>Civic Analytics</h3>
      <p>Prof. Maps • maps@ucsd.edu</p>
      <p>D40 8 seats Wednesdays 3pm</p>
      <p>Analyze public-service data.</p>
      <ul>
        <li>Mentoring Style: Hands-on early, lighter later.</li>
      </ul>
    </main>
    """

    domains = parse_domains(html, base_url="https://dsc-capstone.org/enrollment/")

    assert len(domains) == 2
    assert domains[0].title == "Safe Agentic AI"
    assert domains[0].mentor == "Babak Salimi"
    assert domains[0].section == "D33"
    assert domains[0].seats == 4
    assert domains[0].meeting_time == "Fridays, 11am-12pm"
    assert domains[0].industry_partner is True
    assert domains[0].topic_area == "AI/ML Systems"
    assert domains[0].description == "Students will audit and harden LLM agents."
    assert domains[0].prerequisites == "Python and ML fundamentals."
    assert domains[0].mentor_style == "Weekly research meetings."
    assert domains[0].summer_tasks == "Read papers and reproduce a baseline."
    assert domains[0].previous_projects.endswith("/showcase/safe-ai")
    assert domains[0].url == "https://dsc-capstone.org/enrollment#safe-ai"
    assert "Safe Agentic AI" in domains[0].raw_text

    assert domains[1].title == "Civic Analytics"
    assert domains[1].industry_partner is False
    assert domains[1].topic_area == "Applied Data Science"
    assert domains[1].prerequisites == ""


def test_parse_domains_tolerates_weird_domain_formatting() -> None:
    html = """
    <h2>Theoretical Foundations</h2>
    <h3>Odd But Valid Domain</h3>
    <p>D99 3 seats TBD</p>
    <p>No mentor line is available yet.</p>
    """

    domains = parse_domains(html)

    assert len(domains) == 1
    assert domains[0].title == "Odd But Valid Domain"
    assert domains[0].mentor is None
    assert domains[0].meeting_time == "TBD"
    assert domains[0].raw_text
