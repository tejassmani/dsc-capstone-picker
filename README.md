# dsc-capstone-picker

`dsc-capstone-picker` is a command-line decision-support tool for UCSD DSC students choosing DSC 180A capstone domains. It parses the official [DSC Capstone enrollment page](https://dsc-capstone.org/enrollment/) into structured domain profiles, then helps students search, compare, summarize, and rank domains based on interests, background, mentor style, prerequisites, and resume fit.

The goal is to make the new top-10 domain selection process easier, more transparent, and less overwhelming. This project is designed for the UCSD DSC Capstone sequence covering DSC 180A in Fall 2026 and DSC 180B in Winter 2027, with optional GPT-powered explanations.

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

Optional GPT-powered explanations:

```bash
OPENAI_API_KEY=... uv run dsc-capstone-picker recommend --profile profile.json --top 10 --llm
```

## API Key

Core functionality works without an API key. `OPENAI_API_KEY` is only needed when using `--llm` for optional GPT-powered explanations.

## Privacy

Resume and profile data stay local for normal fetch, search, recommendation, and export workflows. If `--llm` is used, only the top ranked domains and the student profile/resume summary are sent to OpenAI for concise explanations.
