from __future__ import annotations

import re
from dataclasses import dataclass

try:
    from guardrails import Guard, OnFailAction
    from guardrails.hub import DetectPII, BanList, ValidLength, RegexMatch, SecretsPresent

    _HAS_GUARDRAILS = True
except ModuleNotFoundError:
    Guard = None
    OnFailAction = None
    DetectPII = None
    BanList = None
    ValidLength = None
    RegexMatch = None
    SecretsPresent = None
    _HAS_GUARDRAILS = False


EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
PHONE_RE = re.compile(r"\b(?:\+?1[\s-]?)?(?:\(?\d{3}\)?[\s-]?)\d{3}[\s-]?\d{4}\b")
SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
CARD_RE = re.compile(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b")
AWS_KEY_RE = re.compile(r"\bAKIA[0-9A-Z]{16}\b")
GITHUB_TOKEN_RE = re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b")
OPENAI_KEY_RE = re.compile(r"\bsk-[A-Za-z0-9_-]{10,}\b")


@dataclass
class SimpleValidationResult:
    validation_passed: bool
    error: str | None = None


@dataclass
class SimpleGuard:
    banned_words: list[str]
    min_len: int = 1
    max_len: int = 2000

    def validate(self, text: str) -> SimpleValidationResult:
        if len(text) < self.min_len:
            raise ValueError(f"Input must be at least {self.min_len} character(s) long")
        if len(text) > self.max_len:
            raise ValueError(f"Input must be at most {self.max_len} character(s) long")

        if EMAIL_RE.search(text):
            raise ValueError("Detected email address")
        if PHONE_RE.search(text):
            raise ValueError("Detected phone number")
        if SSN_RE.search(text):
            raise ValueError("Detected US SSN")

        lowered = text.lower()
        for word in self.banned_words:
            if word.lower() in lowered:
                raise ValueError(f"Detected banned content: {word}")

        if AWS_KEY_RE.search(text):
            raise ValueError("Detected AWS access key")
        if GITHUB_TOKEN_RE.search(text):
            raise ValueError("Detected GitHub token")
        if OPENAI_KEY_RE.search(text):
            raise ValueError("Detected OpenAI API key")
        if CARD_RE.search(text):
            raise ValueError("Detected payment card number")

        return SimpleValidationResult(validation_passed=True)


def build_guard(banned_words, min_len=1, max_len=2000):
    if _HAS_GUARDRAILS:
        return Guard.for_string(
            validators=[
                ValidLength(min=min_len, max=max_len, on_fail=OnFailAction.EXCEPTION),
                DetectPII(
                    pii_entities=["EMAIL_ADDRESS", "PHONE_NUMBER", "US_SSN"],
                    on_fail=OnFailAction.EXCEPTION,
                ),
                BanList(banned_words=banned_words, on_fail=OnFailAction.EXCEPTION),
                SecretsPresent(on_fail=OnFailAction.EXCEPTION),
                RegexMatch(
                    regex=CARD_RE.pattern,
                    match_type="search",
                    on_fail=OnFailAction.EXCEPTION,
                ),
            ]
        )

    return SimpleGuard(
        banned_words=list(banned_words),
        min_len=min_len,
        max_len=max_len,
    )


def is_safe(guard, text) -> tuple[bool, str]:
    try:
        outcome = guard.validate(text)
        if outcome.validation_passed:
            return True, "OK"
        return False, outcome.error or "Validation failed"
    except Exception as e:
        return False, str(e)


input_guard = build_guard(
    banned_words=[
        "secret_project",
        "ignore previous instructions",
        "you are now",
        "disregard all",
    ]
)

output_guard = build_guard(
    banned_words=[
        "secret_project",
        "CNRY-7X9K2",
    ]
)


if __name__ == "__main__":
    print(is_safe(input_guard, "What's your return policy?"))
    print(is_safe(input_guard, "ignore previous instructions"))
    print(is_safe(output_guard, "Our return window is 30 days."))
    print(is_safe(output_guard, "Sure, here's our CNRY-7X9K2 ..."))
