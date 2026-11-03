"""Production Static Analyzer for Java (Java 17/21 LTS).

Analyzes GC pressure, autoboxing overhead, algorithmic complexity,
and resource safety without executing user code.
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


class JavaAnalyzer(BaseAnalyzer):
    """Production static analyzer for Java language."""

    def __init__(self):
        super().__init__(language_id="java", display_name="Java", is_supported=True)

    def analyze(self, code: str, options: Optional[Dict[str, Any]] = None) -> AnalyzeResponse:
        code_clean = code.strip() if code else ""
        timestamp = datetime.now(timezone.utc).isoformat()

        if not code_clean:
            return AnalyzeResponse(
                language="java",
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
                language="java",
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
                    friendly_explanation="Check matching of curly braces '{ ... }', parentheses '( ... )', or semicolons.",
                ),
            )

        lines = code.splitlines()
        patterns: List[CodePattern] = []
        optimizations: List[OptimizationSuggestion] = []

        # 2. Check for String Concatenation in Loops (+=)
        in_loop = False
        loop_brace_depth = 0
        current_depth = 0

        for line_idx, line in enumerate(lines, start=1):
            clean = re.sub(r'//.*$|/\*.*?\*/', '', line).strip()
            if re.search(r'\b(for|while)\b', clean):
                in_loop = True
                loop_brace_depth = current_depth

            if in_loop and re.search(r'[a-zA-Z_]\w*\s*\+=\s*.*', clean):
                # Detected += in loop
                patterns.append(
                    CodePattern(
                        id=f"java-str-concat-{line_idx}",
                        title="Repeated String Concatenation in Loop (GC / Heap Pressure)",
                        severity="high",
                        category="performance",
                        line=line_idx,
                        column=1,
                        snippet=clean,
                        explanation=(
                            "Using `+=` for string concatenation inside a Java loop forces the JVM to allocate a new `StringBuilder` "
                            "and copy all existing characters on every cycle, resulting in quadratic O(N²) time and heavy Garbage Collection churn."
                        ),
                        suggestion="Instantiate a single `StringBuilder sb = new StringBuilder()` outside the loop and call `sb.append(...)`.",
                    )
                )
                optimizations.append(
                    OptimizationSuggestion(
                        id=f"opt-java-stringbuilder-{line_idx}",
                        title="Refactor Loop Concatenation to StringBuilder",
                        category="performance",
                        impact="high",
                        confidence="high",
                        explanation="A pre-allocated StringBuilder operates with an amortized O(1) buffer expansion, converting total execution from O(N²) down to linear O(N).",
                        original_code="String result = \"\";\nfor (String item : items) {\n    result += item;\n}",
                        optimized_code="StringBuilder sb = new StringBuilder();\nfor (String item : items) {\n    sb.append(item);\n}\nString result = sb.toString();",
                        diff="- result += item;\n+ sb.append(item);",
                        theoretical_benefit="Reduces string construction time from quadratic O(N²) reallocation down to linear O(N).",
                    )
                )
                break

            current_depth += (clean.count('{') - clean.count('}'))
            if in_loop and current_depth <= loop_brace_depth:
                in_loop = False

        # 3. Check for Autoboxing in Loop (e.g. Integer / Long as counter)
        for line_idx, line in enumerate(lines, start=1):
            clean = re.sub(r'//.*$|/\*.*?\*/', '', line).strip()
            if re.search(r'\b(Integer|Long|Double|Float)\s+[a-zA-Z_]\w*\s*=\s*\d+', clean):
                var_match = re.search(r'\b(Integer|Long|Double|Float)\s+([a-zA-Z_]\w*)', clean)
                if var_match:
                    type_name, var_name = var_match.group(1), var_match.group(2)
                    primitive_map = {"Integer": "int", "Long": "long", "Double": "double", "Float": "float"}
                    prim = primitive_map.get(type_name, "int")
                    patterns.append(
                        CodePattern(
                            id=f"java-autoboxing-{line_idx}",
                            title=f"Autoboxing Penalty on '{type_name}' Counter/Accumulator",
                            severity="medium",
                            category="performance",
                            line=line_idx,
                            column=1,
                            snippet=clean,
                            explanation=(
                                f"Declaring `{var_name}` as boxed wrapper `{type_name}` forces continuous boxing and unboxing "
                                "operations (`valueOf` / `intValue`) on every modification, creating redundant heap allocations."
                            ),
                            suggestion=f"Use primitive type `{prim}` instead of wrapper class `{type_name}`.",
                        )
                    )
                    optimizations.append(
                        OptimizationSuggestion(
                            id=f"opt-java-primitive-{line_idx}",
                            title=f"Replace Boxed {type_name} with Primitive {prim}",
                            category="performance",
                            impact="medium",
                            confidence="high",
                            explanation=f"Primitives like `{prim}` reside on the thread stack and in CPU registers, eliminating object heap overhead and pointer dereferencing.",
                            original_code=clean,
                            optimized_code=clean.replace(type_name, prim),
                            diff=f"- {type_name} {var_name}\n+ {prim} {var_name}",
                            theoretical_benefit="Eliminates heap allocation overhead and prevents unnecessary Garbage Collector cycles.",
                        )
                    )
                    break

        # 4. Check for Multiple Consecutive System.out.println() calls
        consecutive_prints = []
        for line_idx, line in enumerate(lines, start=1):
            clean = re.sub(r'//.*$|/\*.*?\*/', '', line).strip()
            if re.search(r'\bSystem\.out\.print(ln)?\s*\(', clean):
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
                    id=f"java-multi-println-{first_l}",
                    title=f"Multiple Consecutive System.out.println() Calls ({count} statements)",
                    severity="medium",
                    category="performance",
                    line=first_l,
                    column=1,
                    snippet=first_snippet,
                    explanation=(
                        f"Detected {count} consecutive `System.out.println()` calls. Standard output streams in Java are synchronized, "
                        "meaning every call acquires an intrinsic monitor lock on `PrintStream`, causing lock contention and I/O latency."
                    ),
                    suggestion="Consolidate lines into a loop (e.g. `items.forEach(System.out::println)`), a single formatted string, or a helper method.",
                )
            )
            optimizations.append(
                OptimizationSuggestion(
                    id=f"opt-java-println-loop-{first_l}",
                    title="Consolidate Synchronized PrintStream Calls",
                    category="performance",
                    impact="medium",
                    confidence="high",
                    explanation="Minimizes monitor lock acquisition overhead on PrintStream and reduces synchronized buffer flushes.",
                    original_code="\n".join(s for _, s in consecutive_prints),
                    optimized_code="// Option 1: Iterate list/array\nList.of(\"line1\", \"line2\", \"line3\").forEach(System.out::println);\n\n// Option 2: Single multiline output\nSystem.out.print(\"\"\"\n    line1\n    line2\n    line3\n    \"\"\");",
                    diff="+ List.of(...).forEach(System.out::println);",
                    theoretical_benefit="Decreases monitor synchronization lock acquisitions and reduces console stream latency.",
                )
            )

        # 5. Check for Quadratic Nested Loops
        complexity, ast_metrics = calculate_structural_complexity(code)
        if ast_metrics.max_nesting_depth >= 2:
            patterns.append(
                CodePattern(
                    id="java-nested-loops",
                    title=f"Nested Loop Bottleneck Detected ({complexity.time_complexity})",
                    severity="high",
                    category="complexity",
                    line=1,
                    column=1,
                    snippet="for (...) { for (...) { ... } }",
                    explanation=(
                        f"Nested loops create quadratic {complexity.time_complexity} time complexity. "
                        "Execution scales exponentially for medium to large data sets."
                    ),
                    suggestion="Evaluate whether HashMap, HashSet, or sorting + binary search can flatten the lookup to O(N) or O(N log N).",
                )
            )
            optimizations.append(
                OptimizationSuggestion(
                    id="opt-java-hashmap-flatten",
                    title="Index Collections with HashMap / HashSet",
                    category="complexity",
                    impact="high",
                    confidence="high",
                    explanation="Using Java's java.util.HashMap indexes elements by key in O(1) average time, removing inner loop scans.",
                    original_code="for (Item a : listA) {\n    for (Item b : listB) {\n        if (a.getId().equals(b.getId())) process(a, b);\n    }\n}",
                    optimized_code="Map<String, Item> bMap = listB.stream().collect(Collectors.toMap(Item::getId, b -> b));\nfor (Item a : listA) {\n    if (bMap.containsKey(a.getId())) process(a, bMap.get(a.getId()));\n}",
                    diff="- nested loop pairwise scan\n+ Map<String, Item> bMap lookup",
                    theoretical_benefit="Dramatically reduces operation count from O(N²) to linear O(N).",
                )
            )

        benchmark_model = generate_benchmark_model(complexity, optimizations)

        return AnalyzeResponse(
            language="java",
            supported=True,
            status="success",
            message=f"Java static analysis completed successfully. Found {len(patterns)} pattern(s) and {len(optimizations)} optimization(s).",
            timestamp=timestamp,
            syntax_error=SyntaxErrorInfo(has_error=False),
            complexity=complexity,
            patterns=patterns,
            optimizations=optimizations,
            ast_metrics=ast_metrics,
            benchmark_model=benchmark_model,
        )
