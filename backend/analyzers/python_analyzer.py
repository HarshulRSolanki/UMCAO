"""Real static analysis engine for Python using built-in AST module.

Safety: This analyzer performs purely static AST analysis and NEVER executes user code.
"""

import ast
import math
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple, Set

from models.schemas import (
    AnalyzeResponse,
    SyntaxErrorInfo,
    CodePattern,
    OptimizationSuggestion,
    ComplexityEstimate,
    ASTMetrics,
    BenchmarkModel,
    BenchmarkPoint,
)
from .base import BaseAnalyzer


class ASTMetricVisitor(ast.NodeVisitor):
    """Walks the AST to compute structural metrics."""

    def __init__(self):
        self.total_nodes = 0
        self.functions_count = 0
        self.classes_count = 0
        self.loops_count = 0
        self.branches_count = 0
        self.current_depth = 0
        self.max_nesting_depth = 0

    def generic_visit(self, node: ast.AST):
        self.total_nodes += 1
        is_nesting = isinstance(node, (ast.For, ast.While, ast.If, ast.With, ast.Try))
        if is_nesting:
            self.current_depth += 1
            if self.current_depth > self.max_nesting_depth:
                self.max_nesting_depth = self.current_depth

        super().generic_visit(node)

        if is_nesting:
            self.current_depth -= 1

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self.functions_count += 1
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self.functions_count += 1
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        self.classes_count += 1
        self.generic_visit(node)

    def visit_For(self, node: ast.For):
        self.loops_count += 1
        self.generic_visit(node)

    def visit_While(self, node: ast.While):
        self.loops_count += 1
        self.generic_visit(node)

    def visit_If(self, node: ast.If):
        self.branches_count += 1
        self.generic_visit(node)


