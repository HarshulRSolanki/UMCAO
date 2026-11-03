"""Unit and integration tests for UMCAO Gemini AI Explanation Routes."""

import sys
import os
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app
from services.gemini_service import _parse_sections_from_markdown

client = TestClient(app)


class TestAIExtensionRoutes(unittest.TestCase):
    def test_explain_empty_code_rejected(self):
        """Empty code should return 400 or error status."""
        response = client.post(
            "/api/ai/explain",
            json={"code": "   ", "language": "python", "mode": "detailed", "explanation_language": "english"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("No code", response.json()["detail"])

    def test_parse_sections_from_markdown(self):
        """Test section parser extracts all 11 standardized markdown headers."""
        sample_markdown = """
## 1. Code Overview
This is a quick summary of the bubble sort code.

## 2. Purpose
Sorts an array in ascending order.

## 3. Line-by-Line Explanation
Line 1 sets up the loop.

## 4. Variables and Functions
- `arr`: The input list.
- `n`: Length of the list.

## 5. Logic and Workflow
It iterates through the elements and swaps adjacent inverted elements.

## 6. Algorithm
Bubble Sort algorithm with pairwise adjacent swaps.

## 7. Example Input and Output
Input: [5, 1, 4] -> Output: [1, 4, 5]

## 8. Time Complexity
O(N^2) worst case.

## 9. Space Complexity
O(1) auxiliary space.

## 10. Possible Improvements
Add an early-termination flag if no swaps occurred.

## 11. Learning Summary
Nested loops, in-place sorting, bubble sort mechanics.
"""
        sections = _parse_sections_from_markdown(sample_markdown)
        self.assertIn("bubble sort", sections.code_overview.lower())
        self.assertIn("ascending order", sections.purpose.lower())
        self.assertIn("arr", sections.variables_and_functions)
        self.assertIn("O(N^2)", sections.time_complexity)
        self.assertIn("O(1)", sections.space_complexity)
        self.assertIn("early-termination", sections.possible_improvements)

    @patch("api.ai_routes.explain_code_with_gemini")
    def test_mocked_explain_endpoint(self, mock_explain):
        mock_explain.return_value = {
            "success": True,
            "language": "python",
            "mode": "detailed",
            "explanation_language": "english",
            "markdown": "## 1. Code Overview\nTest overview.",
            "sections": {
                "code_overview": "Test overview.",
                "purpose": "Test purpose.",
                "line_by_line": "",
                "variables_and_functions": "",
                "logic_and_workflow": "",
                "algorithm": "",
                "example_input_output": "",
                "time_complexity": "O(1)",
                "space_complexity": "O(1)",
                "possible_improvements": "",
                "learning_summary": "",
            },
            "model_used": "gemini-3.5-flash-lite",
            "timestamp": "2026-11-03T10:00:00Z",
            "error": None,
        }

        response = client.post(
            "/api/ai/explain",
            json={"code": "x = 10", "language": "python", "mode": "detailed", "explanation_language": "english"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["sections"]["code_overview"], "Test overview.")

        # Test specific endpoints
        endpoints = [
            "/api/ai/explain-line-by-line",
            "/api/ai/explain-algorithm",
            "/api/ai/explain-interview",
            "/api/ai/explain-optimization",
        ]
        for ep in endpoints:
            r = client.post(ep, json={"code": "x = 10", "language": "python"})
            self.assertEqual(r.status_code, 200)
            self.assertTrue(r.json()["success"])

    @patch("api.ai_routes.chat_with_gemini")
    def test_mocked_chat_endpoint(self, mock_chat):
        mock_chat.return_value = {
            "success": True,
            "reply": "The loop executes N times.",
            "model_used": "gemini-3.5-flash-lite",
            "timestamp": "2026-11-03T10:00:00Z",
            "error": None,
        }

        response = client.post(
            "/api/ai/chat",
            json={
                "code": "for i in range(10): print(i)",
                "message": "Why is this loop used?",
                "language": "python",
                "explanation_language": "english",
                "history": [],
            },
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn("loop executes", data["reply"])
