"""Production Static Analyzer for C (C99/C11/C17).

Provides static memory safety diagnosis, complexity estimation,
and algorithmic optimization without executing user code.
"""

import re
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

from models.schemas import (
    AnalyzeResponse,
    SyntaxErrorInfo,
    CodePattern,
    OptimizationSuggestion,
    ComplexityEstimate,
    ASTMetrics,
    BenchmarkModel,
)
from .base import BaseAnalyzer
from .common import check_bracket_balance, calculate_structural_complexity, generate_benchmark_model


class CAnalyzer(BaseAnalyzer):
    """Production static analyzer for C language."""

    def __init__(self):
        super().__init__(language_id="c", display_name="C", is_supported=True)

    def analyze(self, code: str, options: Optional[Dict[str, Any]] = None) -> AnalyzeResponse:
        code_clean = code.strip() if code else ""
        timestamp = datetime.now(timezone.utc).isoformat()

        if not code_clean:
            return AnalyzeResponse(
                language="c",
                supported=True,
                status="success",
                message="No code provided to analyze.",
                timestamp=timestamp,
                patterns=[],
                optimizations=[],
                ast_metrics=ASTMetrics(
                    total_nodes=0,
                    functions_count=0,
                    classes_count=0,
                    loops_count=0,
                    branches_count=0,
                    max_nesting_depth=0,
                    lines_of_code=0,
                    comment_lines=0,
                ),
            )

        # 1. Syntax / Bracket Check
        bracket_err = check_bracket_balance(code)
        if bracket_err:
            err_line, err_col, err_msg = bracket_err
            lines = code.splitlines()
            snippet = lines[err_line - 1].strip() if 0 < err_line <= len(lines) else None
            return AnalyzeResponse(
                language="c",
                supported=True,
                status="syntax_error",
                message=f"Syntax Error at line {err_line}, column {err_col}: {err_msg}",
                timestamp=timestamp,
                syntax_error=SyntaxErrorInfo(
                    has_error=True,
                    message=err_msg,
                    line=err_line,
                    column=err_col,
                    text=snippet,
                    friendly_explanation="Check matching of curly braces '{ ... }', parentheses '( ... )', or brackets.",
                ),
            )

        lines = code.splitlines()
        patterns: List[CodePattern] = []
        optimizations: List[OptimizationSuggestion] = []

        # 2. Check for Unsafe String Functions (Buffer Overflow)
        unsafe_funcs = [("strcpy", "strncpy"), ("strcat", "strncat"), ("gets", "fgets"), ("sprintf", "snprintf")]
        for line_idx, line in enumerate(lines, start=1):
            clean = re.sub(r'//.*$|/\*.*?\*/', '', line)
            for bad_fn, safe_fn in unsafe_funcs:
                if re.search(rf'\b{bad_fn}\s*\(', clean):
                    patterns.append(
                        CodePattern(
                            id=f"c-unsafe-func-{line_idx}",
                            title=f"Unsafe Function Call: '{bad_fn}' (Buffer Overflow Risk)",
                            severity="high",
                            category="best_practice",
                            line=line_idx,
                            column=clean.find(bad_fn) + 1,
                            snippet=clean.strip(),
                            explanation=(
                                f"`{bad_fn}()` does not perform boundary checks on the destination buffer. "
                                f"If input exceeds the buffer size, it causes stack memory corruption and severe security vulnerabilities."
                            ),
                            suggestion=f"Replace `{bad_fn}()` with bounded alternative `{safe_fn}()` specifying `sizeof(destination)`.",
                        )
                    )
                    optimizations.append(
                        OptimizationSuggestion(
                            id=f"opt-c-safe-{line_idx}",
                            title=f"Replace Unbounded {bad_fn}() with Bounded {safe_fn}()",
                            category="best_practice",
                            impact="high",
                            confidence="high",
                            explanation=(
                                f"Using bounded string functions ({safe_fn}) guarantees string termination and prevents "
                                "stack-smashing and segmentation faults caused by buffer overruns."
                            ),
                            original_code=clean.strip(),
                            optimized_code=f"// Bounded buffer copy with size limit\n{safe_fn}(dest, src, sizeof(dest) - 1);\ndest[sizeof(dest) - 1] = '\\0';",
                            diff=f"- {clean.strip()}\n+ {safe_fn}(dest, src, sizeof(dest) - 1);",
                            theoretical_benefit="Prevents buffer overflows, stack corruption, and undefined behavior.",
                        )
                    )
                    break
            if patterns:
                break

        # 3. Check for Unchecked malloc() / calloc()
        if re.search(r'\b(malloc|calloc)\s*\(', code) and not re.search(r'==\s*NULL|!=\s*NULL|!\s*[a-zA-Z_]\w*', code):
            for line_idx, line in enumerate(lines, start=1):
                clean = re.sub(r'//.*$|/\*.*?\*/', '', line)
                if re.search(r'\b(malloc|calloc)\s*\(', clean):
                    patterns.append(
                        CodePattern(
                            id=f"c-unchecked-malloc-{line_idx}",
                            title="Unchecked Dynamic Allocation (Null Pointer Dereference Risk)",
                            severity="high",
                            category="best_practice",
                            line=line_idx,
                            column=1,
                            snippet=clean.strip(),
                            explanation=(
                                "Memory allocation (`malloc`/`calloc`) returns `NULL` if system memory is exhausted. "
                                "Dereferencing without checking against `NULL` triggers immediate segmentation fault (SIGSEGV)."
                            ),
                            suggestion="Check if the returned pointer is NULL before accessing its contents.",
                        )
                    )
                    optimizations.append(
                        OptimizationSuggestion(
                            id=f"opt-c-malloc-guard-{line_idx}",
                            title="Add NULL Pointer Allocation Guard",
                            category="best_practice",
                            impact="high",
                            confidence="high",
                            explanation="Defensive null checking ensures the application handles out-of-memory gracefully without crashing.",
                            original_code=clean.strip() + "\nptr[0] = value;",
                            optimized_code=clean.strip() + "\nif (ptr == NULL) {\n    fprintf(stderr, \"Memory allocation failed\\n\");\n    return -1;\n}\nptr[0] = value;",
                            diff="+ if (ptr == NULL) { return -1; }",
                            theoretical_benefit="Eliminates null pointer dereference crashes and undefined behavior.",
                        )
                    )
                    break

        # 4. Check for Multiple Consecutive printf() calls
        consecutive_prints = []
        for line_idx, line in enumerate(lines, start=1):
            clean = re.sub(r'//.*$|/\*.*?\*/', '', line).strip()
            if re.match(r'printf\s*\(', clean):
                consecutive_prints.append((line_idx, clean))
            else:
                if len(consecutive_prints) >= 2:
                    break
                consecutive_prints = []

        if len(consecutive_prints) >= 2:
            first_l, first_snippet = consecutive_prints[0]
            count = len(consecutive_prints)
            patterns.append(
                CodePattern(
                    id=f"c-multi-printf-{first_l}",
                    title=f"Multiple Consecutive printf() Calls ({count} statements)",
                    severity="medium",
                    category="performance",
                    line=first_l,
                    column=1,
                    snippet=first_snippet,
                    explanation=(
                        f"Detected {count} consecutive `printf()` calls. Repeated I/O operations trigger multiple context switches "
                        "and buffer writes to `stdout`."
                    ),
                    suggestion="Consolidate multiple printf calls into a single call with newline escapes ('\\n') or iterate through an array with a loop.",
                )
            )
            optimizations.append(
                OptimizationSuggestion(
                    id=f"opt-c-printf-loop-{first_l}",
                    title="Consolidate printf() Calls into Single String or Loop",
                    category="performance",
                    impact="medium",
                    confidence="high",
                    explanation="Minimizes standard library write syscalls and reduces binary instruction bloat.",
                    original_code="\n".join(s for _, s in consecutive_prints),
                    optimized_code="// Option 1: Loop over array\nconst char* lines[] = {\"line1\", \"line2\", \"line3\"};\nfor (int i = 0; i < 3; i++) {\n    printf(\"%s\\n\", lines[i]);\n}\n\n// Option 2: Single formatted call\nprintf(\"line1\\nline2\\nline3\\n\");",
                    diff="+ printf(\"Consolidated output with single I/O write\\n\");",
                    theoretical_benefit="Reduces user/kernel mode transitions and standard I/O buffer flushes.",
                )
            )

        # 5. Check for Quadratic Nested Loops
        complexity, ast_metrics = calculate_structural_complexity(code)
        if ast_metrics.max_nesting_depth >= 2:
            patterns.append(
                CodePattern(
                    id="c-nested-loops",
                    title=f"Nested Iteration Detected ({complexity.time_complexity})",
                    severity="high",
                    category="complexity",
                    line=1,
                    column=1,
                    snippet="for (...) { for (...) { ... } }",
                    explanation=(
                        f"Nested loops create quadratic {complexity.time_complexity} operations. For large inputs (N > 10,000), "
                        "operation counts grow to millions, degrading system throughput."
                    ),
                    suggestion="Investigate if sorting + two-pointer, hash table indexing, or binary search can reduce complexity to O(N) or O(N log N).",
                )
            )
            optimizations.append(
                OptimizationSuggestion(
                    id="opt-c-flatten-loops",
                    title="Algorithmic Optimization: Flatten Nested Search",
                    category="complexity",
                    impact="high",
                    confidence="high",
                    explanation="Linear or binary indexed search reduces computational overhead from polynomial to linear.",
                    original_code="for (int i = 0; i < n; i++) {\n    for (int j = 0; j < m; j++) {\n        if (arr1[i] == arr2[j]) process();\n    }\n}",
                    optimized_code="// Pre-sort arr2 and use bsearch() for O(N log M) instead of O(N*M)\nqsort(arr2, m, sizeof(int), cmp_ints);\nfor (int i = 0; i < n; i++) {\n    if (bsearch(&arr1[i], arr2, m, sizeof(int), cmp_ints)) process();\n}",
                    diff="- nested loop pairwise search\n+ qsort + bsearch binary lookup",
                    theoretical_benefit="Reduces asymptotic operations from O(N²) to O(N log N).",
                )
            )

        benchmark_model = generate_benchmark_model(complexity, optimizations)

        return AnalyzeResponse(
            language="c",
            supported=True,
            status="success",
            message=f"C static analysis completed successfully. Found {len(patterns)} pattern(s) and {len(optimizations)} optimization(s).",
            timestamp=timestamp,
            syntax_error=SyntaxErrorInfo(has_error=False),
            complexity=complexity,
            patterns=patterns,
            optimizations=optimizations,
            ast_metrics=ast_metrics,
            benchmark_model=benchmark_model,
        )
