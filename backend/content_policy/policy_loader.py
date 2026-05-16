import os

def load_policy() -> str:
    path = os.path.join(os.path.dirname(__file__), "prompts", "content_policy.txt")
    with open(path, "r") as f:
        return f.read()

def wrap_user_input(text: str) -> str:
    return f"<user_input>\n{text}\n</user_input>"
