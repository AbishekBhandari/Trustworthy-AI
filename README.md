# Trustworthy AI Guardrails

A Python-based question-answering assistant prototype that demonstrates input screening, personally identifiable information (PII) redaction, prompt-injection detection, response-schema validation, and groundedness checks.

## Features

### Input guardrails
- Reject empty and oversized inputs.
- Detect common prompt-injection patterns, including instruction overrides and hidden-prompt extraction attempts.
- Detect and redact supported PII formats, including emails, phone numbers, and national-ID-like strings.
- Recognize common obfuscated email formats, such as `[at]` and `[dot]`.
- Classify selected sensitive topics and apply configurable handling policies.

### Output guardrails
- Validate response structure using Pydantic.
- Check whether answer claims have support in retrieved reference text.
- Detect and redact supported PII patterns in answers.
- Return a safe fallback when the response schema is invalid or claims are unsupported.

### Evaluation
- Automated tests using `pytest`.
- A test suite covering input guardrails, output guardrails, schemas, and API behavior.
- A separate evaluation script that records expected and actual outcomes, pass/fail status, and precision/recall metrics.

## Architecture

The request pipeline follows this general flow:

1. Validate user input.
2. Check for prompt injection.
3. Apply sensitive-topic policies.
4. Detect and redact PII.
5. Retrieve relevant passages from the local knowledge base.
6. Generate an answer from retrieved material.
7. Validate the response schema.
8. Check output PII and groundedness.
9. Return the validated response or a safe fallback.

See [`docs/architecture.mmd`](docs/architecture.mmd) for the architecture diagram.

## Technology Stack

- Python 3.13
- `uv` for dependency and environment management
- FastAPI for the API
- Pydantic for response-schema validation
- Regular expressions for rule-based detection
- `pytest` for automated testing
- JSON for the local reference knowledge base

## Project Structure

```text
trustworthy-ai-guardrails/
├── app/
│   ├── assistant.py
│   ├── config.py
│   ├── input_guardrails.py
│   ├── knowledge_base.py
│   ├── main.py
│   ├── output_guardrails.py
│   └── schemas.py
├── data/
│   └── reference_docs.json
├── docs/
│   └── architecture.mmd
├── reports/
│   ├── evaluation_metrics.json
│   ├── evaluation_report.md
│   └── evaluation_results.csv
├── scripts/
│   └── evaluate.py
├── tests/
├── pyproject.toml
├── uv.lock
├── requirements.txt
└── README.md
```

## Setup

Install Python 3.13 and [`uv`](https://docs.astral.sh/uv/).

Clone the repository, then navigate into the project directory:

```bash
git clone <YOUR_REPOSITORY_URL>
cd trustworthy-ai-guardrails
```

Create or synchronize the project environment:

```bash
uv sync
```

## Run the API

Start the development server:

```bash
uv run uvicorn app.main:app --reload
```

The API should be available at `http://127.0.0.1:8000`.

- Health endpoint: `GET /health`
- Question endpoint: `POST /ask`
- Interactive API documentation: `http://127.0.0.1:8000/docs`

Use the interactive API documentation to inspect the exact request schema for `/ask`.

## Run Tests

Run the complete automated test suite:

```bash
uv run python -m pytest -v
```

The latest recorded run completed with **36 passed and 0 failed**.

## Run the Guardrail Evaluation

Execute:

```bash
uv run python scripts/evaluate.py
```

The evaluation script writes detailed results to:

- `reports/evaluation_results.csv`
- `reports/evaluation_metrics.json`

The latest recorded evaluation covered 36 cases, with 36 passing and 0 failing. Each of the six reported guardrail categories recorded precision of 1.00 and recall of 1.00 on that test set.

These results describe only the current, manually constructed evaluation cases. They do not establish comprehensive security or guarantee detection of unseen attacks.

## Evaluation Report

See [`reports/evaluation_report.md`](reports/evaluation_report.md) for the design, results, failure analysis, trade-offs, limitations, and proposed improvements.

## Known Limitations

- Regular-expression rules may miss paraphrased or context-dependent prompt injections.
- PII detection covers selected formats and may miss unfamiliar or encoded representations.
- Lexical-overlap groundedness checks are heuristic and may fail to identify semantic contradictions.
- The local knowledge base is small and retrieval is based on keyword overlap.
- Evaluation coverage is limited; broader adversarial and benign test cases are needed.
- The project is an educational prototype and is not ready to be treated as a production security boundary.

## Future Improvements

- Expand the evaluation dataset with independently reviewed adversarial and benign examples.
- Improve semantic groundedness validation.
- Add more international and obfuscated PII formats.
- Improve knowledge retrieval with semantic search.
- Add structured logging and monitoring.
- Run regular regression tests as new failure cases are discovered.

