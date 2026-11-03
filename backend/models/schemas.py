"""Pydantic schemas for UMCAO Code Analyzer & Optimizer."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    code: str = Field(..., description="Source code to analyze")
    language: str = Field(default="python", description="Programming language of the code")
    options: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Optional analysis parameters")


class CodePattern(BaseModel):
    id: str
    title: str
    severity: str = Field(..., description="'high' | 'medium' | 'low' | 'info'")
    category: str = Field(..., description="'complexity' | 'performance' | 'idiom' | 'best_practice'")
    line: Optional[int] = None
    column: Optional[int] = None
    snippet: Optional[str] = None
    explanation: str
    suggestion: str


class OptimizationSuggestion(BaseModel):
    id: str
    title: str
    category: str
    impact: str = Field(..., description="'high' | 'medium' | 'low'")
    confidence: str = Field(..., description="'high' | 'medium' | 'low'")
    explanation: str
    original_code: str
    optimized_code: str
    diff: Optional[str] = None
    theoretical_benefit: str


class ComplexityEstimate(BaseModel):
    time_complexity: str = Field(..., description="Estimated Big-O time complexity, e.g., O(1), O(n), O(n^2)")
    space_complexity: str = Field(..., description="Estimated Big-O space complexity, e.g., O(1), O(n)")
    confidence: str = Field(..., description="'high' | 'medium' | 'low'")
    reasons: List[str] = Field(default_factory=list)
    uncertainty_factors: List[str] = Field(default_factory=list)
    disclaimer: str = (
        "Complexity estimation is statically derived from structural AST cues (loop depth, recursion, allocations). "
        "Dynamic runtime values, early loop breaks, and built-in library complexity may alter actual execution."
    )


class ASTMetrics(BaseModel):
    total_nodes: int
    functions_count: int
    classes_count: int
    loops_count: int
    branches_count: int
    max_nesting_depth: int
    lines_of_code: int
    comment_lines: int


class BenchmarkPoint(BaseModel):
    input_size: int
    baseline_ops: float
    optimized_ops: float


class BenchmarkModel(BaseModel):
    available: bool = True
    curve_type: str = "theoretical_scaling"
    baseline_label: str = "Current Implementation"
    optimized_label: str = "Optimized Suggestion"
    data_points: List[BenchmarkPoint] = Field(default_factory=list)
    disclaimer: str = (
        "Chart illustrates theoretical computational scaling across varying input sizes (N) based on AST complexity analysis. "
        "It does not represent server-side execution of user code."
    )


class SyntaxErrorInfo(BaseModel):
    has_error: bool = False
    message: Optional[str] = None
    line: Optional[int] = None
    column: Optional[int] = None
    text: Optional[str] = None
    friendly_explanation: Optional[str] = None


class UnsupportedLanguageInfo(BaseModel):
    language: str
    display_name: str
    status: str = "in_development"
    planned_engine: str
    description: str
    features_in_progress: List[str]


class AnalyzeResponse(BaseModel):
    language: str
    supported: bool
    status: str = Field(..., description="'success' | 'syntax_error' | 'unsupported_language' | 'error'")
    message: str
    timestamp: str
    syntax_error: Optional[SyntaxErrorInfo] = None
    complexity: Optional[ComplexityEstimate] = None
    patterns: List[CodePattern] = Field(default_factory=list)
    optimizations: List[OptimizationSuggestion] = Field(default_factory=list)
    ast_metrics: Optional[ASTMetrics] = None
    benchmark_model: Optional[BenchmarkModel] = None
    roadmap_info: Optional[UnsupportedLanguageInfo] = None


class ExplanationSections(BaseModel):
    code_overview: str = Field(default="", description="Short summary of the program")
    purpose: str = Field(default="", description="What problem does the code solve?")
    line_by_line: str = Field(default="", description="Explain important statements in order")
    variables_and_functions: str = Field(default="", description="Explain their purpose")
    logic_and_workflow: str = Field(default="", description="Explain how the program executes")
    algorithm: str = Field(default="", description="Identify and explain the algorithm, if applicable")
    example_input_output: str = Field(default="", description="Give a suitable example and explain it")
    time_complexity: str = Field(default="", description="Give Big-O notation only when justified")
    space_complexity: str = Field(default="", description="Give Big-O notation only when justified")
    possible_improvements: str = Field(default="", description="Suggest improvements with reasons")
    learning_summary: str = Field(default="", description="List the important concepts learned")


class AIExplainRequest(BaseModel):
    code: str = Field(..., description="Source code to explain")
    language: str = Field(default="python", description="Source code language: python, c, cpp, java, javascript")
    mode: str = Field(default="detailed", description="'simple' | 'line_by_line' | 'detailed' | 'algorithm' | 'interview' | 'optimization'")
    explanation_language: str = Field(default="english", description="'english' | 'gujarati' | 'hindi'")


class AIExplainResponse(BaseModel):
    success: bool
    language: str
    mode: str
    explanation_language: str
    markdown: str
    sections: Optional[ExplanationSections] = None
    model_used: str
    timestamp: str
    error: Optional[str] = None


class ChatMessage(BaseModel):
    role: str = Field(..., description="'user' | 'model' | 'assistant'")
    content: str


class AIChatRequest(BaseModel):
    code: str = Field(..., description="Active source code context")
    language: str = Field(default="python", description="Programming language of code")
    explanation_language: str = Field(default="english", description="Target explanation language: english, gujarati, hindi")
    message: str = Field(..., description="User follow-up question")
    history: List[ChatMessage] = Field(default_factory=list, description="Prior conversation turns")


class AIChatResponse(BaseModel):
    success: bool
    reply: str
    model_used: str
    timestamp: str
    error: Optional[str] = None


# ============================================================================
# Compilation & Sandboxed Code Execution Schemas
# ============================================================================

class CodeValidateRequest(BaseModel):
    code: str = Field(..., description="Source code to validate")
    language: str = Field(default="python", description="Language: python, c, cpp, java, javascript")


class CodeValidateResponse(BaseModel):
    valid: bool
    language: str
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    line: Optional[int] = None
    column: Optional[int] = None
    details: Optional[str] = None


class CodeCompileRequest(BaseModel):
    code: str = Field(..., description="Source code to compile")
    language: str = Field(..., description="Language: c, cpp, java")


class CodeCompileResponse(BaseModel):
    success: bool
    language: str
    status: str  # "compilation_successful" | "compilation_failed" | "tool_not_installed"
    stdout: str = ""
    stderr: str = ""
    error_message: Optional[str] = None
    line: Optional[int] = None
    column: Optional[int] = None
    compilation_time: float = 0.0


class CodeExecuteRequest(BaseModel):
    code: str = Field(..., description="Source code to execute")
    language: str = Field(default="python", description="Language: python, c, cpp, java, javascript")
    stdin_input: Optional[str] = Field(default="", description="Simulated standard input (stdin)")


class CodeExecuteResponse(BaseModel):
    success: bool
    language: str
    status: str  # "execution_successful" | "compilation_failed" | "runtime_error" | "execution_timeout" | "syntax_error" | "tool_not_installed"
    stdout: str = ""
    stderr: str = ""
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    line: Optional[int] = None
    column: Optional[int] = None
    execution_time: float = 0.0  # Execution time in seconds
    exit_code: int = 0


class AnalyzeAndRunRequest(BaseModel):
    code: str = Field(..., description="Source code to analyze and run")
    language: str = Field(default="python", description="Language: python, c, cpp, java, javascript")
    stdin_input: Optional[str] = Field(default="", description="Standard input for the program")
    include_ast: bool = Field(default=True, description="Whether to also run static AST analysis")


class AnalyzeAndRunResponse(BaseModel):
    success: bool
    language: str
    status: str
    stdout: str = ""
    stderr: str = ""
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    line: Optional[int] = None
    column: Optional[int] = None
    execution_time: float = 0.0
    exit_code: int = 0
    ast_analysis: Optional[AnalyzeResponse] = None


class ExplainErrorRequest(BaseModel):
    code: str = Field(..., description="Submitted source code")
    language: str = Field(default="python", description="Programming language")
    error_message: str = Field(..., description="Error message from compiler or runtime")
    error_type: Optional[str] = Field(default=None, description="e.g. SyntaxError, CompilationError, RuntimeError")
    line: Optional[int] = Field(default=None, description="Line number of error")
    explanation_language: str = Field(default="english", description="Target explanation language: english, gujarati, hindi")


class ExplainErrorResponse(BaseModel):
    success: bool
    explanation: str
    suggested_fix: Optional[str] = None
    corrected_code: Optional[str] = None
    model_used: str = ""
    timestamp: str = ""
    error: Optional[str] = None


