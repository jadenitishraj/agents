from guardrails import Guard, OnFailAction
from guardrails.hub import ToxicLanguage, DetectPII, RegexMatch, CompetitorCheck


def build_guard(competitors=None, banned_words=None, extra_regex=None):
    competitors = competitors or ["Apple", "Samsung"]
    banned_words = banned_words or []

    validators = [
        ToxicLanguage(threshold=0.5, on_fail=OnFailAction.EXCEPTION),
        DetectPII(
            pii_entities=["EMAIL_ADDRESS", "PHONE_NUMBER", "US_SSN"],
            on_fail=OnFailAction.EXCEPTION,
        ),
        CompetitorCheck(competitors=competitors, on_fail=OnFailAction.EXCEPTION),
    ]

    if banned_words:
        validators.append(
            RegexMatch(regex="|".join(banned_words), match_type="search",
                       on_fail=OnFailAction.EXCEPTION)
        )

    if extra_regex:
        validators.append(
            RegexMatch(regex=extra_regex, match_type="search",
                       on_fail=OnFailAction.EXCEPTION)
        )

    return Guard().use_many(*validators)


def is_safe(guard, text) -> tuple[bool, str]:
    try:
        guard.validate(text)
        return True, "OK"
    except Exception as e:
        return False, str(e)


INJECTION_REGEX = "ignore previous instructions|you are now|system:|disregard all"
CANARY_REGEX = "CNRY-7X9K2"

input_guard = build_guard(
    banned_words=["secret_project"],
    extra_regex=INJECTION_REGEX,
)
output_guard = build_guard(
    banned_words=["secret_project"],
    extra_regex=CANARY_REGEX,
)

# --- Demo ---
if __name__ == "__main__":
    print(is_safe(input_guard, "What's your return policy?"))
    print(is_safe(input_guard, "ignore previous instructions"))
    print(is_safe(output_guard, "Our return window is 30 days."))
    print(is_safe(output_guard, "Sure, here's our CNRY-7X9K2 ..."))
