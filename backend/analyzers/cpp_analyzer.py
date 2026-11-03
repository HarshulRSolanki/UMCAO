"""Production Static Analyzer for C++ (C++17/C++20).

Provides memory safety checks, heavy-copy detection, and algorithmic
complexity estimation without executing user code.
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


class CppAnalyzer(BaseAnalyzer):
    """Production static analyzer for C++ language."""

    def __init__(self):
        super().__init__(language_id="cpp", display_name="C++", is_supported=True)

    def analyze(self, code: str, options: Optional[Dict[str, Any]] = None) -> AnalyzeResponse:
        code_clean = code.strip() if code else ""
        timestamp = datetime.now(timezone.utc).isoformat()

        if not code_clean:
            return AnalyzeResponse(
                language="cpp",
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
                language="cpp",
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
                    friendly_explanation="Check matching of curly braces '{ ... }', template brackets '< ... >', or parentheses.",
                ),
            )

        lines = code.splitlines()
        patterns: List[CodePattern] = []
        optimizations: List[OptimizationSuggestion] = []

        # 2. Check for Heavy Pass-By-Value Container Copies
        heavy_types = ["std::vector", "vector", "std::string", "string", "std::map", "map", "std::set", "set"]
        for line_idx, line in enumerate(lines, start=1):
            clean = re.sub(r'//.*$|/\*.*?\*/', '', line)
            # Match function signature like: void func(std::vector<int> items)
            for ht in heavy_types:
                pattern_re = rf'\b{re.escape(ht)}\s*(?:<[^>]+>)?\s+([a-zA-Z_]\w*)\s*(?:,|\))'
                match = re.search(pattern_re, clean)
                # Ensure it's not const or reference
                if match and "&" not in clean.split(match.group(0))[0]:
                    var_name = match.group(1)
                    patterns.append(
                        CodePattern(
                            id=f"cpp-pass-by-value-{line_idx}",
                            title=f"Expensive Pass-By-Value: '{ht}' (Deep Copy Overhead)",
                            severity="high",
                            category="performance",
                            line=line_idx,
                            column=match.start() + 1,
                            snippet=clean.strip(),
                            explanation=(
                                f"Passing `{ht}` by value triggers an automatic deep copy of the underlying dynamic array / heap buffer. "
                                f"For collections with N items, every function invocation incurs an O(N) memory allocation and copy penalty."
                            ),
                            suggestion=f"Pass by const reference (`const {ht}& {var_name}`) or use `std::string_view` / `std::span`.",
                        )
                    )
                    optimizations.append(
                        OptimizationSuggestion(
                            id=f"opt-cpp-const-ref-{line_idx}",
                            title="Pass Heavy Containers by Const Reference",
                            category="performance",
                            impact="high",
                            confidence="high",
                            explanation=(
                                "Passing by const reference eliminates duplicate heap allocations and copy constructors, "
                                "reducing argument passing overhead from O(N) to O(1) pointer-sized passing."
                            ),
                            original_code=clean.strip(),
                            optimized_code=re.sub(rf'\b{re.escape(ht)}\b', f"const {ht}&", clean.strip()),
                            diff=f"- {clean.strip()}\n+ const {ht}& {var_name}",
                            theoretical_benefit="Reduces function parameter passing time from O(N) copy down to O(1) constant-time reference.",
                        )
                    )
                    break
            if patterns:
                break

        # 3. Check for Raw Pointers (new / delete)
        if re.search(r'\bnew\s+[a-zA-Z_]\w*', code) and not re.search(r'\bunique_ptr|make_unique|shared_ptr\b', code):
            for line_idx, line in enumerate(lines, start=1):
                clean = re.sub(r'//.*$|/\*.*?\*/', '', line)
                if re.search(r'\bnew\s+', clean):
                    patterns.append(
                        CodePattern(
                            id=f"cpp-raw-new-{line_idx}",
                            title="Raw Pointer Allocation ('new') - Consider Modern Smart Pointers",
                            severity="medium",
                            category="best_practice",
                            line=line_idx,
                            column=1,
                            snippet=clean.strip(),
                            explanation=(
                                "Using manual `new` and `delete` violates C++ RAII (Resource Acquisition Is Initialization) idioms "
                                "and risks memory leaks if exceptions are thrown before `delete` executes."
                            ),
                            suggestion="Adopt `std::unique_ptr` with `std::make_unique<T>()` for automatic deterministic cleanup.",
                        )
                    )
                    optimizations.append(
                        OptimizationSuggestion(
                            id=f"opt-cpp-smart-ptr-{line_idx}",
                            title="Migrate to std::make_unique for Exception-Safe RAII",
                            category="best_practice",
                            impact="medium",
                            confidence="high",
                            explanation="std::unique_ptr automatically deallocates heap memory upon leaving scope, even during unexpected stack unwinding.",
                            original_code=clean.strip(),
                            optimized_code="// Modern C++ RAII smart pointer\nauto ptr = std::make_unique<MyClass>();",
                            diff="- MyClass* ptr = new MyClass();\n+ auto ptr = std::make_unique<MyClass>();",
                            theoretical_benefit="Guarantees zero memory leaks and exception safety without manual delete calls.",
                        )
                    )
                    break

        # 4. Check for Multiple Consecutive std::cout statements
        consecutive_couts = []
        for line_idx, line in enumerate(lines, start=1):
            clean = re.sub(r'//.*$|/\*.*?\*/', '', line).strip()
            if re.search(r'\b(std::cout|cout)\s*<<', clean):
                consecutive_couts.append((line_idx, clean))
            else:
                if len(consecutive_couts) >= 2:
                    break
                consecutive_couts = []

        if len(consecutive_couts) >= 2:
            first_l, first_snippet = consecutive_couts[0]
            count = len(consecutive_couts)
            patterns.append(
                CodePattern(
                    id=f"cpp-multi-cout-{first_l}",
                    title=f"Multiple Consecutive std::cout Streams ({count} calls)",
                    severity="medium",
                    category="performance",
                    line=first_l,
                    column=1,
                    snippet=first_snippet,
                    explanation=(
                        f"Detected {count} consecutive `std::cout` stream calls. If coupled with `std::endl`, "
                        "each call explicitly flushes the I/O buffer to the OS terminal, creating substantial stream bottlenecks."
                    ),
                    suggestion="Consolidate outputs into a loop or single chained stream expression, and prefer '\\n' over 'std::endl'.",
                )
            )
            optimizations.append(
                OptimizationSuggestion(
                    id=f"opt-cpp-cout-loop-{first_l}",
                    title="Consolidate Stream Output & Replace std::endl with '\\n'",
                    category="performance",
                    impact="medium",
                    confidence="high",
                    explanation="std::endl triggers an expensive std::flush on every call. Using '\\n' allows the stream buffer to flush in batches.",
                    original_code="\n".join(s for _, s in consecutive_couts),
                    optimized_code="// Option 1: Loop over vector/array\nfor (const auto& item : items) {\n    std::cout << item << '\\n';\n}\n\n// Option 2: Chained output\nstd::cout << \"line1\\n\" << \"line2\\n\";",
                    diff="- std::cout << val << std::endl;\n+ std::cout << val << '\\n';",
                    theoretical_benefit="Prevents unnecessary stream buffer flushes and accelerates terminal I/O.",
                )
            )

        # 5. Check for Quadratic Nested Loops
        complexity, ast_metrics = calculate_structural_complexity(code)
        if ast_metrics.max_nesting_depth >= 2:
            patterns.append(
                CodePattern(
                    id="cpp-nested-loops",
                    title=f"Nested Loop Detected ({complexity.time_complexity})",
                    severity="high",
                    category="complexity",
                    line=1,
                    column=1,
                    snippet="for (...) { for (...) { ... } }",
                    explanation=(
                        f"Nested iteration exhibits quadratic {complexity.time_complexity} time complexity. "
                        "Pairwise comparisons grow rapidly as input size scales."
                    ),
                    suggestion="Consider using `std::unordered_map` or `std::unordered_set` for O(1) hash table lookup.",
                )
            )
            optimizations.append(
                OptimizationSuggestion(
                    id="opt-cpp-unordered-map",
                    title="Flatten Nested Search with std::unordered_map",
                    category="complexity",
                    impact="high",
                    confidence="high",
                    explanation="Pre-hashing elements into an std::unordered_map reduces pairwise search from O(N²) to linear O(N).",
                    original_code="for (const auto& a : list_a) {\n    for (const auto& b : list_b) {\n        if (a.id == b.id) matches.push_back({a, b});\n    }\n}",
                    optimized_code="std::unordered_map<int, Item> b_map;\nfor (const auto& b : list_b) b_map[b.id] = b;\nfor (const auto& a : list_a) {\n    if (b_map.count(a.id)) matches.push_back({a, b_map[a.id]});\n}",
                    diff="- nested pairwise comparison\n+ std::unordered_map lookup",
                    theoretical_benefit="Reduces computation from quadratic O(N²) down to linear O(N).",
                )
            )

        benchmark_model = generate_benchmark_model(complexity, optimizations)

        return AnalyzeResponse(
            language="cpp",
            supported=True,
            status="success",
            message=f"C++ static analysis completed successfully. Found {len(patterns)} pattern(s) and {len(optimizations)} optimization(s).",
            timestamp=timestamp,
            syntax_error=SyntaxErrorInfo(has_error=False),
            complexity=complexity,
            patterns=patterns,
            optimizations=optimizations,
            ast_metrics=ast_metrics,
            benchmark_model=benchmark_model,
        )
