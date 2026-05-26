from __future__ import annotations

import os
import unittest

from dotenv import load_dotenv

from backend.rag import evaluate_answer, read_with_rag

load_dotenv()

QUESTION = "What is Python used for and why is it popular?"
ANSWER = "Python is used for web development, automation, data science, and AI because it is readable and has a large ecosystem."


def sample_sources() -> list[dict[str, str]]:
    return [
        {
            "title": "Python Overview",
            "url": "https://example.com/python",
            "snippet": "Python is a high-level interpreted programming language.",
            "content": "# Python\n\nPython is used for scripting, web apps, automation, data science, and AI.",
        },
        {
            "title": "Python Uses",
            "url": "https://example.com/python-uses",
            "snippet": "Python is popular in web development and machine learning.",
            "content": "Python has many libraries for backend services, data analysis, and education.",
        },
        {
            "title": "Python Design",
            "url": "https://example.com/python-design",
            "snippet": "Python syntax is designed to be readable and concise.",
            "content": "Python readability and its standard library make it approachable and useful.",
        },
    ]


@unittest.skipUnless(os.getenv("OPENAI_API_KEY"), "OPENAI_API_KEY is required")
class LivePipelineTests(unittest.TestCase):
    def test_read_and_evaluate(self) -> None:
        result = read_with_rag(QUESTION, sample_sources())
        self.assertGreaterEqual(len(result.facts), 3)
        self.assertGreaterEqual(len(result.contexts), 1)
        scores = evaluate_answer(QUESTION, ANSWER, result.contexts, result.reference)
        self.assertIn("faithfulness", scores)
        self.assertIn("answer_relevance", scores)
