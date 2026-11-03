"""Shared analysis helpers and utilities for multi-language analyzers."""

import re
import math
from typing import List, Tuple, Optional, Dict, Any
from models.schemas import (
    ComplexityEstimate,
    OptimizationSuggestion,
    BenchmarkModel,
    BenchmarkPoint,
    ASTMetrics,
)


def check_bracket_balance(code: str) -> Optional[Tuple[int, int, str]]:
    """Checks for unmatched braces, brackets, and parentheses.

    Returns (line, column, message) if unmatched, else None.
    """
    stack = []
    pairs = {')': '(', '}': '{', ']': '['}
    lines = code.splitlines()

    # Track in_string or in_comment to avoid false positives
    in_single_quote = False
    in_double_quote = False
    in_block_comment = False

    for line_idx, line in enumerate(lines, start=1):
        col_idx = 0
        while col_idx < len(line):
            ch = line[col_idx]

            # Block comment start/end
            if not in_single_quote and not in_double_quote:
                if in_block_comment:
                    if ch == '*' and col_idx + 1 < len(line) and line[col_idx + 1] == '/':
                        in_block_comment = False
                        col_idx += 2
                        continue
                    col_idx += 1
                    continue
                else:
                    if ch == '/' and col_idx + 1 < len(line) and line[col_idx + 1] == '*':
                        in_block_comment = True
                        col_idx += 2
                        continue
                    if ch == '/' and col_idx + 1 < len(line) and line[col_idx + 1] == '/':
                        break  # Line comment, rest of line is ignored

            # Quotes
            if not in_block_comment:
                if ch == '"' and not in_single_quote and (col_idx == 0 or line[col_idx - 1] != '\\'):
                    in_double_quote = not in_double_quote
                elif ch == "'" and not in_double_quote and (col_idx == 0 or line[col_idx - 1] != '\\'):
                    in_single_quote = not in_single_quote

            if not in_single_quote and not in_double_quote and not in_block_comment:
                if ch in "({[":
                    stack.append((ch, line_idx, col_idx + 1))
                elif ch in ")}]":
                    if not stack:
                        return (line_idx, col_idx + 1, f"Unmatched closing bracket '{ch}' without opening bracket.")
                    top, top_l, top_c = stack.pop()
                    if pairs[ch] != top:
                        return (line_idx, col_idx + 1, f"Mismatched bracket: expected closing for '{top}' (from line {top_l}), but found '{ch}'.")

            col_idx += 1

    if stack:
        top, top_l, top_c = stack[-1]
        return (top_l, top_c, f"Unclosed opening bracket '{top}'. Expected matching bracket.")

    return None


