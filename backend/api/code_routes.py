"""Code Validation, Compilation, Execution, and Error Explanation Routes for UMCAO.

Endpoints:
- POST /api/code/validate
- POST /api/code/compile
- POST /api/code/execute
- POST /api/code/analyze-run
- POST /api/code/explain-error
"""

from fastapi import APIRouter, HTTPException, status
from models.schemas import (
    CodeValidateRequest,
    CodeValidateResponse,
    CodeCompileRequest,
    CodeCompileResponse,
    CodeExecuteRequest,
    CodeExecuteResponse,
    AnalyzeAndRunRequest,
    AnalyzeAndRunResponse,
    ExplainErrorRequest,
    ExplainErrorResponse,
)
from services.execution_service import (
    validate_code_syntax,
    compile_code,
    execute_code_sandboxed,
    check_compiler_availability,
)
from services.gemini_service import explain_error_with_gemini
from analyzers.registry import analyzer_registry

router = APIRouter(prefix="/api/code", tags=["Code Execution & Error Detection"])


@router.post("/validate", response_model=CodeValidateResponse)
def validate_code(request: CodeValidateRequest):
    """Validates source code syntax and structural correctness without executing it."""
    result = validate_code_syntax(request.code, request.language)
    return CodeValidateResponse(
        valid=result["valid"],
        language=result["language"],
        error_type=result.get("error_type"),
        error_message=result.get("error_message"),
        line=result.get("line"),
        column=result.get("column"),
        details=result.get("details"),
    )


@router.post("/compile", response_model=CodeCompileResponse)
def compile_code_endpoint(request: CodeCompileRequest):
    """Compiles code for compiled languages (C, C++, Java) and returns compiler diagnostics."""
    result = compile_code(request.code, request.language)
    return CodeCompileResponse(
        success=result["success"],
        language=result["language"],
        status=result["status"],
        stdout=result.get("stdout", ""),
        stderr=result.get("stderr", ""),
        error_message=result.get("error_message"),
        line=result.get("line"),
        column=result.get("column"),
        compilation_time=result.get("compilation_time", 0.0),
    )


@router.post("/execute", response_model=CodeExecuteResponse)
def execute_code_endpoint(request: CodeExecuteRequest):
    """Executes validated code inside a safe sandboxed subprocess environment."""
    result = execute_code_sandboxed(
        code=request.code,
        language=request.language,
        stdin_input=request.stdin_input or "",
    )
    return CodeExecuteResponse(
        success=result["success"],
        language=result["language"],
        status=result["status"],
        stdout=result.get("stdout", ""),
        stderr=result.get("stderr", ""),
        error_type=result.get("error_type"),
        error_message=result.get("error_message"),
        line=result.get("line"),
        column=result.get("column"),
        execution_time=result.get("execution_time", 0.0),
        exit_code=result.get("exit_code", 0),
    )


@router.post("/analyze-run", response_model=AnalyzeAndRunResponse)
def analyze_and_run(request: AnalyzeAndRunRequest):
    """Complete workflow: syntax validation -> compiler verification -> sandbox execution -> optional AST analysis.
    
    Guarantees:
    - Never executes if syntax or compilation errors occur.
    - Captures real stdout and stderr.
    - Identifies error line and column when available.
    - Reports clear tool status when compilers (GCC, javac) are not installed on the host.
    """
    lang = request.language.strip().lower()

    # Step 1: Validate Syntax
    val = validate_code_syntax(request.code, lang)
    if not val["valid"]:
        return AnalyzeAndRunResponse(
            success=False,
            language=lang,
            status="syntax_error" if val.get("error_type") != "CompilerNotInstalled" else "tool_not_installed",
            stdout="",
            stderr=val.get("details") or val.get("error_message") or "Syntax validation failed.",
            error_type=val.get("error_type") or "SyntaxError",
            error_message=val.get("error_message") or "Syntax validation failed.",
            line=val.get("line"),
            column=val.get("column"),
            execution_time=0.0,
            exit_code=1,
            ast_analysis=None,
        )

    # Step 2: Check compiler / interpreter availability
    avail, tool_msg, _ = check_compiler_availability(lang)
    if not avail:
        return AnalyzeAndRunResponse(
            success=False,
            language=lang,
            status="tool_not_installed",
            stdout="",
            stderr=tool_msg,
            error_type="CompilerNotInstalled",
            error_message=tool_msg,
            line=None,
            column=None,
            execution_time=0.0,
            exit_code=1,
            ast_analysis=None,
        )

    # Step 3: Compile if required (C, C++, Java)
    if lang in ("c", "cpp", "c++", "cplusplus", "java"):
        comp_res = compile_code(request.code, lang)
        if not comp_res["success"]:
            return AnalyzeAndRunResponse(
                success=False,
                language=lang,
                status=comp_res.get("status", "compilation_failed"),
                stdout=comp_res.get("stdout", ""),
                stderr=comp_res.get("stderr", ""),
                error_type="CompilationError",
                error_message=comp_res.get("error_message") or "Compilation failed.",
                line=comp_res.get("line"),
                column=comp_res.get("column"),
                execution_time=comp_res.get("compilation_time", 0.0),
                exit_code=1,
                ast_analysis=None,
            )

    # Step 4: Execute code inside isolated sandbox
    exec_res = execute_code_sandboxed(
        code=request.code,
        language=lang,
        stdin_input=request.stdin_input or "",
    )

    # Step 5: Optional static AST analysis
    ast_res = None
    if request.include_ast:
        analyzer = analyzer_registry.get_analyzer(lang)
        if analyzer:
            try:
                ast_res = analyzer.analyze(request.code)
            except Exception:
                ast_res = None

    return AnalyzeAndRunResponse(
        success=exec_res["success"],
        language=lang,
        status=exec_res["status"],
        stdout=exec_res.get("stdout", ""),
        stderr=exec_res.get("stderr", ""),
        error_type=exec_res.get("error_type"),
        error_message=exec_res.get("error_message"),
        line=exec_res.get("line"),
        column=exec_res.get("column"),
        execution_time=exec_res.get("execution_time", 0.0),
        exit_code=exec_res.get("exit_code", 0),
        ast_analysis=ast_res,
    )


@router.post("/explain-error", response_model=ExplainErrorResponse)
def explain_error_endpoint(request: ExplainErrorRequest):
    """Uses Gemini AI to explain why an error occurred and provide a corrected version of the code."""
    res = explain_error_with_gemini(
        code=request.code,
        language=request.language,
        error_message=request.error_message,
        error_type=request.error_type,
        line=request.line,
        explanation_language=request.explanation_language or "english",
    )
    if not res["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=res.get("error", "Error diagnosis failed."),
        )
    return res