class PythonAnalyzer(BaseAnalyzer):
    """Production static analyzer for Python based on standard library `ast`."""

    def __init__(self):
        super().__init__(language_id="python", display_name="Python", is_supported=True)

    def analyze(self, code: str, options: Optional[Dict[str, Any]] = None) -> AnalyzeResponse:
        code_clean = code.strip() if code else ""
        timestamp = datetime.now(timezone.utc).isoformat()

        if not code_clean:
            return AnalyzeResponse(
                language="python",
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

        # 1. Parse AST & Detect Syntax Errors
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return self._handle_syntax_error(e, code, timestamp)
        except Exception as e:
            return AnalyzeResponse(
                language="python",
                supported=True,
                status="error",
                message=f"Parser encountered an error: {str(e)}",
                timestamp=timestamp,
            )

        lines = code.splitlines()
        loc = len([ln for ln in lines if ln.strip() and not ln.strip().startswith("#")])
        comment_lines = len([ln for ln in lines if ln.strip().startswith("#")])

        # 2. Extract AST Metrics
        metric_visitor = ASTMetricVisitor()
        metric_visitor.visit(tree)
        ast_metrics = ASTMetrics(
            total_nodes=metric_visitor.total_nodes,
            functions_count=metric_visitor.functions_count,
            classes_count=metric_visitor.classes_count,
            loops_count=metric_visitor.loops_count,
            branches_count=metric_visitor.branches_count,
            max_nesting_depth=metric_visitor.max_nesting_depth,
            lines_of_code=loc,
            comment_lines=comment_lines,
        )

        # 3. Detect Inefficient Patterns & Generate Optimization Suggestions
        patterns: List[CodePattern] = []
        optimizations: List[OptimizationSuggestion] = []

        self._check_string_concatenation_in_loops(tree, lines, patterns, optimizations)
        self._check_list_membership_in_loops(tree, lines, patterns, optimizations)
        self._check_unidiomatic_range_len(tree, lines, patterns, optimizations)
        self._check_len_comparisons(tree, lines, patterns, optimizations)
        self._check_nested_loops(tree, lines, patterns, optimizations)
        self._check_exponential_recursion(tree, lines, patterns, optimizations)
        self._check_bare_except(tree, lines, patterns, optimizations)
        self._check_unclosed_files(tree, lines, patterns, optimizations)
        self._check_redundant_dict_keys(tree, lines, patterns, optimizations)
        self._check_repeated_append_pattern(tree, lines, patterns, optimizations)
        self._check_multiple_prints(tree, lines, patterns, optimizations)

        # 4. Structural Complexity Estimation
        complexity = self._estimate_complexity(tree, patterns)

        # 5. Benchmark Scaling Model for Chart.js
        benchmark_model = self._generate_benchmark_model(complexity, optimizations)

        return AnalyzeResponse(
            language="python",
            supported=True,
            status="success",
            message=f"Python static analysis completed successfully. Found {len(patterns)} pattern(s) and {len(optimizations)} optimization(s).",
            timestamp=timestamp,
            syntax_error=SyntaxErrorInfo(has_error=False),
            complexity=complexity,
            patterns=patterns,
            optimizations=optimizations,
            ast_metrics=ast_metrics,
            benchmark_model=benchmark_model,
        )

    # -------------------------------------------------------------------------
    # Syntax Error Handling
    # -------------------------------------------------------------------------
    def _handle_syntax_error(self, e: SyntaxError, full_code: str, timestamp: str) -> AnalyzeResponse:
        lines = full_code.splitlines()
        err_line = e.lineno or 1
        err_col = e.offset or 1
        raw_snippet = lines[err_line - 1] if 0 < err_line <= len(lines) else (e.text or "")

        explanation = self._explain_syntax_error(str(e.msg), raw_snippet)

        syntax_info = SyntaxErrorInfo(
            has_error=True,
            message=str(e.msg),
            line=err_line,
            column=err_col,
            text=raw_snippet.strip() if raw_snippet else None,
            friendly_explanation=explanation,
        )

        return AnalyzeResponse(
            language="python",
            supported=True,
            status="syntax_error",
            message=f"SyntaxError detected at line {err_line}, column {err_col}: {e.msg}",
            timestamp=timestamp,
            syntax_error=syntax_info,
            patterns=[],
            optimizations=[],
            ast_metrics=ASTMetrics(
                total_nodes=0,
                functions_count=0,
                classes_count=0,
                loops_count=0,
                branches_count=0,
                max_nesting_depth=0,
                lines_of_code=len(lines),
                comment_lines=0,
            ),
        )

    def _explain_syntax_error(self, msg: str, snippet: str) -> str:
        msg_lower = msg.lower()
        if "expected ':'" in msg_lower or snippet.strip().endswith(("def ", "if ", "for ", "while ", "else", "elif")):
            return "Missing colon (':') at the end of a header statement (such as def, if, for, while, class, or try)."
        elif "unexpected indent" in msg_lower:
            return "Unexpected indentation. Python relies on consistent whitespace indentation (usually 4 spaces) to define code blocks."
        elif "unindent does not match" in msg_lower:
            return "Unindent does not match any outer indentation level. Check spaces vs tabs or inconsistent block alignment."
        elif "was never closed" in msg_lower or "unmatched" in msg_lower:
            return "An opening bracket, parenthesis, brace, or quote was opened but never closed properly."
        elif "cannot assign to" in msg_lower:
            return "Invalid assignment target. Did you accidentally use '=' (assignment) instead of '==' (equality check)?"
        elif "return' outside function" in msg_lower:
            return "'return' statement is outside of a function definition. Return statements can only appear within a 'def' block."
        return f"Python parser encountered an invalid token or structure: '{msg}'. Ensure statements follow standard Python 3 grammar."

    # -------------------------------------------------------------------------
    # Pattern Detection Methods
    # -------------------------------------------------------------------------
    def _check_string_concatenation_in_loops(
        self, tree: ast.AST, lines: List[str], patterns: List[CodePattern], optimizations: List[OptimizationSuggestion]
    ):
        """Detects string concatenation with `+=` inside loops."""
        for loop_node in ast.walk(tree):
            if isinstance(loop_node, (ast.For, ast.While)):
                for sub in ast.walk(loop_node):
                    if isinstance(sub, ast.AugAssign) and isinstance(sub.op, ast.Add):
                        # AugAssign with addition (+=) inside loop
                        target_name = sub.target.id if isinstance(sub.target, ast.Name) else "text"
                        line_num = getattr(sub, "lineno", loop_node.lineno)
                        snippet = lines[line_num - 1].strip() if 0 < line_num <= len(lines) else f"{target_name} += item"

                        pattern = CodePattern(
                            id=f"perf-str-concat-{line_num}",
                            title="Repeated String Concatenation in Loop",
                            severity="high",
                            category="performance",
                            line=line_num,
                            column=getattr(sub, "col_offset", 0),
                            snippet=snippet,
                            explanation=(
                                f"In-place string concatenation (`{target_name} += ...`) inside a loop incurs O(N²) memory reallocation overhead "
                                "because Python strings are immutable and must be reallocated and copied on every iteration."
                            ),
                            suggestion=f"Collect parts in a list (`chunks.append(...)`) and merge once using `'{target_name} = \"\".join(chunks)'` after the loop.",
                        )
                        patterns.append(pattern)

                        optimizations.append(
                            OptimizationSuggestion(
                                id=f"opt-str-concat-{line_num}",
                                title="Vectorize / Batch String Construction with ''.join()",
                                category="performance",
                                impact="high",
                                confidence="high",
                                explanation=(
                                    "Strings are immutable in Python. Using `+=` in a loop forces Python to allocate a new memory buffer "
                                    "and copy previous characters on each step, leading to quadratic O(N²) time. Collecting elements into a list "
                                    "and calling `''.join()` executes in linear O(N) time at C-speed."
                                ),
                                original_code=f"{target_name} = \"\"\nfor item in items:\n    {target_name} += str(item)",
                                optimized_code=f"chunks = [str(item) for item in items]\n{target_name} = \"\".join(chunks)",
                                diff=f"- {target_name} += str(item)\n+ chunks.append(str(item))\n+ {target_name} = ''.join(chunks)",
                                theoretical_benefit="Reduces asymptotic time from O(N²) reallocation down to linear O(N).",
                            )
                        )
                        return

    def _check_multiple_prints(
        self, tree: ast.AST, lines: List[str], patterns: List[CodePattern], optimizations: List[OptimizationSuggestion]
    ):
        """Detects multiple consecutive or repeated print() statements and suggests using a loop or helper function."""
        def is_print_call(stmt: ast.AST) -> bool:
            return (
                isinstance(stmt, ast.Expr)
                and isinstance(stmt.value, ast.Call)
                and isinstance(stmt.value.func, ast.Name)
                and stmt.value.func.id == "print"
            )

        # Inspect all statement lists (module body, function bodies, if/else bodies, etc.)
        for node in ast.walk(tree):
            for block_attr in ("body", "orelse", "finalbody"):
                stmts = getattr(node, block_attr, None)
                if not isinstance(stmts, list) or len(stmts) < 2:
                    continue

                # Find runs of consecutive print statements
                current_group: List[ast.Expr] = []
                for stmt in stmts:
                    if is_print_call(stmt):
                        current_group.append(stmt)
                    else:
                        if len(current_group) >= 2:
                            break
                        current_group = []

                if len(current_group) < 2:
                    # Check if there are >= 3 total print statements in this block even if separated
                    all_prints = [s for s in stmts if is_print_call(s)]
                    if len(all_prints) >= 3:
                        current_group = all_prints

                if len(current_group) >= 2:
                    first_stmt = current_group[0]
                    last_stmt = current_group[-1]
                    start_line = getattr(first_stmt, "lineno", 1)
                    end_line = getattr(last_stmt, "end_lineno", getattr(last_stmt, "lineno", start_line))
                    col_offset = getattr(first_stmt, "col_offset", 0)
                    indent_str = " " * col_offset

                    # Collect original code snippet and lines
                    snippet = lines[start_line - 1].strip() if 0 < start_line <= len(lines) else "print(...)"
                    orig_lines = lines[start_line - 1 : end_line] if 0 < start_line <= len(lines) else [f"print(item_{i})" for i in range(len(current_group))]
                    original_snippet = "\n".join(orig_lines)

                    # Extract arguments from print statements
                    extracted_args = []
                    for s in current_group:
                        call = s.value
                        if call.args:
                            try:
                                # Unparse each argument
                                arg_text = ", ".join(ast.unparse(a) for a in call.args)
                                extracted_args.append(arg_text)
                            except Exception:
                                extracted_args.append("item")
                        else:
                            extracted_args.append("''")

                    # Formulate dynamic examples based on extracted arguments
                    count = len(current_group)
                    args_joined = ", ".join(extracted_args)
                    is_all_simple = count <= 8

                    if is_all_simple:
                        items_list_str = f"[{args_joined}]"
                        print_args_str = args_joined
                    else:
                        items_list_str = f"[{extracted_args[0]}, {extracted_args[1]}, ...]"
                        print_args_str = f"{extracted_args[0]}, {extracted_args[1]}, ..."

                    # Pattern object
                    patterns.append(
                        CodePattern(
                            id=f"perf-multiple-print-{start_line}",
                            title=f"Multiple Consecutive Print Statements ({count} calls)",
                            severity="medium" if count >= 3 else "low",
                            category="performance",
                            line=start_line,
                            column=col_offset,
                            snippet=snippet,
                            explanation=(
                                f"Detected {count} consecutive `print()` invocations. Calling `print()` repeatedly executes "
                                "multiple independent I/O system calls and stream flushes. This introduces redundant I/O overhead "
                                "and violates the DRY (Don't Repeat Yourself) principle."
                            ),
                            suggestion=(
                                f"Consolidate repetitive print calls into a `for` loop (e.g. `for item in [{args_joined}]: print(item)`), "
                                f"a single `print(..., sep='\\n')` call, or encapsulate into a reusable helper function."
                            ),
                        )
                    )

                    # Optimization suggestion with concrete, runnable refactorings
                    optimized_code_lines = [
                        f"{indent_str}# Option 1: Iterate using a for-loop (Clean & Scalable)",
                        f"{indent_str}for item in {items_list_str}:",
                        f"{indent_str}    print(item)",
                        f"",
                        f"{indent_str}# Option 2: Single print() with newline separator (Fastest I/O)",
                        f"{indent_str}print({print_args_str}, sep='\\n')",
                        f"",
                        f"{indent_str}# Option 3: Reusable helper function (Modular & DRY)",
                        f"{indent_str}def print_all(*items):",
                        f"{indent_str}    for item in items:",
                        f"{indent_str}        print(item)",
                        f"",
                        f"{indent_str}print_all({print_args_str})",
                    ]
                    optimized_code = "\n".join(optimized_code_lines)

                    diff_lines = [f"- {line}" for line in orig_lines]
                    diff_lines.append(f"+ # Refactored with loop:")
                    diff_lines.append(f"+ for item in {items_list_str}:")
                    diff_lines.append(f"+     print(item)")
                    diff_text = "\n".join(diff_lines)

                    optimizations.append(
                        OptimizationSuggestion(
                            id=f"opt-loop-function-print-{start_line}",
                            title="Refactor Repeated Prints to Loop or Helper Function",
                            category="performance",
                            impact="medium",
                            confidence="high",
                            explanation=(
                                "Invoking `print()` multiple times forces repeated system I/O context switching, locks `sys.stdout`, "
                                "and performs redundant line buffering. Replacing repetitive print statements with an iterable loop "
                                "or a single `print(*items, sep='\\n')` cuts boilerplate, eliminates I/O stalls, and makes adding new outputs trivial."
                            ),
                            original_code=original_snippet,
                            optimized_code=optimized_code,
                            diff=diff_text,
                            theoretical_benefit="Reduces multiple I/O system calls and stream flushes into a unified iteration or single buffered output.",
                        )
                    )
                    return  # Flag once per file to avoid noise

    def _check_list_membership_in_loops(
        self, tree: ast.AST, lines: List[str], patterns: List[CodePattern], optimizations: List[OptimizationSuggestion]
    ):
        """Detects `item in list` membership test inside loops."""
        for loop_node in ast.walk(tree):
            if isinstance(loop_node, (ast.For, ast.While)):
                for sub in ast.walk(loop_node):
                    if isinstance(sub, ast.Compare):
                        for op, comparator in zip(sub.ops, sub.comparators):
                            if isinstance(op, (ast.In, ast.NotIn)):
                                is_list_literal = isinstance(comparator, ast.List)
                                is_list_var = isinstance(comparator, ast.Name) and "list" in comparator.id.lower()
                                if is_list_literal or is_list_var:
                                    line_num = getattr(sub, "lineno", loop_node.lineno)
                                    snippet = lines[line_num - 1].strip() if 0 < line_num <= len(lines) else "if item in collection:"
                                    target_str = "lookup_list" if is_list_literal else comparator.id

                                    patterns.append(
                                        CodePattern(
                                            id=f"comp-list-membership-{line_num}",
                                            title="Linear List Membership Check in Loop",
                                            severity="high",
                                            category="complexity",
                                            line=line_num,
                                            column=getattr(sub, "col_offset", 0),
                                            snippet=snippet,
                                            explanation=(
                                                f"Performing `in {target_str}` inside a loop executes an O(M) linear search on every iteration, "
                                                "transforming what could be an O(N) algorithm into an O(N * M) quadratic bottleneck."
                                            ),
                                            suggestion=f"Convert the collection to a `set` (`{target_str}_set = set({target_str})`) outside the loop for O(1) average lookup.",
                                        )
                                    )

                                    optimizations.append(
                                        OptimizationSuggestion(
                                            id=f"opt-set-lookup-{line_num}",
                                            title="Replace List Search with Set / Hash Lookup",
                                            category="complexity",
                                            impact="high",
                                            confidence="high",
                                            explanation=(
                                                "List membership testing (`x in my_list`) performs an O(M) linear search by inspecting elements one by one. "
                                                "A Python `set` uses hash tables with O(1) average lookup time. Pre-computing `my_set = set(my_list)` "
                                                "reduces total search time across N iterations from O(N * M) to O(N + M)."
                                            ),
                                            original_code=f"for item in data:\n    if item in lookup_items:  # O(M) search each time\n        process(item)",
                                            optimized_code=f"lookup_set = set(lookup_items)  # O(M) one-time cost\nfor item in data:\n    if item in lookup_set:  # O(1) average lookup\n        process(item)",
                                            diff="- if item in lookup_items:\n+ lookup_set = set(lookup_items)\n+ if item in lookup_set:",
                                            theoretical_benefit="Accelerates inner search from O(M) linear scan to O(1) constant-time hash lookup.",
                                        )
                                    )
                                    return

    def _check_multiple_prints(
        self, tree: ast.AST, lines: List[str], patterns: List[CodePattern], optimizations: List[OptimizationSuggestion]
    ):
        """Detects multiple consecutive or repeated print() statements and suggests using a loop or helper function."""
        def is_print_call(stmt: ast.AST) -> bool:
            return (
                isinstance(stmt, ast.Expr)
                and isinstance(stmt.value, ast.Call)
                and isinstance(stmt.value.func, ast.Name)
                and stmt.value.func.id == "print"
            )

        # Inspect all statement lists (module body, function bodies, if/else bodies, etc.)
        for node in ast.walk(tree):
            for block_attr in ("body", "orelse", "finalbody"):
                stmts = getattr(node, block_attr, None)
                if not isinstance(stmts, list) or len(stmts) < 2:
                    continue

                # Find runs of consecutive print statements
                current_group: List[ast.Expr] = []
                for stmt in stmts:
                    if is_print_call(stmt):
                        current_group.append(stmt)
                    else:
                        if len(current_group) >= 2:
                            break
                        current_group = []

                if len(current_group) < 2:
                    # Check if there are >= 3 total print statements in this block even if separated
                    all_prints = [s for s in stmts if is_print_call(s)]
                    if len(all_prints) >= 3:
                        current_group = all_prints

                if len(current_group) >= 2:
                    first_stmt = current_group[0]
                    last_stmt = current_group[-1]
                    start_line = getattr(first_stmt, "lineno", 1)
                    end_line = getattr(last_stmt, "end_lineno", getattr(last_stmt, "lineno", start_line))
                    col_offset = getattr(first_stmt, "col_offset", 0)
                    indent_str = " " * col_offset

                    # Collect original code snippet and lines
                    snippet = lines[start_line - 1].strip() if 0 < start_line <= len(lines) else "print(...)"
                    orig_lines = lines[start_line - 1 : end_line] if 0 < start_line <= len(lines) else [f"print(item_{i})" for i in range(len(current_group))]
                    original_snippet = "\n".join(orig_lines)

                    # Extract arguments from print statements
                    extracted_args = []
                    for s in current_group:
                        call = s.value
                        if call.args:
                            try:
                                # Unparse each argument
                                arg_text = ", ".join(ast.unparse(a) for a in call.args)
                                extracted_args.append(arg_text)
                            except Exception:
                                extracted_args.append("item")
                        else:
                            extracted_args.append("''")

                    # Formulate dynamic examples based on extracted arguments
                    count = len(current_group)
                    args_joined = ", ".join(extracted_args)
                    is_all_simple = count <= 8

                    if is_all_simple:
                        items_list_str = f"[{args_joined}]"
                        print_args_str = args_joined
                    else:
                        items_list_str = f"[{extracted_args[0]}, {extracted_args[1]}, ...]"
                        print_args_str = f"{extracted_args[0]}, {extracted_args[1]}, ..."

                    # Pattern object
                    patterns.append(
                        CodePattern(
                            id=f"perf-multiple-print-{start_line}",
                            title=f"Multiple Consecutive Print Statements ({count} calls)",
                            severity="medium" if count >= 3 else "low",
                            category="performance",
                            line=start_line,
                            column=col_offset,
                            snippet=snippet,
                            explanation=(
                                f"Detected {count} consecutive `print()` invocations. Calling `print()` repeatedly executes "
                                "multiple independent I/O system calls and stream flushes. This introduces redundant I/O overhead "
                                "and violates the DRY (Don't Repeat Yourself) principle."
                            ),
                            suggestion=(
                                f"Consolidate repetitive print calls into a `for` loop (e.g. `for item in [{args_joined}]: print(item)`), "
                                f"a single `print(..., sep='\\n')` call, or encapsulate into a reusable helper function."
                            ),
                        )
                    )

                    # Optimization suggestion with concrete, runnable refactorings
                    optimized_code_lines = [
                        f"{indent_str}# Option 1: Iterate using a for-loop (Clean & Scalable)",
                        f"{indent_str}for item in {items_list_str}:",
                        f"{indent_str}    print(item)",
                        f"",
                        f"{indent_str}# Option 2: Single print() with newline separator (Fastest I/O)",
                        f"{indent_str}print({print_args_str}, sep='\\n')",
                        f"",
                        f"{indent_str}# Option 3: Reusable helper function (Modular & DRY)",
                        f"{indent_str}def print_all(*items):",
                        f"{indent_str}    for item in items:",
                        f"{indent_str}        print(item)",
                        f"",
                        f"{indent_str}print_all({print_args_str})",
                    ]
                    optimized_code = "\n".join(optimized_code_lines)

                    diff_lines = [f"- {line}" for line in orig_lines]
                    diff_lines.append(f"+ # Refactored with loop:")
                    diff_lines.append(f"+ for item in {items_list_str}:")
                    diff_lines.append(f"+     print(item)")
                    diff_text = "\n".join(diff_lines)

                    optimizations.append(
                        OptimizationSuggestion(
                            id=f"opt-loop-function-print-{start_line}",
                            title="Refactor Repeated Prints to Loop or Helper Function",
                            category="performance",
                            impact="medium",
                            confidence="high",
                            explanation=(
                                "Invoking `print()` multiple times forces repeated system I/O context switching, locks `sys.stdout`, "
                                "and performs redundant line buffering. Replacing repetitive print statements with an iterable loop "
                                "or a single `print(*items, sep='\\n')` cuts boilerplate, eliminates I/O stalls, and makes adding new outputs trivial."
                            ),
                            original_code=original_snippet,
                            optimized_code=optimized_code,
                            diff=diff_text,
                            theoretical_benefit="Reduces multiple I/O system calls and stream flushes into a unified iteration or single buffered output.",
                        )
                    )
                    return

    def _check_unidiomatic_range_len(
        self, tree: ast.AST, lines: List[str], patterns: List[CodePattern], optimizations: List[OptimizationSuggestion]
    ):
        """Detects `for i in range(len(seq))`."""
        for node in ast.walk(tree):
            if isinstance(node, ast.For):
                if isinstance(node.iter, ast.Call) and isinstance(node.iter.func, ast.Name):
                    if node.iter.func.id == "range" and node.iter.args:
                        arg0 = node.iter.args[0]
                        if isinstance(arg0, ast.Call) and isinstance(arg0.func, ast.Name) and arg0.func.id == "len":
                            line_num = node.lineno
                            seq_name = arg0.args[0].id if arg0.args and isinstance(arg0.args[0], ast.Name) else "items"
                            idx_var = node.target.id if isinstance(node.target, ast.Name) else "i"
                            snippet = lines[line_num - 1].strip() if 0 < line_num <= len(lines) else f"for {idx_var} in range(len({seq_name})):"

                            patterns.append(
                                CodePattern(
                                    id=f"idiom-range-len-{line_num}",
                                    title="Unidiomatic Index Iteration: range(len())",
                                    severity="medium",
                                    category="idiom",
                                    line=line_num,
                                    column=node.col_offset,
                                    snippet=snippet,
                                    explanation=(
                                        f"Using `range(len({seq_name}))` is an anti-pattern in Python. It introduces unnecessary index tracking "
                                        f"and subscript lookups (`{seq_name}[{idx_var}]`) which add bytecode overhead."
                                    ),
                                    suggestion=f"Use direct iteration (`for item in {seq_name}:`) or `enumerate({seq_name})` if you need both index and element.",
                                )
                            )

                            optimizations.append(
                                OptimizationSuggestion(
                                    id=f"opt-enumerate-{line_num}",
                                    title="Modernize Iteration with enumerate()",
                                    category="idiom",
                                    impact="medium",
                                    confidence="high",
                                    explanation=(
                                        "`for i in range(len(items))` requires repeated index subscripting (`items[i]`), generating extra `BINARY_SUBSCR` "
                                        "bytecode instructions and bounds checks. `enumerate(items)` directly yields pairs via iterator protocol, improving "
                                        "both performance and readability."
                                    ),
                                    original_code=f"for {idx_var} in range(len({seq_name})):\n    val = {seq_name}[{idx_var}]\n    print({idx_var}, val)",
                                    optimized_code=f"for {idx_var}, val in enumerate({seq_name}):\n    print({idx_var}, val)",
                                    diff=f"- for {idx_var} in range(len({seq_name})):\n-     val = {seq_name}[{idx_var}]\n+ for {idx_var}, val in enumerate({seq_name}):",
                                    theoretical_benefit="Eliminates subscript overhead and bounds checking, saving bytecode execution cycles.",
                                )
                            )
                            return

    def _check_multiple_prints(
        self, tree: ast.AST, lines: List[str], patterns: List[CodePattern], optimizations: List[OptimizationSuggestion]
    ):
        """Detects multiple consecutive or repeated print() statements and suggests using a loop or helper function."""
        def is_print_call(stmt: ast.AST) -> bool:
            return (
                isinstance(stmt, ast.Expr)
                and isinstance(stmt.value, ast.Call)
                and isinstance(stmt.value.func, ast.Name)
                and stmt.value.func.id == "print"
            )

        # Inspect all statement lists (module body, function bodies, if/else bodies, etc.)
        for node in ast.walk(tree):
            for block_attr in ("body", "orelse", "finalbody"):
                stmts = getattr(node, block_attr, None)
                if not isinstance(stmts, list) or len(stmts) < 2:
                    continue

                # Find runs of consecutive print statements
                current_group: List[ast.Expr] = []
                for stmt in stmts:
                    if is_print_call(stmt):
                        current_group.append(stmt)
                    else:
                        if len(current_group) >= 2:
                            break
                        current_group = []

                if len(current_group) < 2:
                    # Check if there are >= 3 total print statements in this block even if separated
                    all_prints = [s for s in stmts if is_print_call(s)]
                    if len(all_prints) >= 3:
                        current_group = all_prints

                if len(current_group) >= 2:
                    first_stmt = current_group[0]
                    last_stmt = current_group[-1]
                    start_line = getattr(first_stmt, "lineno", 1)
                    end_line = getattr(last_stmt, "end_lineno", getattr(last_stmt, "lineno", start_line))
                    col_offset = getattr(first_stmt, "col_offset", 0)
                    indent_str = " " * col_offset

                    # Collect original code snippet and lines
                    snippet = lines[start_line - 1].strip() if 0 < start_line <= len(lines) else "print(...)"
                    orig_lines = lines[start_line - 1 : end_line] if 0 < start_line <= len(lines) else [f"print(item_{i})" for i in range(len(current_group))]
                    original_snippet = "\n".join(orig_lines)

                    # Extract arguments from print statements
                    extracted_args = []
                    for s in current_group:
                        call = s.value
                        if call.args:
                            try:
                                # Unparse each argument
                                arg_text = ", ".join(ast.unparse(a) for a in call.args)
                                extracted_args.append(arg_text)
                            except Exception:
                                extracted_args.append("item")
                        else:
                            extracted_args.append("''")

                    # Formulate dynamic examples based on extracted arguments
                    count = len(current_group)
                    args_joined = ", ".join(extracted_args)
                    is_all_simple = count <= 8

                    if is_all_simple:
                        items_list_str = f"[{args_joined}]"
                        print_args_str = args_joined
                    else:
                        items_list_str = f"[{extracted_args[0]}, {extracted_args[1]}, ...]"
                        print_args_str = f"{extracted_args[0]}, {extracted_args[1]}, ..."

                    # Pattern object
                    patterns.append(
                        CodePattern(
                            id=f"perf-multiple-print-{start_line}",
                            title=f"Multiple Consecutive Print Statements ({count} calls)",
                            severity="medium" if count >= 3 else "low",
                            category="performance",
                            line=start_line,
                            column=col_offset,
                            snippet=snippet,
                            explanation=(
                                f"Detected {count} consecutive `print()` invocations. Calling `print()` repeatedly executes "
                                "multiple independent I/O system calls and stream flushes. This introduces redundant I/O overhead "
                                "and violates the DRY (Don't Repeat Yourself) principle."
                            ),
                            suggestion=(
                                f"Consolidate repetitive print calls into a `for` loop (e.g. `for item in [{args_joined}]: print(item)`), "
                                f"a single `print(..., sep='\\n')` call, or encapsulate into a reusable helper function."
                            ),
                        )
                    )

                    # Optimization suggestion with concrete, runnable refactorings
                    optimized_code_lines = [
                        f"{indent_str}# Option 1: Iterate using a for-loop (Clean & Scalable)",
                        f"{indent_str}for item in {items_list_str}:",
                        f"{indent_str}    print(item)",
                        f"",
                        f"{indent_str}# Option 2: Single print() with newline separator (Fastest I/O)",
                        f"{indent_str}print({print_args_str}, sep='\\n')",
                        f"",
                        f"{indent_str}# Option 3: Reusable helper function (Modular & DRY)",
                        f"{indent_str}def print_all(*items):",
                        f"{indent_str}    for item in items:",
                        f"{indent_str}        print(item)",
                        f"",
                        f"{indent_str}print_all({print_args_str})",
                    ]
                    optimized_code = "\n".join(optimized_code_lines)

                    diff_lines = [f"- {line}" for line in orig_lines]
                    diff_lines.append(f"+ # Refactored with loop:")
                    diff_lines.append(f"+ for item in {items_list_str}:")
                    diff_lines.append(f"+     print(item)")
                    diff_text = "\n".join(diff_lines)

                    optimizations.append(
                        OptimizationSuggestion(
                            id=f"opt-loop-function-print-{start_line}",
                            title="Refactor Repeated Prints to Loop or Helper Function",
                            category="performance",
                            impact="medium",
                            confidence="high",
                            explanation=(
                                "Invoking `print()` multiple times forces repeated system I/O context switching, locks `sys.stdout`, "
                                "and performs redundant line buffering. Replacing repetitive print statements with an iterable loop "
                                "or a single `print(*items, sep='\\n')` cuts boilerplate, eliminates I/O stalls, and makes adding new outputs trivial."
                            ),
                            original_code=original_snippet,
                            optimized_code=optimized_code,
                            diff=diff_text,
                            theoretical_benefit="Reduces multiple I/O system calls and stream flushes into a unified iteration or single buffered output.",
                        )
                    )
                    return

    def _check_len_comparisons(
        self, tree: ast.AST, lines: List[str], patterns: List[CodePattern], optimizations: List[OptimizationSuggestion]
    ):
        """Detects `len(x) == 0` or `len(x) > 0`."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Compare):
                if isinstance(node.left, ast.Call) and isinstance(node.left.func, ast.Name) and node.left.func.id == "len":
                    if node.comparators and isinstance(node.comparators[0], ast.Constant) and node.comparators[0].value == 0:
                        line_num = getattr(node, "lineno", 1)
                        snippet = lines[line_num - 1].strip() if 0 < line_num <= len(lines) else "if len(collection) == 0:"
                        var_name = node.left.args[0].id if node.left.args and isinstance(node.left.args[0], ast.Name) else "seq"

                        patterns.append(
                            CodePattern(
                                id=f"idiom-len-zero-{line_num}",
                                title="Explicit Length Check vs Truth Value Testing",
                                severity="low",
                                category="idiom",
                                line=line_num,
                                column=getattr(node, "col_offset", 0),
                                snippet=snippet,
                                explanation=(
                                    f"Calling `len({var_name}) == 0` executes a function call, a length lookup, and a comparison. "
                                    f"In Python, empty sequences (`[]`, `\"\"`, `{{}}`) evaluate to `False` in boolean contexts."
                                ),
                                suggestion=f"Use natural truthiness: `if not {var_name}:` instead of `if len({var_name}) == 0:`.",
                            )
                        )

                        optimizations.append(
                            OptimizationSuggestion(
                                id=f"opt-truthy-len-{line_num}",
                                title="Leverage Pythonic Truth Value Testing",
                                category="idiom",
                                impact="low",
                                confidence="high",
                                explanation=(
                                    "PEP 8 recommends relying on boolean coercion. `if not seq:` avoids the `LOAD_GLOBAL len`, `CALL_FUNCTION`, "
                                    "and `COMPARE_OP == 0` bytecode sequence, delegating truthiness directly to the object's `__bool__` or `__len__` slot."
                                ),
                                original_code=f"if len({var_name}) == 0:\n    handle_empty()",
                                optimized_code=f"if not {var_name}:\n    handle_empty()",
                                diff=f"- if len({var_name}) == 0:\n+ if not {var_name}:",
                                theoretical_benefit="Saves function call overhead and comparison opcode.",
                            )
                        )
                        return

    def _check_multiple_prints(
        self, tree: ast.AST, lines: List[str], patterns: List[CodePattern], optimizations: List[OptimizationSuggestion]
    ):
        """Detects multiple consecutive or repeated print() statements and suggests using a loop or helper function."""
        def is_print_call(stmt: ast.AST) -> bool:
            return (
                isinstance(stmt, ast.Expr)
                and isinstance(stmt.value, ast.Call)
                and isinstance(stmt.value.func, ast.Name)
                and stmt.value.func.id == "print"
            )

        # Inspect all statement lists (module body, function bodies, if/else bodies, etc.)
        for node in ast.walk(tree):
            for block_attr in ("body", "orelse", "finalbody"):
                stmts = getattr(node, block_attr, None)
                if not isinstance(stmts, list) or len(stmts) < 2:
                    continue

                # Find runs of consecutive print statements
                current_group: List[ast.Expr] = []
                for stmt in stmts:
                    if is_print_call(stmt):
                        current_group.append(stmt)
                    else:
                        if len(current_group) >= 2:
                            break
                        current_group = []

                if len(current_group) < 2:
                    # Check if there are >= 3 total print statements in this block even if separated
                    all_prints = [s for s in stmts if is_print_call(s)]
                    if len(all_prints) >= 3:
                        current_group = all_prints

                if len(current_group) >= 2:
                    first_stmt = current_group[0]
                    last_stmt = current_group[-1]
                    start_line = getattr(first_stmt, "lineno", 1)
                    end_line = getattr(last_stmt, "end_lineno", getattr(last_stmt, "lineno", start_line))
                    col_offset = getattr(first_stmt, "col_offset", 0)
                    indent_str = " " * col_offset

                    # Collect original code snippet and lines
                    snippet = lines[start_line - 1].strip() if 0 < start_line <= len(lines) else "print(...)"
                    orig_lines = lines[start_line - 1 : end_line] if 0 < start_line <= len(lines) else [f"print(item_{i})" for i in range(len(current_group))]
                    original_snippet = "\n".join(orig_lines)

                    # Extract arguments from print statements
                    extracted_args = []
                    for s in current_group:
                        call = s.value
                        if call.args:
                            try:
                                # Unparse each argument
                                arg_text = ", ".join(ast.unparse(a) for a in call.args)
                                extracted_args.append(arg_text)
                            except Exception:
                                extracted_args.append("item")
                        else:
                            extracted_args.append("''")

                    # Formulate dynamic examples based on extracted arguments
                    count = len(current_group)
                    args_joined = ", ".join(extracted_args)
                    is_all_simple = count <= 8

                    if is_all_simple:
                        items_list_str = f"[{args_joined}]"
                        print_args_str = args_joined
                    else:
                        items_list_str = f"[{extracted_args[0]}, {extracted_args[1]}, ...]"
                        print_args_str = f"{extracted_args[0]}, {extracted_args[1]}, ..."

                    # Pattern object
                    patterns.append(
                        CodePattern(
                            id=f"perf-multiple-print-{start_line}",
                            title=f"Multiple Consecutive Print Statements ({count} calls)",
                            severity="medium" if count >= 3 else "low",
                            category="performance",
                            line=start_line,
                            column=col_offset,
                            snippet=snippet,
                            explanation=(
                                f"Detected {count} consecutive `print()` invocations. Calling `print()` repeatedly executes "
                                "multiple independent I/O system calls and stream flushes. This introduces redundant I/O overhead "
                                "and violates the DRY (Don't Repeat Yourself) principle."
                            ),
                            suggestion=(
                                f"Consolidate repetitive print calls into a `for` loop (e.g. `for item in [{args_joined}]: print(item)`), "
                                f"a single `print(..., sep='\\n')` call, or encapsulate into a reusable helper function."
                            ),
                        )
                    )

                    # Optimization suggestion with concrete, runnable refactorings
                    optimized_code_lines = [
                        f"{indent_str}# Option 1: Iterate using a for-loop (Clean & Scalable)",
                        f"{indent_str}for item in {items_list_str}:",
                        f"{indent_str}    print(item)",
                        f"",
                        f"{indent_str}# Option 2: Single print() with newline separator (Fastest I/O)",
                        f"{indent_str}print({print_args_str}, sep='\\n')",
                        f"",
                        f"{indent_str}# Option 3: Reusable helper function (Modular & DRY)",
                        f"{indent_str}def print_all(*items):",
                        f"{indent_str}    for item in items:",
                        f"{indent_str}        print(item)",
                        f"",
                        f"{indent_str}print_all({print_args_str})",
                    ]
                    optimized_code = "\n".join(optimized_code_lines)

                    diff_lines = [f"- {line}" for line in orig_lines]
                    diff_lines.append(f"+ # Refactored with loop:")
                    diff_lines.append(f"+ for item in {items_list_str}:")
                    diff_lines.append(f"+     print(item)")
                    diff_text = "\n".join(diff_lines)

                    optimizations.append(
                        OptimizationSuggestion(
                            id=f"opt-loop-function-print-{start_line}",
                            title="Refactor Repeated Prints to Loop or Helper Function",
                            category="performance",
                            impact="medium",
                            confidence="high",
                            explanation=(
                                "Invoking `print()` multiple times forces repeated system I/O context switching, locks `sys.stdout`, "
                                "and performs redundant line buffering. Replacing repetitive print statements with an iterable loop "
                                "or a single `print(*items, sep='\\n')` cuts boilerplate, eliminates I/O stalls, and makes adding new outputs trivial."
                            ),
                            original_code=original_snippet,
                            optimized_code=optimized_code,
                            diff=diff_text,
                            theoretical_benefit="Reduces multiple I/O system calls and stream flushes into a unified iteration or single buffered output.",
                        )
                    )
                    return

    def _check_nested_loops(
        self, tree: ast.AST, lines: List[str], patterns: List[CodePattern], optimizations: List[OptimizationSuggestion]
    ):
        """Detects nested loops causing quadratic O(n^2) or worse complexity."""
        for node in ast.walk(tree):
            if isinstance(node, (ast.For, ast.While)):
                for child in node.body:
                    if isinstance(child, (ast.For, ast.While)):
                        line_num = getattr(child, "lineno", node.lineno)
                        snippet = lines[line_num - 1].strip() if 0 < line_num <= len(lines) else "for j in inner_loop:"

                        patterns.append(
                            CodePattern(
                                id=f"comp-nested-loops-{line_num}",
                                title="Nested Loop Detected (Polynomial O(N²) or Higher)",
                                severity="high",
                                category="complexity",
                                line=line_num,
                                column=getattr(child, "col_offset", 0),
                                snippet=snippet,
                                explanation=(
                                    "Directly nesting loops over input data structures results in quadratic O(N²) or cubic O(N³) time complexity. "
                                    "For large inputs (e.g. N > 10,000), execution will severely degrade or time out."
                                ),
                                suggestion="Evaluate whether a hash map, dictionary indexing, prefix sum, or sorting + two-pointer technique can flatten the algorithm to O(N) or O(N log N).",
                            )
                        )

                        optimizations.append(
                            OptimizationSuggestion(
                                id=f"opt-flatten-loops-{line_num}",
                                title="Algorithmic Optimization: Flatten Quadratic Nested Loop",
                                category="complexity",
                                impact="high",
                                confidence="high",
                                explanation=(
                                    "Two nested loops comparing elements pairwise takes O(N²) operations (1,000,000 ops for N=1,000). "
                                    "Indexing the inner collection into a dictionary or set allows single-pass O(N) iteration, "
                                    "dropping operations from N² down to 2N."
                                ),
                                original_code="matches = []\nfor a in list_a:\n    for b in list_b:\n        if a.id == b.id:\n            matches.append((a, b))",
                                optimized_code="b_map = {b.id: b for b in list_b}\nmatches = [(a, b_map[a.id]) for a in list_a if a.id in b_map]",
                                diff="- for a in list_a:\n-     for b in list_b:\n-         if a.id == b.id: ...\n+ b_map = {b.id: b for b in list_b}\n+ matches = [(a, b_map[a.id]) for a in list_a if a.id in b_map]",
                                theoretical_benefit="Drastically reduces computational steps from O(N²) to linear O(N) with O(N) auxiliary space.",
                            )
                        )
                        return

    def _check_multiple_prints(
        self, tree: ast.AST, lines: List[str], patterns: List[CodePattern], optimizations: List[OptimizationSuggestion]
    ):
        """Detects multiple consecutive or repeated print() statements and suggests using a loop or helper function."""
        def is_print_call(stmt: ast.AST) -> bool:
            return (
                isinstance(stmt, ast.Expr)
                and isinstance(stmt.value, ast.Call)
                and isinstance(stmt.value.func, ast.Name)
                and stmt.value.func.id == "print"
            )

        # Inspect all statement lists (module body, function bodies, if/else bodies, etc.)
        for node in ast.walk(tree):
            for block_attr in ("body", "orelse", "finalbody"):
                stmts = getattr(node, block_attr, None)
                if not isinstance(stmts, list) or len(stmts) < 2:
                    continue

                # Find runs of consecutive print statements
                current_group: List[ast.Expr] = []
                for stmt in stmts:
                    if is_print_call(stmt):
                        current_group.append(stmt)
                    else:
                        if len(current_group) >= 2:
                            break
                        current_group = []

                if len(current_group) < 2:
                    # Check if there are >= 3 total print statements in this block even if separated
                    all_prints = [s for s in stmts if is_print_call(s)]
                    if len(all_prints) >= 3:
                        current_group = all_prints

                if len(current_group) >= 2:
                    first_stmt = current_group[0]
                    last_stmt = current_group[-1]
                    start_line = getattr(first_stmt, "lineno", 1)
                    end_line = getattr(last_stmt, "end_lineno", getattr(last_stmt, "lineno", start_line))
                    col_offset = getattr(first_stmt, "col_offset", 0)
                    indent_str = " " * col_offset

                    # Collect original code snippet and lines
                    snippet = lines[start_line - 1].strip() if 0 < start_line <= len(lines) else "print(...)"
                    orig_lines = lines[start_line - 1 : end_line] if 0 < start_line <= len(lines) else [f"print(item_{i})" for i in range(len(current_group))]
                    original_snippet = "\n".join(orig_lines)

                    # Extract arguments from print statements
                    extracted_args = []
                    for s in current_group:
                        call = s.value
                        if call.args:
                            try:
                                # Unparse each argument
                                arg_text = ", ".join(ast.unparse(a) for a in call.args)
                                extracted_args.append(arg_text)
                            except Exception:
                                extracted_args.append("item")
                        else:
                            extracted_args.append("''")

                    # Formulate dynamic examples based on extracted arguments
                    count = len(current_group)
                    args_joined = ", ".join(extracted_args)
                    is_all_simple = count <= 8

                    if is_all_simple:
                        items_list_str = f"[{args_joined}]"
                        print_args_str = args_joined
                    else:
                        items_list_str = f"[{extracted_args[0]}, {extracted_args[1]}, ...]"
                        print_args_str = f"{extracted_args[0]}, {extracted_args[1]}, ..."

                    # Pattern object
                    patterns.append(
                        CodePattern(
                            id=f"perf-multiple-print-{start_line}",
                            title=f"Multiple Consecutive Print Statements ({count} calls)",
                            severity="medium" if count >= 3 else "low",
                            category="performance",
                            line=start_line,
                            column=col_offset,
                            snippet=snippet,
                            explanation=(
                                f"Detected {count} consecutive `print()` invocations. Calling `print()` repeatedly executes "
                                "multiple independent I/O system calls and stream flushes. This introduces redundant I/O overhead "
                                "and violates the DRY (Don't Repeat Yourself) principle."
                            ),
                            suggestion=(
                                f"Consolidate repetitive print calls into a `for` loop (e.g. `for item in [{args_joined}]: print(item)`), "
                                f"a single `print(..., sep='\\n')` call, or encapsulate into a reusable helper function."
                            ),
                        )
                    )

                    # Optimization suggestion with concrete, runnable refactorings
                    optimized_code_lines = [
                        f"{indent_str}# Option 1: Iterate using a for-loop (Clean & Scalable)",
                        f"{indent_str}for item in {items_list_str}:",
                        f"{indent_str}    print(item)",
                        f"",
                        f"{indent_str}# Option 2: Single print() with newline separator (Fastest I/O)",
                        f"{indent_str}print({print_args_str}, sep='\\n')",
                        f"",
                        f"{indent_str}# Option 3: Reusable helper function (Modular & DRY)",
                        f"{indent_str}def print_all(*items):",
                        f"{indent_str}    for item in items:",
                        f"{indent_str}        print(item)",
                        f"",
                        f"{indent_str}print_all({print_args_str})",
                    ]
                    optimized_code = "\n".join(optimized_code_lines)

                    diff_lines = [f"- {line}" for line in orig_lines]
                    diff_lines.append(f"+ # Refactored with loop:")
                    diff_lines.append(f"+ for item in {items_list_str}:")
                    diff_lines.append(f"+     print(item)")
                    diff_text = "\n".join(diff_lines)

                    optimizations.append(
                        OptimizationSuggestion(
                            id=f"opt-loop-function-print-{start_line}",
                            title="Refactor Repeated Prints to Loop or Helper Function",
                            category="performance",
                            impact="medium",
                            confidence="high",
                            explanation=(
                                "Invoking `print()` multiple times forces repeated system I/O context switching, locks `sys.stdout`, "
                                "and performs redundant line buffering. Replacing repetitive print statements with an iterable loop "
                                "or a single `print(*items, sep='\\n')` cuts boilerplate, eliminates I/O stalls, and makes adding new outputs trivial."
                            ),
                            original_code=original_snippet,
                            optimized_code=optimized_code,
                            diff=diff_text,
                            theoretical_benefit="Reduces multiple I/O system calls and stream flushes into a unified iteration or single buffered output.",
                        )
                    )
                    return

    def _check_exponential_recursion(
        self, tree: ast.AST, lines: List[str], patterns: List[CodePattern], optimizations: List[OptimizationSuggestion]
    ):
        """Detects un-memoized recursive calls creating branching trees (e.g. fib(n-1) + fib(n-2))."""
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_name = node.name
                # Check decorators for lru_cache or cache
                has_cache = any(
                    (isinstance(d, ast.Name) and d.id in ("cache", "lru_cache"))
                    or (isinstance(d, ast.Call) and isinstance(d.func, ast.Name) and d.func.id in ("cache", "lru_cache"))
                    or (isinstance(d, ast.Attribute) and d.attr in ("cache", "lru_cache"))
                    for d in node.decorator_list
                )
                if has_cache:
                    continue

                # Count calls to func_name inside body
                recursive_calls = []
                for sub in ast.walk(node):
                    if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Name) and sub.func.id == func_name:
                        recursive_calls.append(sub)

                if len(recursive_calls) >= 2:
                    line_num = getattr(recursive_calls[0], "lineno", node.lineno)
                    snippet = lines[line_num - 1].strip() if 0 < line_num <= len(lines) else f"return {func_name}(n-1) + {func_name}(n-2)"

                    patterns.append(
                        CodePattern(
                            id=f"comp-exp-recursion-{line_num}",
                            title="Un-memoized Branching Recursion (Exponential O(2^N))",
                            severity="high",
                            category="complexity",
                            line=line_num,
                            column=getattr(recursive_calls[0], "col_offset", 0),
                            snippet=snippet,
                            explanation=(
                                f"Function `{func_name}` makes multiple recursive self-calls without caching or memoization. "
                                "This creates an exponential call tree with O(2^N) runtime and repeated redundant sub-problem calculations."
                            ),
                            suggestion=f"Decorate the function with `@functools.lru_cache(maxsize=None)` or convert to iterative dynamic programming.",
                        )
                    )

                    optimizations.append(
                        OptimizationSuggestion(
                            id=f"opt-memoize-{line_num}",
                            title="Apply Memoization / Dynamic Programming",
                            category="complexity",
                            impact="high",
                            confidence="high",
                            explanation=(
                                "Without memoization, overlapping subproblems are recomputed exponentially many times. "
                                "Adding `@functools.lru_cache(None)` stores previously calculated return values in memory, "
                                "reducing time complexity from O(2^N) to O(N)."
                            ),
                            original_code=f"def {func_name}(n):\n    if n <= 1:\n        return n\n    return {func_name}(n - 1) + {func_name}(n - 2)",
                            optimized_code=f"from functools import lru_cache\n\n@lru_cache(maxsize=None)\ndef {func_name}(n):\n    if n <= 1:\n        return n\n    return {func_name}(n - 1) + {func_name}(n - 2)",
                            diff=f"+ from functools import lru_cache\n+ @lru_cache(maxsize=None)\n  def {func_name}(n):",
                            theoretical_benefit="Converts exponential O(2^N) execution down to linear O(N) by caching subproblem solutions.",
                        )
                    )
                    return

    def _check_multiple_prints(
        self, tree: ast.AST, lines: List[str], patterns: List[CodePattern], optimizations: List[OptimizationSuggestion]
    ):
        """Detects multiple consecutive or repeated print() statements and suggests using a loop or helper function."""
        def is_print_call(stmt: ast.AST) -> bool:
            return (
                isinstance(stmt, ast.Expr)
                and isinstance(stmt.value, ast.Call)
                and isinstance(stmt.value.func, ast.Name)
                and stmt.value.func.id == "print"
            )

        # Inspect all statement lists (module body, function bodies, if/else bodies, etc.)
        for node in ast.walk(tree):
            for block_attr in ("body", "orelse", "finalbody"):
                stmts = getattr(node, block_attr, None)
                if not isinstance(stmts, list) or len(stmts) < 2:
                    continue

                # Find runs of consecutive print statements
                current_group: List[ast.Expr] = []
                for stmt in stmts:
                    if is_print_call(stmt):
                        current_group.append(stmt)
                    else:
                        if len(current_group) >= 2:
                            break
                        current_group = []

                if len(current_group) < 2:
                    # Check if there are >= 3 total print statements in this block even if separated
                    all_prints = [s for s in stmts if is_print_call(s)]
                    if len(all_prints) >= 3:
                        current_group = all_prints

                if len(current_group) >= 2:
                    first_stmt = current_group[0]
                    last_stmt = current_group[-1]
                    start_line = getattr(first_stmt, "lineno", 1)
                    end_line = getattr(last_stmt, "end_lineno", getattr(last_stmt, "lineno", start_line))
                    col_offset = getattr(first_stmt, "col_offset", 0)
                    indent_str = " " * col_offset

                    # Collect original code snippet and lines
                    snippet = lines[start_line - 1].strip() if 0 < start_line <= len(lines) else "print(...)"
                    orig_lines = lines[start_line - 1 : end_line] if 0 < start_line <= len(lines) else [f"print(item_{i})" for i in range(len(current_group))]
                    original_snippet = "\n".join(orig_lines)

                    # Extract arguments from print statements
                    extracted_args = []
                    for s in current_group:
                        call = s.value
                        if call.args:
                            try:
                                # Unparse each argument
                                arg_text = ", ".join(ast.unparse(a) for a in call.args)
                                extracted_args.append(arg_text)
                            except Exception:
                                extracted_args.append("item")
                        else:
                            extracted_args.append("''")

                    # Formulate dynamic examples based on extracted arguments
                    count = len(current_group)
                    args_joined = ", ".join(extracted_args)
                    is_all_simple = count <= 8

                    if is_all_simple:
                        items_list_str = f"[{args_joined}]"
                        print_args_str = args_joined
                    else:
                        items_list_str = f"[{extracted_args[0]}, {extracted_args[1]}, ...]"
                        print_args_str = f"{extracted_args[0]}, {extracted_args[1]}, ..."

                    # Pattern object
                    patterns.append(
                        CodePattern(
                            id=f"perf-multiple-print-{start_line}",
                            title=f"Multiple Consecutive Print Statements ({count} calls)",
                            severity="medium" if count >= 3 else "low",
                            category="performance",
                            line=start_line,
                            column=col_offset,
                            snippet=snippet,
                            explanation=(
                                f"Detected {count} consecutive `print()` invocations. Calling `print()` repeatedly executes "
                                "multiple independent I/O system calls and stream flushes. This introduces redundant I/O overhead "
                                "and violates the DRY (Don't Repeat Yourself) principle."
                            ),
                            suggestion=(
                                f"Consolidate repetitive print calls into a `for` loop (e.g. `for item in [{args_joined}]: print(item)`), "
                                f"a single `print(..., sep='\\n')` call, or encapsulate into a reusable helper function."
                            ),
                        )
                    )

                    # Optimization suggestion with concrete, runnable refactorings
                    optimized_code_lines = [
                        f"{indent_str}# Option 1: Iterate using a for-loop (Clean & Scalable)",
                        f"{indent_str}for item in {items_list_str}:",
                        f"{indent_str}    print(item)",
                        f"",
                        f"{indent_str}# Option 2: Single print() with newline separator (Fastest I/O)",
                        f"{indent_str}print({print_args_str}, sep='\\n')",
                        f"",
                        f"{indent_str}# Option 3: Reusable helper function (Modular & DRY)",
                        f"{indent_str}def print_all(*items):",
                        f"{indent_str}    for item in items:",
                        f"{indent_str}        print(item)",
                        f"",
                        f"{indent_str}print_all({print_args_str})",
                    ]
                    optimized_code = "\n".join(optimized_code_lines)

                    diff_lines = [f"- {line}" for line in orig_lines]
                    diff_lines.append(f"+ # Refactored with loop:")
                    diff_lines.append(f"+ for item in {items_list_str}:")
                    diff_lines.append(f"+     print(item)")
                    diff_text = "\n".join(diff_lines)

                    optimizations.append(
                        OptimizationSuggestion(
                            id=f"opt-loop-function-print-{start_line}",
                            title="Refactor Repeated Prints to Loop or Helper Function",
                            category="performance",
                            impact="medium",
                            confidence="high",
                            explanation=(
                                "Invoking `print()` multiple times forces repeated system I/O context switching, locks `sys.stdout`, "
                                "and performs redundant line buffering. Replacing repetitive print statements with an iterable loop "
                                "or a single `print(*items, sep='\\n')` cuts boilerplate, eliminates I/O stalls, and makes adding new outputs trivial."
                            ),
                            original_code=original_snippet,
                            optimized_code=optimized_code,
                            diff=diff_text,
                            theoretical_benefit="Reduces multiple I/O system calls and stream flushes into a unified iteration or single buffered output.",
                        )
                    )
                    return

    def _check_bare_except(
        self, tree: ast.AST, lines: List[str], patterns: List[CodePattern], optimizations: List[OptimizationSuggestion]
    ):
        """Detects bare `except:` clauses."""
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler):
                if node.type is None:
                    line_num = getattr(node, "lineno", 1)
                    snippet = lines[line_num - 1].strip() if 0 < line_num <= len(lines) else "except:"

                    patterns.append(
                        CodePattern(
                            id=f"bp-bare-except-{line_num}",
                            title="Bare 'except:' Swallowing System Signals",
                            severity="medium",
                            category="best_practice",
                            line=line_num,
                            column=getattr(node, "col_offset", 0),
                            snippet=snippet,
                            explanation=(
                                "A bare `except:` clause intercepts `BaseException`, silently catching `KeyboardInterrupt`, "
                                "`SystemExit`, and memory errors, which prevents graceful process termination."
                            ),
                            suggestion="Catch `except Exception:` or catch the specific expected exceptions (e.g., `except (ValueError, KeyError):`).",
                        )
                    )

                    optimizations.append(
                        OptimizationSuggestion(
                            id=f"opt-specific-except-{line_num}",
                            title="Specify Explicit Exception Types",
                            category="best_practice",
                            impact="medium",
                            confidence="high",
                            explanation=(
                                "Replacing bare `except:` with `except Exception:` ensures standard runtime errors are captured "
                                "while letting control signals (like Ctrl+C / SIGINT) propagate naturally."
                            ),
                            original_code="try:\n    perform_action()\nexcept:\n    pass",
                            optimized_code="try:\n    perform_action()\nexcept Exception as e:\n    logging.error(f'Failed: {e}')",
                            diff="- except:\n+ except Exception as e:\n+     logging.error(f'Failed: {e}')",
                            theoretical_benefit="Prevents program hangs, zombie threads, and masked critical runtime defects.",
                        )
                    )
                    return

    def _check_multiple_prints(
        self, tree: ast.AST, lines: List[str], patterns: List[CodePattern], optimizations: List[OptimizationSuggestion]
    ):
        """Detects multiple consecutive or repeated print() statements and suggests using a loop or helper function."""
        def is_print_call(stmt: ast.AST) -> bool:
            return (
                isinstance(stmt, ast.Expr)
                and isinstance(stmt.value, ast.Call)
                and isinstance(stmt.value.func, ast.Name)
                and stmt.value.func.id == "print"
            )

        # Inspect all statement lists (module body, function bodies, if/else bodies, etc.)
        for node in ast.walk(tree):
            for block_attr in ("body", "orelse", "finalbody"):
                stmts = getattr(node, block_attr, None)
                if not isinstance(stmts, list) or len(stmts) < 2:
                    continue

                # Find runs of consecutive print statements
                current_group: List[ast.Expr] = []
                for stmt in stmts:
                    if is_print_call(stmt):
                        current_group.append(stmt)
                    else:
                        if len(current_group) >= 2:
                            break
                        current_group = []

                if len(current_group) < 2:
                    # Check if there are >= 3 total print statements in this block even if separated
                    all_prints = [s for s in stmts if is_print_call(s)]
                    if len(all_prints) >= 3:
                        current_group = all_prints

                if len(current_group) >= 2:
                    first_stmt = current_group[0]
                    last_stmt = current_group[-1]
                    start_line = getattr(first_stmt, "lineno", 1)
                    end_line = getattr(last_stmt, "end_lineno", getattr(last_stmt, "lineno", start_line))
                    col_offset = getattr(first_stmt, "col_offset", 0)
                    indent_str = " " * col_offset

                    # Collect original code snippet and lines
                    snippet = lines[start_line - 1].strip() if 0 < start_line <= len(lines) else "print(...)"
                    orig_lines = lines[start_line - 1 : end_line] if 0 < start_line <= len(lines) else [f"print(item_{i})" for i in range(len(current_group))]
                    original_snippet = "\n".join(orig_lines)

                    # Extract arguments from print statements
                    extracted_args = []
                    for s in current_group:
                        call = s.value
                        if call.args:
                            try:
                                # Unparse each argument
                                arg_text = ", ".join(ast.unparse(a) for a in call.args)
                                extracted_args.append(arg_text)
                            except Exception:
                                extracted_args.append("item")
                        else:
                            extracted_args.append("''")

                    # Formulate dynamic examples based on extracted arguments
                    count = len(current_group)
                    args_joined = ", ".join(extracted_args)
                    is_all_simple = count <= 8

                    if is_all_simple:
                        items_list_str = f"[{args_joined}]"
                        print_args_str = args_joined
                    else:
                        items_list_str = f"[{extracted_args[0]}, {extracted_args[1]}, ...]"
                        print_args_str = f"{extracted_args[0]}, {extracted_args[1]}, ..."

                    # Pattern object
                    patterns.append(
                        CodePattern(
                            id=f"perf-multiple-print-{start_line}",
                            title=f"Multiple Consecutive Print Statements ({count} calls)",
                            severity="medium" if count >= 3 else "low",
                            category="performance",
                            line=start_line,
                            column=col_offset,
                            snippet=snippet,
                            explanation=(
                                f"Detected {count} consecutive `print()` invocations. Calling `print()` repeatedly executes "
                                "multiple independent I/O system calls and stream flushes. This introduces redundant I/O overhead "
                                "and violates the DRY (Don't Repeat Yourself) principle."
                            ),
                            suggestion=(
                                f"Consolidate repetitive print calls into a `for` loop (e.g. `for item in [{args_joined}]: print(item)`), "
                                f"a single `print(..., sep='\\n')` call, or encapsulate into a reusable helper function."
                            ),
                        )
                    )

                    # Optimization suggestion with concrete, runnable refactorings
                    optimized_code_lines = [
                        f"{indent_str}# Option 1: Iterate using a for-loop (Clean & Scalable)",
                        f"{indent_str}for item in {items_list_str}:",
                        f"{indent_str}    print(item)",
                        f"",
                        f"{indent_str}# Option 2: Single print() with newline separator (Fastest I/O)",
                        f"{indent_str}print({print_args_str}, sep='\\n')",
                        f"",
                        f"{indent_str}# Option 3: Reusable helper function (Modular & DRY)",
                        f"{indent_str}def print_all(*items):",
                        f"{indent_str}    for item in items:",
                        f"{indent_str}        print(item)",
                        f"",
                        f"{indent_str}print_all({print_args_str})",
                    ]
                    optimized_code = "\n".join(optimized_code_lines)

                    diff_lines = [f"- {line}" for line in orig_lines]
                    diff_lines.append(f"+ # Refactored with loop:")
                    diff_lines.append(f"+ for item in {items_list_str}:")
                    diff_lines.append(f"+     print(item)")
                    diff_text = "\n".join(diff_lines)

                    optimizations.append(
                        OptimizationSuggestion(
                            id=f"opt-loop-function-print-{start_line}",
                            title="Refactor Repeated Prints to Loop or Helper Function",
                            category="performance",
                            impact="medium",
                            confidence="high",
                            explanation=(
                                "Invoking `print()` multiple times forces repeated system I/O context switching, locks `sys.stdout`, "
                                "and performs redundant line buffering. Replacing repetitive print statements with an iterable loop "
                                "or a single `print(*items, sep='\\n')` cuts boilerplate, eliminates I/O stalls, and makes adding new outputs trivial."
                            ),
                            original_code=original_snippet,
                            optimized_code=optimized_code,
                            diff=diff_text,
                            theoretical_benefit="Reduces multiple I/O system calls and stream flushes into a unified iteration or single buffered output.",
                        )
                    )
                    return

    def _check_unclosed_files(
        self, tree: ast.AST, lines: List[str], patterns: List[CodePattern], optimizations: List[OptimizationSuggestion]
    ):
        """Detects `open(...)` call assigned outside of a `with` context manager."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name) and node.value.func.id == "open":
                    line_num = getattr(node, "lineno", 1)
                    snippet = lines[line_num - 1].strip() if 0 < line_num <= len(lines) else "f = open('data.txt')"

                    patterns.append(
                        CodePattern(
                            id=f"bp-unclosed-file-{line_num}",
                            title="File Opened Without Context Manager (Resource Leak)",
                            severity="medium",
                            category="best_practice",
                            line=line_num,
                            column=getattr(node, "col_offset", 0),
                            snippet=snippet,
                            explanation=(
                                "Calling `open()` without a `with` statement risks leaking file descriptors if an unhandled exception "
                                "occurs before `.close()` is executed."
                            ),
                            suggestion="Use `with open(...) as f:` to guarantee file closure even in failure scenarios.",
                        )
                    )

                    optimizations.append(
                        OptimizationSuggestion(
                            id=f"opt-context-manager-{line_num}",
                            title="Wrap File I/O in 'with' Context Manager",
                            category="best_practice",
                            impact="medium",
                            confidence="high",
                            explanation=(
                                "Context managers guarantee deterministic file handle deallocation using Python's `__enter__` and `__exit__` "
                                "dunder protocol, preventing file descriptor starvation under high load."
                            ),
                            original_code="f = open('data.txt', 'r')\ncontent = f.read()\nf.close()",
                            optimized_code="with open('data.txt', 'r') as f:\n    content = f.read()",
                            diff="- f = open('data.txt', 'r')\n- content = f.read()\n- f.close()\n+ with open('data.txt', 'r') as f:\n+     content = f.read()",
                            theoretical_benefit="Guarantees file descriptor cleanup and prevents resource exhaustion.",
                        )
                    )
                    return

    def _check_multiple_prints(
        self, tree: ast.AST, lines: List[str], patterns: List[CodePattern], optimizations: List[OptimizationSuggestion]
    ):
        """Detects multiple consecutive or repeated print() statements and suggests using a loop or helper function."""
        def is_print_call(stmt: ast.AST) -> bool:
            return (
                isinstance(stmt, ast.Expr)
                and isinstance(stmt.value, ast.Call)
                and isinstance(stmt.value.func, ast.Name)
                and stmt.value.func.id == "print"
            )

        # Inspect all statement lists (module body, function bodies, if/else bodies, etc.)
        for node in ast.walk(tree):
            for block_attr in ("body", "orelse", "finalbody"):
                stmts = getattr(node, block_attr, None)
                if not isinstance(stmts, list) or len(stmts) < 2:
                    continue

                # Find runs of consecutive print statements
                current_group: List[ast.Expr] = []
                for stmt in stmts:
                    if is_print_call(stmt):
                        current_group.append(stmt)
                    else:
                        if len(current_group) >= 2:
                            break
                        current_group = []

                if len(current_group) < 2:
                    # Check if there are >= 3 total print statements in this block even if separated
                    all_prints = [s for s in stmts if is_print_call(s)]
                    if len(all_prints) >= 3:
                        current_group = all_prints

                if len(current_group) >= 2:
                    first_stmt = current_group[0]
                    last_stmt = current_group[-1]
                    start_line = getattr(first_stmt, "lineno", 1)
                    end_line = getattr(last_stmt, "end_lineno", getattr(last_stmt, "lineno", start_line))
                    col_offset = getattr(first_stmt, "col_offset", 0)
                    indent_str = " " * col_offset

                    # Collect original code snippet and lines
                    snippet = lines[start_line - 1].strip() if 0 < start_line <= len(lines) else "print(...)"
                    orig_lines = lines[start_line - 1 : end_line] if 0 < start_line <= len(lines) else [f"print(item_{i})" for i in range(len(current_group))]
                    original_snippet = "\n".join(orig_lines)

                    # Extract arguments from print statements
                    extracted_args = []
                    for s in current_group:
                        call = s.value
                        if call.args:
                            try:
                                # Unparse each argument
                                arg_text = ", ".join(ast.unparse(a) for a in call.args)
                                extracted_args.append(arg_text)
                            except Exception:
                                extracted_args.append("item")
                        else:
                            extracted_args.append("''")

                    # Formulate dynamic examples based on extracted arguments
                    count = len(current_group)
                    args_joined = ", ".join(extracted_args)
                    is_all_simple = count <= 8

                    if is_all_simple:
                        items_list_str = f"[{args_joined}]"
                        print_args_str = args_joined
                    else:
                        items_list_str = f"[{extracted_args[0]}, {extracted_args[1]}, ...]"
                        print_args_str = f"{extracted_args[0]}, {extracted_args[1]}, ..."

                    # Pattern object
                    patterns.append(
                        CodePattern(
                            id=f"perf-multiple-print-{start_line}",
                            title=f"Multiple Consecutive Print Statements ({count} calls)",
                            severity="medium" if count >= 3 else "low",
                            category="performance",
                            line=start_line,
                            column=col_offset,
                            snippet=snippet,
                            explanation=(
                                f"Detected {count} consecutive `print()` invocations. Calling `print()` repeatedly executes "
                                "multiple independent I/O system calls and stream flushes. This introduces redundant I/O overhead "
                                "and violates the DRY (Don't Repeat Yourself) principle."
                            ),
                            suggestion=(
                                f"Consolidate repetitive print calls into a `for` loop (e.g. `for item in [{args_joined}]: print(item)`), "
                                f"a single `print(..., sep='\\n')` call, or encapsulate into a reusable helper function."
                            ),
                        )
                    )

                    # Optimization suggestion with concrete, runnable refactorings
                    optimized_code_lines = [
                        f"{indent_str}# Option 1: Iterate using a for-loop (Clean & Scalable)",
                        f"{indent_str}for item in {items_list_str}:",
                        f"{indent_str}    print(item)",
                        f"",
                        f"{indent_str}# Option 2: Single print() with newline separator (Fastest I/O)",
                        f"{indent_str}print({print_args_str}, sep='\\n')",
                        f"",
                        f"{indent_str}# Option 3: Reusable helper function (Modular & DRY)",
                        f"{indent_str}def print_all(*items):",
                        f"{indent_str}    for item in items:",
                        f"{indent_str}        print(item)",
                        f"",
                        f"{indent_str}print_all({print_args_str})",
                    ]
                    optimized_code = "\n".join(optimized_code_lines)

                    diff_lines = [f"- {line}" for line in orig_lines]
                    diff_lines.append(f"+ # Refactored with loop:")
                    diff_lines.append(f"+ for item in {items_list_str}:")
                    diff_lines.append(f"+     print(item)")
                    diff_text = "\n".join(diff_lines)

                    optimizations.append(
                        OptimizationSuggestion(
                            id=f"opt-loop-function-print-{start_line}",
                            title="Refactor Repeated Prints to Loop or Helper Function",
                            category="performance",
                            impact="medium",
                            confidence="high",
                            explanation=(
                                "Invoking `print()` multiple times forces repeated system I/O context switching, locks `sys.stdout`, "
                                "and performs redundant line buffering. Replacing repetitive print statements with an iterable loop "
                                "or a single `print(*items, sep='\\n')` cuts boilerplate, eliminates I/O stalls, and makes adding new outputs trivial."
                            ),
                            original_code=original_snippet,
                            optimized_code=optimized_code,
                            diff=diff_text,
                            theoretical_benefit="Reduces multiple I/O system calls and stream flushes into a unified iteration or single buffered output.",
                        )
                    )
                    return

    def _check_redundant_dict_keys(
        self, tree: ast.AST, lines: List[str], patterns: List[CodePattern], optimizations: List[OptimizationSuggestion]
    ):
        """Detects `for k in d.keys():` or `x in d.keys()`."""
        for node in ast.walk(tree):
            # Check `for k in d.keys()`
            if isinstance(node, ast.For):
                if isinstance(node.iter, ast.Call) and isinstance(node.iter.func, ast.Attribute) and node.iter.func.attr == "keys":
                    line_num = getattr(node, "lineno", 1)
                    d_name = node.iter.func.value.id if isinstance(node.iter.func.value, ast.Name) else "d"
                    snippet = lines[line_num - 1].strip() if 0 < line_num <= len(lines) else f"for k in {d_name}.keys():"

                    patterns.append(
                        CodePattern(
                            id=f"idiom-dict-keys-{line_num}",
                            title="Redundant .keys() Call on Dictionary",
                            severity="low",
                            category="idiom",
                            line=line_num,
                            column=getattr(node, "col_offset", 0),
                            snippet=snippet,
                            explanation=(
                                f"Calling `.{d_name}.keys()` creates an extra method call and dict-key view object. "
                                f"Directly iterating `{d_name}` iterates over its keys natively."
                            ),
                            suggestion=f"Write `for k in {d_name}:` instead of `for k in {d_name}.keys():`.",
                        )
                    )
                    return

    def _check_multiple_prints(
        self, tree: ast.AST, lines: List[str], patterns: List[CodePattern], optimizations: List[OptimizationSuggestion]
    ):
        """Detects multiple consecutive or repeated print() statements and suggests using a loop or helper function."""
        def is_print_call(stmt: ast.AST) -> bool:
            return (
                isinstance(stmt, ast.Expr)
                and isinstance(stmt.value, ast.Call)
                and isinstance(stmt.value.func, ast.Name)
                and stmt.value.func.id == "print"
            )

        # Inspect all statement lists (module body, function bodies, if/else bodies, etc.)
        for node in ast.walk(tree):
            for block_attr in ("body", "orelse", "finalbody"):
                stmts = getattr(node, block_attr, None)
                if not isinstance(stmts, list) or len(stmts) < 2:
                    continue

                # Find runs of consecutive print statements
                current_group: List[ast.Expr] = []
                for stmt in stmts:
                    if is_print_call(stmt):
                        current_group.append(stmt)
                    else:
                        if len(current_group) >= 2:
                            break
                        current_group = []

                if len(current_group) < 2:
                    # Check if there are >= 3 total print statements in this block even if separated
                    all_prints = [s for s in stmts if is_print_call(s)]
                    if len(all_prints) >= 3:
                        current_group = all_prints

                if len(current_group) >= 2:
                    first_stmt = current_group[0]
                    last_stmt = current_group[-1]
                    start_line = getattr(first_stmt, "lineno", 1)
                    end_line = getattr(last_stmt, "end_lineno", getattr(last_stmt, "lineno", start_line))
                    col_offset = getattr(first_stmt, "col_offset", 0)
                    indent_str = " " * col_offset

                    # Collect original code snippet and lines
                    snippet = lines[start_line - 1].strip() if 0 < start_line <= len(lines) else "print(...)"
                    orig_lines = lines[start_line - 1 : end_line] if 0 < start_line <= len(lines) else [f"print(item_{i})" for i in range(len(current_group))]
                    original_snippet = "\n".join(orig_lines)

                    # Extract arguments from print statements
                    extracted_args = []
                    for s in current_group:
                        call = s.value
                        if call.args:
                            try:
                                # Unparse each argument
                                arg_text = ", ".join(ast.unparse(a) for a in call.args)
                                extracted_args.append(arg_text)
                            except Exception:
                                extracted_args.append("item")
                        else:
                            extracted_args.append("''")

                    # Formulate dynamic examples based on extracted arguments
                    count = len(current_group)
                    args_joined = ", ".join(extracted_args)
                    is_all_simple = count <= 8

                    if is_all_simple:
                        items_list_str = f"[{args_joined}]"
                        print_args_str = args_joined
                    else:
                        items_list_str = f"[{extracted_args[0]}, {extracted_args[1]}, ...]"
                        print_args_str = f"{extracted_args[0]}, {extracted_args[1]}, ..."

                    # Pattern object
                    patterns.append(
                        CodePattern(
                            id=f"perf-multiple-print-{start_line}",
                            title=f"Multiple Consecutive Print Statements ({count} calls)",
                            severity="medium" if count >= 3 else "low",
                            category="performance",
                            line=start_line,
                            column=col_offset,
                            snippet=snippet,
                            explanation=(
                                f"Detected {count} consecutive `print()` invocations. Calling `print()` repeatedly executes "
                                "multiple independent I/O system calls and stream flushes. This introduces redundant I/O overhead "
                                "and violates the DRY (Don't Repeat Yourself) principle."
                            ),
                            suggestion=(
                                f"Consolidate repetitive print calls into a `for` loop (e.g. `for item in [{args_joined}]: print(item)`), "
                                f"a single `print(..., sep='\\n')` call, or encapsulate into a reusable helper function."
                            ),
                        )
                    )

                    # Optimization suggestion with concrete, runnable refactorings
                    optimized_code_lines = [
                        f"{indent_str}# Option 1: Iterate using a for-loop (Clean & Scalable)",
                        f"{indent_str}for item in {items_list_str}:",
                        f"{indent_str}    print(item)",
                        f"",
                        f"{indent_str}# Option 2: Single print() with newline separator (Fastest I/O)",
                        f"{indent_str}print({print_args_str}, sep='\\n')",
                        f"",
                        f"{indent_str}# Option 3: Reusable helper function (Modular & DRY)",
                        f"{indent_str}def print_all(*items):",
                        f"{indent_str}    for item in items:",
                        f"{indent_str}        print(item)",
                        f"",
                        f"{indent_str}print_all({print_args_str})",
                    ]
                    optimized_code = "\n".join(optimized_code_lines)

                    diff_lines = [f"- {line}" for line in orig_lines]
                    diff_lines.append(f"+ # Refactored with loop:")
                    diff_lines.append(f"+ for item in {items_list_str}:")
                    diff_lines.append(f"+     print(item)")
                    diff_text = "\n".join(diff_lines)

                    optimizations.append(
                        OptimizationSuggestion(
                            id=f"opt-loop-function-print-{start_line}",
                            title="Refactor Repeated Prints to Loop or Helper Function",
                            category="performance",
                            impact="medium",
                            confidence="high",
                            explanation=(
                                "Invoking `print()` multiple times forces repeated system I/O context switching, locks `sys.stdout`, "
                                "and performs redundant line buffering. Replacing repetitive print statements with an iterable loop "
                                "or a single `print(*items, sep='\\n')` cuts boilerplate, eliminates I/O stalls, and makes adding new outputs trivial."
                            ),
                            original_code=original_snippet,
                            optimized_code=optimized_code,
                            diff=diff_text,
                            theoretical_benefit="Reduces multiple I/O system calls and stream flushes into a unified iteration or single buffered output.",
                        )
                    )
                    return

    def _check_repeated_append_pattern(
        self, tree: ast.AST, lines: List[str], patterns: List[CodePattern], optimizations: List[OptimizationSuggestion]
    ):
        """Detects simple loops where every iteration just calls `list.append()`."""
        for node in ast.walk(tree):
            if isinstance(node, ast.For) and len(node.body) == 1:
                stmt = node.body[0]
                if (
                    isinstance(stmt, ast.Expr)
                    and isinstance(stmt.value, ast.Call)
                    and isinstance(stmt.value.func, ast.Attribute)
                    and stmt.value.func.attr == "append"
                ):
                    line_num = node.lineno
                    list_name = stmt.value.func.value.id if isinstance(stmt.value.func.value, ast.Name) else "results"
                    snippet = lines[line_num - 1].strip() if 0 < line_num <= len(lines) else f"for item in data: {list_name}.append(...)"

                    patterns.append(
                        CodePattern(
                            id=f"perf-append-loop-{line_num}",
                            title="Loop Accumulation with Repeated .append()",
                            severity="medium",
                            category="performance",
                            line=line_num,
                            column=node.col_offset,
                            snippet=snippet,
                            explanation=(
                                f"Repeatedly invoking `{list_name}.append()` in a standard loop pays attribute lookup and method invocation "
                                "overhead on each cycle. List comprehensions are optimized in CPython's C loop with `LIST_APPEND` opcodes."
                            ),
                            suggestion="Refactor loop into a list comprehension for cleaner syntax and faster execution.",
                        )
                    )

                    optimizations.append(
                        OptimizationSuggestion(
                            id=f"opt-list-comp-{line_num}",
                            title="Convert Loop Append to List Comprehension",
                            category="performance",
                            impact="medium",
                            confidence="high",
                            explanation=(
                                "List comprehensions run significantly faster than explicit for-loops in CPython because "
                                "the bytecode utilizes a specialized `LIST_APPEND` opcode without popping and pushing items onto the Python evaluation stack."
                            ),
                            original_code=f"{list_name} = []\nfor item in data:\n    {list_name}.append(transform(item))",
                            optimized_code=f"{list_name} = [transform(item) for item in data]",
                            diff=f"- {list_name} = []\n- for item in data:\n-     {list_name}.append(transform(item))\n+ {list_name} = [transform(item) for item in data]",
                            theoretical_benefit="Improves execution speed by ~20-30% in CPython via specialized stack opcodes.",
                        )
                    )
                    return

    def _check_multiple_prints(
        self, tree: ast.AST, lines: List[str], patterns: List[CodePattern], optimizations: List[OptimizationSuggestion]
    ):
        """Detects multiple consecutive or repeated print() statements and suggests using a loop or helper function."""
        def is_print_call(stmt: ast.AST) -> bool:
            return (
                isinstance(stmt, ast.Expr)
                and isinstance(stmt.value, ast.Call)
                and isinstance(stmt.value.func, ast.Name)
                and stmt.value.func.id == "print"
            )

        for node in ast.walk(tree):
            for block_attr in ("body", "orelse", "finalbody"):
                stmts = getattr(node, block_attr, None)
                if not isinstance(stmts, list) or len(stmts) < 2:
                    continue

                # Find runs of consecutive print statements
                current_group: List[ast.Expr] = []
                for stmt in stmts:
                    if is_print_call(stmt):
                        current_group.append(stmt)
                    else:
                        if len(current_group) >= 2:
                            break
                        current_group = []

                if len(current_group) < 2:
                    # Check if there are >= 3 total print statements in this block even if separated
                    all_prints = [s for s in stmts if is_print_call(s)]
                    if len(all_prints) >= 3:
                        current_group = all_prints

                if len(current_group) >= 2:
                    first_stmt = current_group[0]
                    last_stmt = current_group[-1]
                    start_line = getattr(first_stmt, "lineno", 1)
                    end_line = getattr(last_stmt, "end_lineno", getattr(last_stmt, "lineno", start_line))
                    col_offset = getattr(first_stmt, "col_offset", 0)
                    indent_str = " " * col_offset

                    snippet = lines[start_line - 1].strip() if 0 < start_line <= len(lines) else "print(...)"
                    orig_lines = lines[start_line - 1 : end_line] if 0 < start_line <= len(lines) else [f"print(item_{i})" for i in range(len(current_group))]
                    original_snippet = "\n".join(orig_lines)

                    extracted_args = []
                    for s in current_group:
                        call = s.value
                        if call.args:
                            try:
                                arg_text = ", ".join(ast.unparse(a) for a in call.args)
                                extracted_args.append(arg_text)
                            except Exception:
                                extracted_args.append("item")
                        else:
                            extracted_args.append("''")

                    count = len(current_group)
                    args_joined = ", ".join(extracted_args)
                    is_all_simple = count <= 8

                    if is_all_simple:
                        items_list_str = f"[{args_joined}]"
                        print_args_str = args_joined
                    else:
                        items_list_str = f"[{extracted_args[0]}, {extracted_args[1]}, ...]"
                        print_args_str = f"{extracted_args[0]}, {extracted_args[1]}, ..."

                    patterns.append(
                        CodePattern(
                            id=f"perf-multiple-print-{start_line}",
                            title=f"Multiple Consecutive Print Statements ({count} calls)",
                            severity="medium" if count >= 3 else "low",
                            category="performance",
                            line=start_line,
                            column=col_offset,
                            snippet=snippet,
                            explanation=(
                                f"Detected {count} consecutive `print()` invocations. Calling `print()` repeatedly executes "
                                "multiple independent I/O system calls and stream flushes. This introduces redundant I/O overhead "
                                "and violates the DRY (Don't Repeat Yourself) principle."
                            ),
                            suggestion=(
                                f"Consolidate repetitive print calls into a `for` loop (e.g. `for item in [{args_joined}]: print(item)`), "
                                f"a single `print(..., sep='\\n')` call, or encapsulate into a reusable helper function."
                            ),
                        )
                    )

                    optimized_code_lines = [
                        f"{indent_str}# Option 1: Iterate using a for-loop (Clean & Scalable)",
                        f"{indent_str}for item in {items_list_str}:",
                        f"{indent_str}    print(item)",
                        f"",
                        f"{indent_str}# Option 2: Single print() with newline separator (Fastest I/O)",
                        f"{indent_str}print({print_args_str}, sep='\\n')",
                        f"",
                        f"{indent_str}# Option 3: Reusable helper function (Modular & DRY)",
                        f"{indent_str}def print_all(*items):",
                        f"{indent_str}    for item in items:",
                        f"{indent_str}        print(item)",
                        f"",
                        f"{indent_str}print_all({print_args_str})",
                    ]
                    optimized_code = "\n".join(optimized_code_lines)

                    diff_lines = [f"- {line}" for line in orig_lines]
                    diff_lines.append(f"+ # Refactored with loop:")
                    diff_lines.append(f"+ for item in {items_list_str}:")
                    diff_lines.append(f"+     print(item)")
                    diff_text = "\n".join(diff_lines)

                    optimizations.append(
                        OptimizationSuggestion(
                            id=f"opt-loop-function-print-{start_line}",
                            title="Refactor Repeated Prints to Loop or Helper Function",
                            category="performance",
                            impact="medium",
                            confidence="high",
                            explanation=(
                                "Invoking `print()` multiple times forces repeated system I/O context switching, locks `sys.stdout`, "
                                "and performs redundant line buffering. Replacing repetitive print statements with an iterable loop "
                                "or a single `print(*items, sep='\\n')` cuts boilerplate, eliminates I/O stalls, and makes adding new outputs trivial."
                            ),
                            original_code=original_snippet,
                            optimized_code=optimized_code,
                            diff=diff_text,
                            theoretical_benefit="Reduces multiple I/O system calls and stream flushes into a unified iteration or single buffered output.",
                        )
                    )
                    return

    def _check_multiple_prints(
        self, tree: ast.AST, lines: List[str], patterns: List[CodePattern], optimizations: List[OptimizationSuggestion]
    ):
        """Detects multiple consecutive or repeated print() statements and suggests using a loop or helper function."""
        def is_print_call(stmt: ast.AST) -> bool:
            return (
                isinstance(stmt, ast.Expr)
                and isinstance(stmt.value, ast.Call)
                and isinstance(stmt.value.func, ast.Name)
                and stmt.value.func.id == "print"
            )

        # Inspect all statement lists (module body, function bodies, if/else bodies, etc.)
        for node in ast.walk(tree):
            for block_attr in ("body", "orelse", "finalbody"):
                stmts = getattr(node, block_attr, None)
                if not isinstance(stmts, list) or len(stmts) < 2:
                    continue

                # Find runs of consecutive print statements
                current_group: List[ast.Expr] = []
                for stmt in stmts:
                    if is_print_call(stmt):
                        current_group.append(stmt)
                    else:
                        if len(current_group) >= 2:
                            break
                        current_group = []

                if len(current_group) < 2:
                    # Check if there are >= 3 total print statements in this block even if separated
                    all_prints = [s for s in stmts if is_print_call(s)]
                    if len(all_prints) >= 3:
                        current_group = all_prints

                if len(current_group) >= 2:
                    first_stmt = current_group[0]
                    last_stmt = current_group[-1]
                    start_line = getattr(first_stmt, "lineno", 1)
                    end_line = getattr(last_stmt, "end_lineno", getattr(last_stmt, "lineno", start_line))
                    col_offset = getattr(first_stmt, "col_offset", 0)
                    indent_str = " " * col_offset

                    # Collect original code snippet and lines
                    snippet = lines[start_line - 1].strip() if 0 < start_line <= len(lines) else "print(...)"
                    orig_lines = lines[start_line - 1 : end_line] if 0 < start_line <= len(lines) else [f"print(item_{i})" for i in range(len(current_group))]
                    original_snippet = "\n".join(orig_lines)

                    # Extract arguments from print statements
                    extracted_args = []
                    for s in current_group:
                        call = s.value
                        if call.args:
                            try:
                                # Unparse each argument
                                arg_text = ", ".join(ast.unparse(a) for a in call.args)
                                extracted_args.append(arg_text)
                            except Exception:
                                extracted_args.append("item")
                        else:
                            extracted_args.append("''")

                    # Formulate dynamic examples based on extracted arguments
                    count = len(current_group)
                    args_joined = ", ".join(extracted_args)
                    is_all_simple = count <= 8

                    if is_all_simple:
                        items_list_str = f"[{args_joined}]"
                        print_args_str = args_joined
                    else:
                        items_list_str = f"[{extracted_args[0]}, {extracted_args[1]}, ...]"
                        print_args_str = f"{extracted_args[0]}, {extracted_args[1]}, ..."

                    # Pattern object
                    patterns.append(
                        CodePattern(
                            id=f"perf-multiple-print-{start_line}",
                            title=f"Multiple Consecutive Print Statements ({count} calls)",
                            severity="medium" if count >= 3 else "low",
                            category="performance",
                            line=start_line,
                            column=col_offset,
                            snippet=snippet,
                            explanation=(
                                f"Detected {count} consecutive `print()` invocations. Calling `print()` repeatedly executes "
                                "multiple independent I/O system calls and stream flushes. This introduces redundant I/O overhead "
                                "and violates the DRY (Don't Repeat Yourself) principle."
                            ),
                            suggestion=(
                                f"Consolidate repetitive print calls into a `for` loop (e.g. `for item in [{args_joined}]: print(item)`), "
                                f"a single `print(..., sep='\\n')` call, or encapsulate into a reusable helper function."
                            ),
                        )
                    )

                    # Optimization suggestion with concrete, runnable refactorings
                    optimized_code_lines = [
                        f"{indent_str}# Option 1: Iterate using a for-loop (Clean & Scalable)",
                        f"{indent_str}for item in {items_list_str}:",
                        f"{indent_str}    print(item)",
                        f"",
                        f"{indent_str}# Option 2: Single print() with newline separator (Fastest I/O)",
                        f"{indent_str}print({print_args_str}, sep='\\n')",
                        f"",
                        f"{indent_str}# Option 3: Reusable helper function (Modular & DRY)",
                        f"{indent_str}def print_all(*items):",
                        f"{indent_str}    for item in items:",
                        f"{indent_str}        print(item)",
                        f"",
                        f"{indent_str}print_all({print_args_str})",
                    ]
                    optimized_code = "\n".join(optimized_code_lines)

                    diff_lines = [f"- {line}" for line in orig_lines]
                    diff_lines.append(f"+ # Refactored with loop:")
                    diff_lines.append(f"+ for item in {items_list_str}:")
                    diff_lines.append(f"+     print(item)")
                    diff_text = "\n".join(diff_lines)

                    optimizations.append(
                        OptimizationSuggestion(
                            id=f"opt-loop-function-print-{start_line}",
                            title="Refactor Repeated Prints to Loop or Helper Function",
                            category="performance",
                            impact="medium",
                            confidence="high",
                            explanation=(
                                "Invoking `print()` multiple times forces repeated system I/O context switching, locks `sys.stdout`, "
                                "and performs redundant line buffering. Replacing repetitive print statements with an iterable loop "
                                "or a single `print(*items, sep='\\n')` cuts boilerplate, eliminates I/O stalls, and makes adding new outputs trivial."
                            ),
                            original_code=original_snippet,
                            optimized_code=optimized_code,
                            diff=diff_text,
                            theoretical_benefit="Reduces multiple I/O system calls and stream flushes into a unified iteration or single buffered output.",
                        )
                    )
                    return

    # -------------------------------------------------------------------------
    # Complexity Estimation
    # -------------------------------------------------------------------------
    def _estimate_complexity(self, tree: ast.AST, patterns: List[CodePattern]) -> ComplexityEstimate:
        """Estimates Time and Space complexity based on structural AST properties with uncertainty indicators."""
        pattern_ids = {p.id for p in patterns}

        # Check for exponential recursion
        has_exp_recursion = any("comp-exp-recursion" in pid for pid in pattern_ids)
        if has_exp_recursion:
            return ComplexityEstimate(
                time_complexity="O(2^n)",
                space_complexity="O(n)",
                confidence="medium",
                reasons=[
                    "Multiple recursive self-calls discovered without caching/memoization.",
                    "Forms an un-pruned recursive branching tree with height bounded by N.",
                    "Auxiliary space bounded by recursion call stack depth of O(n) frames.",
                ],
                uncertainty_factors=[
                    "Actual branching factor depends on the recurrence relation (e.g. T(n-1)+T(n-2) vs T(n/2)).",
                    "Dynamic base cases or early return guards may terminate branches early.",
                ],
            )

        # Check loop nesting depth
        max_loop_depth = 0
        has_halving_loop = False

        for node in ast.walk(tree):
            if isinstance(node, (ast.For, ast.While)):
                depth = 1
                for sub in ast.walk(node):
                    if sub is not node and isinstance(sub, (ast.For, ast.While)):
                        depth = max(depth, 2)
                        for sub_sub in ast.walk(sub):
                            if sub_sub is not sub and isinstance(sub_sub, (ast.For, ast.While)):
                                depth = max(depth, 3)
                if depth > max_loop_depth:
                    max_loop_depth = depth

                # Check if while loop has halving condition (e.g. n //= 2)
                if isinstance(node, ast.While):
                    for sub in ast.walk(node):
                        if isinstance(sub, ast.AugAssign) and isinstance(sub.op, (ast.FloorDiv, ast.RShift)):
                            has_halving_loop = True

        # Check memory allocations inside loops (e.g. allocating lists/sets)
        allocates_in_loop = False
        if max_loop_depth > 0:
            for node in ast.walk(tree):
                if isinstance(node, (ast.For, ast.While)):
                    for sub in ast.walk(node):
                        if isinstance(sub, (ast.ListComp, ast.SetComp, ast.DictComp, ast.List, ast.Dict, ast.Set)):
                            allocates_in_loop = True
                            break

        if max_loop_depth >= 3:
            time_comp = "O(n^3)"
            space_comp = "O(n)" if allocates_in_loop else "O(1)"
            confidence = "medium"
            reasons = [
                f"Triple-nested loop structure detected (depth = {max_loop_depth}).",
                "Assuming loop boundaries iterate over input dimension N.",
            ]
        elif max_loop_depth == 2:
            time_comp = "O(n^2)"
            space_comp = "O(n)" if allocates_in_loop else "O(1)"
            confidence = "high"
            reasons = [
                "Two nested loops detected operating sequentially.",
                "Worst-case operation count scales quadratically with respect to input collection size.",
            ]
        elif max_loop_depth == 1:
            if has_halving_loop:
                time_comp = "O(log n)"
                space_comp = "O(1)"
                confidence = "medium"
                reasons = [
                    "Single loop with logarithmic decrement/halving operation discovered.",
                ]
            else:
                time_comp = "O(n)"
                space_comp = "O(n)" if allocates_in_loop else "O(1)"
                confidence = "high"
                reasons = [
                    "Single loop iterating over sequence of length N.",
                    "Direct linear scan through collection.",
                ]
        else:
            time_comp = "O(1)"
            space_comp = "O(1)"
            confidence = "high"
            reasons = [
                "No loops or recursive call trees detected in AST.",
                "Executes sequentially in bounded constant time.",
            ]

        uncertainty_factors = [
            "Loop bounds are dynamic and determined at runtime by input data size.",
            "Early break/return statements may lower average-case complexity.",
            "Library calls (e.g. .sort(), re.search(), min()) contain their own algorithmic complexities.",
        ]

        return ComplexityEstimate(
            time_complexity=time_comp,
            space_complexity=space_comp,
            confidence=confidence,
            reasons=reasons,
            uncertainty_factors=uncertainty_factors,
        )

    # -------------------------------------------------------------------------
    # Theoretical Scaling Simulation for Chart.js
    # -------------------------------------------------------------------------
    def _generate_benchmark_model(
        self, complexity: ComplexityEstimate, optimizations: List[OptimizationSuggestion]
    ) -> BenchmarkModel:
        """Generates interactive benchmark scaling data points for Chart.js rendering."""
        input_sizes = [10, 50, 100, 200, 400, 800, 1000]
        time_c = complexity.time_complexity

        has_optimizations = len(optimizations) > 0
        baseline_label = f"Current Implementation ({time_c})"

        # Determine optimized target curve
        if time_c == "O(2^n)":
            optimized_label = "With Memoization (O(n))"
            curve_type = "exponential_vs_linear"
            points = []
            for n in input_sizes:
                # Cap baseline for chart visualization readability
                base_ops = min(2**min(n, 20), 100000)
                opt_ops = n
                points.append(BenchmarkPoint(input_size=n, baseline_ops=base_ops, optimized_ops=opt_ops))
        elif time_c == "O(n^3)":
            optimized_label = "Flattened Structure (O(n log n))"
            curve_type = "cubic_vs_loglinear"
            points = []
            for n in input_sizes:
                base_ops = min(n**3, 500000)
                opt_ops = n * math.log2(max(n, 2))
                points.append(BenchmarkPoint(input_size=n, baseline_ops=base_ops, optimized_ops=round(opt_ops, 1)))
        elif time_c == "O(n^2)":
            optimized_label = "Hash Map / Set Indexing (O(n))"
            curve_type = "quadratic_vs_linear"
            points = []
            for n in input_sizes:
                base_ops = n**2
                opt_ops = n * 2  # O(n) with constant factor
                points.append(BenchmarkPoint(input_size=n, baseline_ops=base_ops, optimized_ops=opt_ops))
        elif time_c == "O(n)":
            optimized_label = "Optimized Iteration (O(n))"
            curve_type = "linear_scaling"
            points = []
            for n in input_sizes:
                base_ops = n * 3.5  # unoptimized python loop with lookups
                opt_ops = n * 1.2  # list comp / vectorized
                points.append(BenchmarkPoint(input_size=n, baseline_ops=round(base_ops, 1), optimized_ops=round(opt_ops, 1)))
        else:
            optimized_label = "Constant Time Execution (O(1))"
            curve_type = "constant_scaling"
            points = []
            for n in input_sizes:
                points.append(BenchmarkPoint(input_size=n, baseline_ops=1.0, optimized_ops=1.0))

        return BenchmarkModel(
            available=True,
            curve_type=curve_type,
            baseline_label=baseline_label,
            optimized_label=optimized_label,
            data_points=points,
        )