def calculate_structural_complexity(code: str) -> Tuple[ComplexityEstimate, ASTMetrics]:
    """Computes Big-O complexity estimate and AST metrics based on structural loop analysis."""
    lines = code.splitlines()
    loc = len([ln for ln in lines if ln.strip() and not ln.strip().startswith(("//", "/*", "*", "#"))])
    comment_lines = len([ln for ln in lines if ln.strip().startswith(("//", "/*", "*", "#"))])

    # Find loops and nested depths
    loop_regex = re.compile(r'\b(for|while|do)\b', re.IGNORECASE)
    branch_regex = re.compile(r'\b(if|else\s+if|switch|case|catch)\b')
    func_regex = re.compile(r'\b(function|void|int|char|double|float|bool|boolean|String|auto|public|private|protected)\b.*?\(')

    total_loops = 0
    total_branches = len(branch_regex.findall(code))
    functions_count = max(len(func_regex.findall(code)), 1 if loc > 0 else 0)

    # Track loop nesting using brace depth
    current_brace_depth = 0
    active_loop_depths = []
    max_nesting_depth = 0

    for line in lines:
        clean = re.sub(r'//.*$|/\*.*?\*/', '', line).strip()
        if loop_regex.search(clean):
            total_loops += 1
            active_loop_depths.append(current_brace_depth)

        # Update brace depth
        open_braces = clean.count('{')
        close_braces = clean.count('}')
        current_brace_depth += (open_braces - close_braces)

        # Calculate current active loop nesting
        if active_loop_depths:
            nesting = len([d for d in active_loop_depths if d <= current_brace_depth])
            if nesting > max_nesting_depth:
                max_nesting_depth = nesting
            # Prune completed loop depths
            active_loop_depths = [d for d in active_loop_depths if d <= current_brace_depth]

    # Big-O estimation
    if max_nesting_depth >= 3:
        time_c = "O(n^3)"
        space_c = "O(1)"
        confidence = "medium"
        reasons = [
            f"Cubic nested loop structure identified (depth = {max_nesting_depth}).",
            "Assuming loop boundaries iterate across input dimension N.",
        ]
    elif max_nesting_depth == 2:
        time_c = "O(n^2)"
        space_c = "O(1)"
        confidence = "high"
        reasons = [
            "Quadratic nested loops discovered operating sequentially.",
            "Worst-case pairwise operations scale proportionally to N².",
        ]
    elif max_nesting_depth == 1 or total_loops > 0:
        time_c = "O(n)"
        space_c = "O(1)"
        confidence = "high"
        reasons = [
            "Single linear loop iterating over input elements.",
            "Direct sequential scan through data structure.",
        ]
    else:
        time_c = "O(1)"
        space_c = "O(1)"
        confidence = "high"
        reasons = [
            "No iterative loop blocks or recursive call trees detected.",
            "Executes sequentially in constant bounded time.",
        ]

    uncertainty_factors = [
        "Loop bounds are dynamic and determined at runtime by input data size.",
        "Early break, return, or exit guards may lower average-case complexity.",
        "External standard library invocations contain their own algorithmic complexities.",
    ]

    complexity = ComplexityEstimate(
        time_complexity=time_c,
        space_complexity=space_c,
        confidence=confidence,
        reasons=reasons,
        uncertainty_factors=uncertainty_factors,
    )

    total_ast_nodes = max(loc * 3 + total_loops * 4 + total_branches * 3 + 12, loc)

    metrics = ASTMetrics(
        total_nodes=total_ast_nodes,
        functions_count=functions_count,
        classes_count=1 if re.search(r'\bclass\b', code) else 0,
        loops_count=total_loops,
        branches_count=total_branches,
        max_nesting_depth=max(max_nesting_depth, 1 if total_loops > 0 else 0),
        lines_of_code=loc,
        comment_lines=comment_lines,
    )

    return complexity, metrics


def generate_benchmark_model(
    complexity: ComplexityEstimate, optimizations: List[OptimizationSuggestion]
) -> BenchmarkModel:
    """Generates standard Chart.js scaling benchmark curves."""
    input_sizes = [10, 50, 100, 200, 400, 800, 1000]
    time_c = complexity.time_complexity
    baseline_label = f"Current Implementation ({time_c})"

    if time_c == "O(2^n)":
        optimized_label = "With Memoization (O(n))"
        curve_type = "exponential_vs_linear"
        points = [
            BenchmarkPoint(input_size=n, baseline_ops=min(2**min(n, 20), 100000), optimized_ops=n)
            for n in input_sizes
        ]
    elif time_c == "O(n^3)":
        optimized_label = "Flattened Structure (O(n log n))"
        curve_type = "cubic_vs_loglinear"
        points = [
            BenchmarkPoint(input_size=n, baseline_ops=min(n**3, 500000), optimized_ops=round(n * math.log2(max(n, 2)), 1))
            for n in input_sizes
        ]
    elif time_c == "O(n^2)":
        optimized_label = "Hash Map / Set Indexing (O(n))"
        curve_type = "quadratic_vs_linear"
        points = [
            BenchmarkPoint(input_size=n, baseline_ops=n**2, optimized_ops=n * 2)
            for n in input_sizes
        ]
    elif time_c == "O(n)":
        optimized_label = "Vectorized / Batch Iteration (O(n))"
        curve_type = "linear_scaling"
        points = [
            BenchmarkPoint(input_size=n, baseline_ops=round(n * 3.0, 1), optimized_ops=round(n * 1.1, 1))
            for n in input_sizes
        ]
    else:
        optimized_label = "Constant Time Execution (O(1))"
        curve_type = "constant_scaling"
        points = [
            BenchmarkPoint(input_size=n, baseline_ops=1.0, optimized_ops=1.0)
            for n in input_sizes
        ]

    return BenchmarkModel(
        available=True,
        curve_type=curve_type,
        baseline_label=baseline_label,
        optimized_label=optimized_label,
        data_points=points,
    )
