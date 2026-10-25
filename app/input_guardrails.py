
"""Input guardrails: PII, prompt injection, and sensitive-topic screening."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal

from app.config import MAX_INPUT_CHARS, SENSITIVE_TOPIC_ACTIONS

Action = Literal["allow", "sanitize", "review", "refuse"]


@dataclass
class GuardrailResult:
    allowed: bool
    action: Action
    text: str
    flags: list[str] = field(default_factory=list)
    details: dict[str, str] = field(default_factory=dict)


# Match standard emails and common text-based email obfuscations:
# alice@example.com, alice [at] example [dot] com,
# alice(at)example(dot)com.
EMAIL_PATTERN = re.compile(
    r"""
    \b
    (?:
        [A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}
        |
        [A-Za-z0-9._%+-]+\s*
        (?:\[at\]|\(at\)|\{at\}|\s+at\s+)\s*
        [A-Za-z0-9-]+
        (?:
            \s*(?:\[dot\]|\(dot\)|\{dot\}|\s+dot\s+)\s*
            [A-Za-z0-9-]+
        )+
    )
    \b
    """,
    re.IGNORECASE | re.VERBOSE,
)

PII_PATTERNS: dict[str, re.Pattern[str]] = {
    "email": EMAIL_PATTERN,
    "phone": re.compile(
        r"(?<!\w)(?:\+\d{1,3}[-.\s]?)?"
        r"(?:\(\d{2,4}\)[-.\s]?)?\d{6,10}(?!\w)"
    ),
    "national_id": re.compile(
        r"\b(?:citizenship|national\s+id|passport|id\s+number)"
        r"\s*[:#-]?\s*[A-Z0-9-]{5,20}\b",
        re.IGNORECASE,
    ),
}


# These patterns detect common, explicit prompt-injection attempts.
# They are heuristic rules, not a complete semantic security filter.
INJECTION_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "instruction_override",
        re.compile(
            r"\b(ignore|disregard|forget|override)\b.{0,80}"
            r"\b(previous|prior|all|system|developer|instructions?|rules?)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "secret_extraction",
        re.compile(
            r"\b(reveal|print|show|expose|leak|extract|summarize|"
            r"describe|quote|repeat|disclose|tell\s+me)\b"
            r".{0,100}\b(system\s+prompt|hidden\s+instructions?|"
            r"secrets?|api\s+keys?|passwords?|confidential\s+data)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "role_override",
        re.compile(
            r"\b(you are now|act as|pretend to be)\b.{0,50}"
            r"\b(unrestricted|developer|admin|system|no rules)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "safety_bypass",
        re.compile(
            r"\b(bypass|disable|turn off|evade)\b.{0,40}"
            r"\b(safety|guardrails?|filters?|restrictions?)\b",
            re.IGNORECASE,
        ),
    ),
]


TOPIC_PATTERNS: dict[str, re.Pattern[str]] = {
    "self_harm": re.compile(
        r"\b(suicide|kill myself|self[- ]harm|hurt myself)\b",
        re.IGNORECASE,
    ),
    "medical": re.compile(
        r"\b(diagnose|symptoms?|medication dosage|treatment for|medical advice)\b",
        re.IGNORECASE,
    ),
    "illegal_activity": re.compile(
        r"\b(make a bomb|build an explosive|evade police|commit fraud|"
        r"steal credit cards?)\b",
        re.IGNORECASE,
    ),
    "credential_theft": re.compile(
        r"\b(phishing|steal passwords?|credential theft|keylogger)\b",
        re.IGNORECASE,
    ),
}


def detect_pii(text: str) -> list[tuple[str, str]]:
    """Return (category, matched_value) pairs for configured PII patterns."""
    matches: list[tuple[str, str]] = []

    for category, pattern in PII_PATTERNS.items():
        matches.extend(
            (category, match.group(0))
            for match in pattern.finditer(text)
        )

    return matches


def redact_pii(text: str) -> tuple[str, list[str]]:
    """Replace detected PII with category-specific placeholders."""
    redacted = text
    categories: list[str] = []

    for category, pattern in PII_PATTERNS.items():
        if pattern.search(redacted):
            categories.append(category)
            redacted = pattern.sub(
                f"[REDACTED_{category.upper()}]",
                redacted,
            )

    return redacted, categories


def detect_prompt_injection(text: str) -> list[str]:
    """Flag common explicit injection and secret-extraction phrases."""
    return [
        name
        for name, pattern in INJECTION_PATTERNS
        if pattern.search(text)
    ]


def classify_sensitive_topics(text: str) -> list[str]:
    """Return all configured sensitive-topic categories found in the input."""
    return [
        category
        for category, pattern in TOPIC_PATTERNS.items()
        if pattern.search(text)
    ]


def inspect_input(
    text: str,
    *,
    redact_personal_data: bool = True,
) -> GuardrailResult:
    """Run input checks in a fixed order and return a policy decision.

    Policy order:
      1. Reject empty or oversized requests.
      2. Refuse detected prompt-injection attempts.
      3. Apply sensitive-topic policy.
      4. Redact PII before downstream processing.
    """
    if not isinstance(text, str) or not text.strip():
        return GuardrailResult(
            False,
            "refuse",
            "",
            ["empty_input"],
            {"reason": "Input must be a non-empty string."},
        )

    if len(text) > MAX_INPUT_CHARS:
        return GuardrailResult(
            False,
            "refuse",
            "",
            ["input_too_long"],
            {"reason": f"Input exceeds {MAX_INPUT_CHARS} characters."},
        )

    injections = detect_prompt_injection(text)
    if injections:
        return GuardrailResult(
            False,
            "refuse",
            "",
            ["prompt_injection", *injections],
            {
                "reason": (
                    "The request appears to attempt instruction "
                    "override or secret extraction."
                )
            },
        )

    topics = classify_sensitive_topics(text)
    refusing_topics = [
        topic
        for topic in topics
        if SENSITIVE_TOPIC_ACTIONS.get(topic) == "refuse"
    ]

    if refusing_topics:
        return GuardrailResult(
            False,
            "refuse",
            "",
            ["sensitive_topic", *refusing_topics],
            {
                "reason": (
                    "This request falls into a category "
                    "this demo refuses to assist with."
                )
            },
        )

    safe_text = text
    pii_matches = detect_pii(text)

    if pii_matches and redact_personal_data:
        safe_text, categories = redact_pii(text)

        return GuardrailResult(
            True,
            "sanitize",
            safe_text,
            ["pii_detected", *categories, *topics],
            {
                "reason": (
                    "Personal data was redacted before "
                    "downstream processing."
                ),
                "sensitive_topics": ",".join(topics),
            },
        )

    if topics:
        return GuardrailResult(
            True,
            "review",
            safe_text,
            ["sensitive_topic", *topics],
            {
                "reason": (
                    "Request requires cautious handling "
                    "by the application."
                ),
                "policy": ",".join(
                    SENSITIVE_TOPIC_ACTIONS[topic]
                    for topic in topics
                ),
            },
        )

    return GuardrailResult(
        True,
        "allow",
        safe_text,
        [],
        {"reason": "No configured input rule was triggered."},
    )
