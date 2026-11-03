"""Unit tests for UMCAO Backend Static Analysis Engine."""

import sys
import os
import unittest

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from analyzers.python_analyzer import PythonAnalyzer
from analyzers.registry import analyzer_registry
from models.schemas import AnalyzeRequest
from api.routes import analyze_code, get_languages, get_sample_presets, health_check


class TestUMCAOAnalyzer(unittest.TestCase):
    def test_python_syntax_error(self):
        analyzer = PythonAnalyzer()
        broken_code = "def broken_func(x, y)\n    return x + y"
        res = analyzer.analyze(broken_code)

        self.assertEqual(res.status, "syntax_error")
        self.assertTrue(res.syntax_error.has_error)
        self.assertEqual(res.syntax_error.line, 1)
        self.assertTrue(
            "colon" in res.syntax_error.friendly_explanation.lower()
            or "header" in res.syntax_error.friendly_explanation.lower()
        )

    def test_nested_loops_quadratic_complexity(self):
        analyzer = PythonAnalyzer()
        code = """
def find_pairs(nums):
    res = []
    for i in nums:
        for j in nums:
            if i + j == 10:
                res.append((i, j))
    return res
"""
        res = analyzer.analyze(code)
        self.assertEqual(res.status, "success")
        self.assertEqual(res.complexity.time_complexity, "O(n^2)")
        pattern_titles = [p.title for p in res.patterns]
        self.assertTrue(any("Nested Loop Detected" in title for title in pattern_titles))
        self.assertTrue(len(res.optimizations) > 0)

    def test_string_concatenation_detection(self):
        analyzer = PythonAnalyzer()
        code = """
def concat_all(items):
    s = ""
    for item in items:
        s += str(item)
    return s
"""
        res = analyzer.analyze(code)
        self.assertEqual(res.status, "success")
        pattern_ids = [p.id for p in res.patterns]
        self.assertTrue(any("str-concat" in pid for pid in pattern_ids))
        self.assertTrue(len(res.optimizations) > 0)

    def test_unmemoized_recursion(self):
        analyzer = PythonAnalyzer()
        code = """
def fib(n):
    if n <= 1:
        return n
    return fib(n - 1) + fib(n - 2)
"""
        res = analyzer.analyze(code)
        self.assertEqual(res.status, "success")
        self.assertEqual(res.complexity.time_complexity, "O(2^n)")
        pattern_ids = [p.id for p in res.patterns]
        self.assertTrue(any("exp-recursion" in pid for pid in pattern_ids))

    def test_unidiomatic_range_len(self):
        analyzer = PythonAnalyzer()
        code = """
def print_all(items):
    for i in range(len(items)):
        print(i, items[i])
"""
        res = analyzer.analyze(code)
        self.assertEqual(res.status, "success")
        pattern_ids = [p.id for p in res.patterns]
        self.assertTrue(any("range-len" in pid for pid in pattern_ids))

    def test_multiple_prints_detection(self):
        analyzer = PythonAnalyzer()
        code = """
print("Item 1")
print("Item 2")
print("Item 3")
"""
        res = analyzer.analyze(code)
        self.assertEqual(res.status, "success")
        pattern_ids = [p.id for p in res.patterns]
        self.assertTrue(any("multiple-print" in pid for pid in pattern_ids))
        self.assertTrue(len(res.optimizations) > 0)
        opt = [o for o in res.optimizations if "print" in o.id][0]
        self.assertIn("loop", opt.optimized_code.lower())
        self.assertIn("def print_all", opt.optimized_code)
        self.assertIn("for item in", opt.optimized_code)

    def test_unsupported_language_stub(self):
        js_analyzer = analyzer_registry.get_analyzer("javascript")
        self.assertIsNotNone(js_analyzer)
        self.assertFalse(js_analyzer.is_supported)

        res = js_analyzer.analyze("function test() { return 0; }")
        self.assertFalse(res.supported)
        self.assertEqual(res.status, "unsupported_language")
        self.assertTrue("in development" in res.message.lower())
        self.assertIsNotNone(res.roadmap_info)
        self.assertTrue(
            "Babel" in res.roadmap_info.planned_engine
            or "Tree-sitter" in res.roadmap_info.planned_engine
        )

    def test_c_cpp_java_supported(self):
        c_analyzer = analyzer_registry.get_analyzer("c")
        self.assertIsNotNone(c_analyzer)
        self.assertTrue(c_analyzer.is_supported)

        cpp_analyzer = analyzer_registry.get_analyzer("cpp")
        self.assertIsNotNone(cpp_analyzer)
        self.assertTrue(cpp_analyzer.is_supported)

        java_analyzer = analyzer_registry.get_analyzer("java")
        self.assertIsNotNone(java_analyzer)
        self.assertTrue(java_analyzer.is_supported)

    def test_fastapi_endpoints(self):
        # Health check
        health_res = health_check()
        self.assertEqual(health_res["status"], "healthy")

        # Languages list
        lang_res = get_languages()
        self.assertEqual(lang_res["status"], "success")
        languages = lang_res["languages"]
        lang_ids = [l["id"] for l in languages]
        self.assertIn("python", lang_ids)
        self.assertIn("c", lang_ids)
        self.assertIn("cpp", lang_ids)
        self.assertIn("java", lang_ids)
        self.assertIn("javascript", lang_ids)

        # Samples endpoint
        sample_res = get_sample_presets(language="python")
        self.assertTrue(len(sample_res["samples"]) > 0)

        # Analyze endpoint
        analyze_res = analyze_code(
            AnalyzeRequest(
                language="python",
                code="def hello():\n    return 'world'",
            )
        )
        self.assertEqual(analyze_res.status, "success")
        self.assertEqual(analyze_res.complexity.time_complexity, "O(1)")


if __name__ == "__main__":
    unittest.main()
