# dsc-capstone-picker

`dsc-capstone-picker` is a DSC 190 final project tool for exploring UCSD DSC capstone domains and finding projects that fit a student's interests, skills, preferences, and resume. It fetches the public capstone domain list, stores it locally, and produces explainable recommendations using local scoring, with optional OpenAI-powered explanations.

## Installation

```bash
uv add "git+https://github.com/tejassmani/dsc-capstone-picker.git"
```

## Usage

Fetch and cache capstone domains:

```bash
uv run dsc-capstone-picker fetch
```

List cached domains:

```bash
uv run dsc-capstone-picker list
```

Search domains:

```bash
uv run dsc-capstone-picker search "large language models"
```

Show one domain:

```bash
uv run dsc-capstone-picker show "Safe Agentic AI"
```

Create an interactive preference profile:

```bash
uv run dsc-capstone-picker profile create
```

Recommend with a profile:

```bash
uv run dsc-capstone-picker recommend --profile profile.json --top 10
```

Recommend with a resume:

```bash
uv run dsc-capstone-picker recommend --resume examples/resume.txt --top 10
uv run dsc-capstone-picker recommend --resume examples/resume.pdf --top 10
```

Combine profile and resume:

```bash
uv run dsc-capstone-picker recommend --profile profile.json --resume examples/resume.txt --top 10
```

Export recommendations:

```bash
uv run dsc-capstone-picker export --profile profile.json --top 10 --output top10.csv
uv run dsc-capstone-picker export --profile profile.json --resume examples/resume.txt --top 10 --output top10.txt --format txt
```

Optional LLM explanations:

```bash
OPENAI_API_KEY=... uv run dsc-capstone-picker recommend --profile profile.json --top 10 --llm
```

## API Key

Core functionality works without an API key. `OPENAI_API_KEY` is only needed when using `--llm` for optional OpenAI-powered explanations.

## Privacy

Resume and profile data stay local for normal fetch, search, recommendation, and export workflows. If `--llm` is used, only the top ranked domains and the student profile/resume summary are sent to OpenAI for concise explanations.
