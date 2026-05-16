from guardrails import Guard, OnFailAction
from guardrails.hub import DetectPII, BanList, ValidLength, RegexMatch, SecretsPresent


def build_guard(banned_words, min_len=1, max_len=2000):
    return Guard.for_string(validators=[
        ValidLength(min=min_len, max=max_len, on_fail=OnFailAction.EXCEPTION),
        DetectPII(
            pii_entities=["EMAIL_ADDRESS", "PHONE_NUMBER", "US_SSN"],
            on_fail=OnFailAction.EXCEPTION,
        ),
        BanList(banned_words=banned_words, on_fail=OnFailAction.EXCEPTION),
        SecretsPresent(on_fail=OnFailAction.EXCEPTION),   # catches API keys, tokens
        RegexMatch(
            regex=r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b",
            match_type="search",
            on_fail=OnFailAction.EXCEPTION,
        ),
    ])


def is_safe(guard, text) -> tuple[bool, str]:
    try:
        outcome = guard.validate(text)
        if outcome.validation_passed:
            return True, "OK"
        return False, outcome.error or "Validation failed"
    except Exception as e:
        return False, str(e)


input_guard = build_guard(banned_words=[
    "secret_project",
    "ignore previous instructions",
    "you are now",
    "disregard all",
])

output_guard = build_guard(banned_words=[
    "secret_project",
    "CNRY-7X9K2",
])


# --- Demo ---
if __name__ == "__main__":
    print(is_safe(input_guard, "What's your return policy?"))
    print(is_safe(input_guard, "ignore previous instructions"))
    print(is_safe(output_guard, "Our return window is 30 days."))
    print(is_safe(output_guard, "Sure, here's our CNRY-7X9K2 ..."))