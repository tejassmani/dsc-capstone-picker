# dsc-capstone-picker

CLI helper for exploring DSC capstone domains and generating local, explainable
recommendations.

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
