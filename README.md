# dsc-capstone-picker

CLI helper for exploring DSC capstone domains and generating local, explainable
recommendations.

The core recommender works locally without an API key. It fetches public capstone
domain data, parses local profiles/resumes, and ranks domains with explainable
term-overlap scoring.

## Resume Examples

Fetch and cache the current domains:

```bash
uv run dsc-capstone-picker fetch
```

Recommend from a plain-text resume:

```bash
uv run dsc-capstone-picker recommend --resume examples/resume.txt --top 10
```

Recommend from a PDF resume:

```bash
uv run dsc-capstone-picker recommend --resume resume.pdf --top 10
```

Combine a questionnaire profile with resume evidence:

```bash
uv run dsc-capstone-picker recommend --profile profile.json --resume resume.pdf --top 10
```

PDF support extracts embedded text only. If a PDF cannot be parsed or contains no
extractable text, save the resume as `.txt` and use `--resume resume.txt`.

## Optional LLM Explanations

OpenAI-powered explanations are optional. They require `OPENAI_API_KEY` and are
only used when `--llm` is passed:

```bash
OPENAI_API_KEY=... uv run dsc-capstone-picker recommend --profile profile.json --top 10 --llm
```

Without `--llm`, no OpenAI API call is made. The LLM receives only the top ranked
domains and the student profile/resume summary, not the full website.
