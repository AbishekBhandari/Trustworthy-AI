"""Configurable policy constants for the guardrail demo."""

MAX_INPUT_CHARS = 4000

# These are examples for an educational demo, not a comprehensive policy.
SENSITIVE_TOPIC_ACTIONS = {
    "medical": "cautious_answer",
    "self_harm": "supportive_redirect",
    "illegal_activity": "refuse",
    "credential_theft": "refuse",
}
