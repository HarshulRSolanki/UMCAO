"""Sandboxed Compilation and Code Execution Service for UMCAO.

Supports:
- Python (syntax validation via AST, execution via Python 3.12 subprocess)
- JavaScript (syntax validation via Node.js --check, execution via Node.js)
- C (compilation via GCC, execution of compiled binary)
- C++ (compilation via G++, execution of compiled binary)
- Java (compilation via javac, execution via java)

Security Safeguards:
- Isolated temporary directories with guaranteed clean-up.
- Strict process execution timeouts (default: 5.0 seconds) to prevent infinite loops.
- Sanitized environment stripping all API keys, host secrets, and credentials.
- Output buffer caps (max 50,000 characters) to prevent memory exhaustion from runaway print loops.
- Clear tool availability detection with actionable error messages when a compiler is missing.
"""

import sys
import os
import re
import time
import shutil
import tempfile
import subprocess
import ast
from typing import Dict, Any, Optional, Tuple

EXECUTION_TIMEOUT_SECONDS = 5.0
MAX_OUTPUT_CHARS = 50000

# Safe environment variables permitted for subprocess execution
SAFE_ENV_VARS = [
    "PATH",
    "SYSTEMROOT",
    "SYSTEMDRIVE",
    "COMSPEC",
    "PATHEXT",
    "TEMP",
    "TMP",
    "TMPDIR",
    "LANG",
    "LC_ALL",
    "NODE_PATH",
    "PYTHONPATH",
    "JAVA_HOME",
]


def _get_sanitized_env() -> Dict[str, str]:
    """Builds a stripped environment dictionary containing only essential system paths."""
    clean_env: Dict[str, str] = {}
    for var in SAFE_ENV_VARS:
        val = os.environ.get(var)
        if val is not None:
            clean_env[var] = val
    # Ensure UTF-8 output encoding for Python subprocesses
    clean_env["PYTHONIOENCODING"] = "utf-8"
    clean_env["PYTHONUNBUFFERED"] = "1"
    return clean_env


def check_compiler_availability(language: str) -> Tuple[bool, str, Optional[str]]:
    """Checks if the required compiler or interpreter is available in PATH.
    
    Returns:
        (is_available, tool_name_or_message, executable_path)
    """
    lang = language.strip().lower()

    if lang in ("python", "py"):
        return True, "Python", sys.executable

    if lang in ("javascript", "js"):
        node_path = shutil.which("node")
        if node_path:
            return True, "Node.js", node_path
        return False, "Node.js runtime ('node') is not installed or not in system PATH.", None

    if lang == "c":
        gcc_path = shutil.which("gcc") or shutil.which("clang")
        if gcc_path:
            return True, "GCC/Clang", gcc_path
        return False, "C compiler (GCC or Clang) is not installed on this system. Please install MinGW, GCC, or Clang to compile and run C code.", None

    if lang in ("cpp", "c++", "cplusplus"):
        gpp_path = shutil.which("g++") or shutil.which("clang++")
        if gpp_path:
            return True, "G++/Clang++", gpp_path
        return False, "C++ compiler (G++ or Clang++) is not installed on this system. Please install MinGW (G++) to compile and run C++ code.", None

    if lang == "java":
        javac_path = shutil.which("javac")
        java_path = shutil.which("java")
        if javac_path and java_path:
            return True, "JDK (javac/java)", javac_path
        if not javac_path:
            return False, "Java compiler ('javac') is not installed on this system. Please install OpenJDK / Oracle JDK to compile Java code.", None
        return False, "Java runtime ('java') is not installed or not in PATH.", None

    return False, f"Unsupported language: '{language}'", None


def validate_code_syntax(code: str, language: str) -> Dict[str, Any]:
    """Checks source code for syntax and parsing errors without executing it."""
    lang = language.strip().lower()
    clean_code = code.strip() if code else ""

    if not clean_code:
        return {
            "valid": False,
            "language": language,
            "error_type": "EmptyCodeError",
            "error_message": "No code provided to validate.",
            "line": None,
            "column": None,
            "details": None,
        }

    # 1. Python Syntax Validation via AST
    if lang in ("python", "py"):
        try:
            ast.parse(clean_code)
            return {
                "valid": True,
                "language": "python",
                "error_type": None,
                "error_message": None,
                "line": None,
                "column": None,
                "details": "Syntax is valid Python 3.12 AST.",
            }
        except SyntaxError as e:
            return {
                "valid": False,
                "language": "python",
                "error_type": "SyntaxError",
                "error_message": e.msg or "Invalid Python syntax",
                "line": e.lineno,
                "column": e.offset,
                "details": f"SyntaxError at line {e.lineno}, column {e.offset}: {e.msg}",
            }

    # 2. JavaScript Syntax Validation via Node.js
    if lang in ("javascript", "js"):
        avail, tool_name, node_exe = check_compiler_availability("javascript")
        if not avail or not node_exe:
            return {
                "valid": False,
                "language": "javascript",
                "error_type": "CompilerNotInstalled",
                "error_message": tool_name,
                "line": None,
                "column": None,
                "details": tool_name,
            }

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file = os.path.join(temp_dir, "script.js")
            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(clean_code)

            try:
                proc = subprocess.run(
                    [node_exe, "--check", temp_file],
                    capture_output=True,
                    text=True,
                    timeout=5.0,
                    env=_get_sanitized_env(),
                )
                if proc.returncode == 0:
                    return {
                        "valid": True,
                        "language": "javascript",
                        "error_type": None,
                        "error_message": None,
                        "line": None,
                        "column": None,
                        "details": "Syntax is valid ECMAScript (Node.js syntax check passed).",
                    }
                else:
                    stderr = proc.stderr
                    line_no, col_no = _parse_node_error_line(stderr)
                    err_msg = _extract_first_error_line(stderr)
                    return {
                        "valid": False,
                        "language": "javascript",
                        "error_type": "SyntaxError",
                        "error_message": err_msg or "JavaScript syntax error",
                        "line": line_no,
                        "column": col_no,
                        "details": stderr.strip(),
                    }
            except Exception as ex:
                return {
                    "valid": False,
                    "language": "javascript",
                    "error_type": "ValidationError",
                    "error_message": str(ex),
                    "line": None,
                    "column": None,
                    "details": str(ex),
                }

    # 3. C, C++, Java Syntax Validation
    avail, tool_name, exe_path = check_compiler_availability(lang)
    if not avail:
        return {
            "valid": False,
            "language": language,
            "error_type": "CompilerNotInstalled",
            "error_message": tool_name,
            "line": None,
            "column": None,
            "details": tool_name,
        }

    # If compiler is installed, compilation acts as syntax check
    compile_res = compile_code(clean_code, lang)
    return {
        "valid": compile_res["success"],
        "language": language,
        "error_type": "CompilationError" if not compile_res["success"] else None,
        "error_message": compile_res.get("error_message"),
        "line": compile_res.get("line"),
        "column": compile_res.get("column"),
        "details": compile_res.get("stderr") or compile_res.get("stdout"),
    }


def compile_code(code: str, language: str) -> Dict[str, Any]:
    """Compiles C, C++, or Java code into an executable or bytecode."""
    lang = language.strip().lower()
    avail, tool_name, exe_path = check_compiler_availability(lang)

    if not avail or not exe_path:
        return {
            "success": False,
            "language": language,
            "status": "tool_not_installed",
            "stdout": "",
            "stderr": tool_name,
            "error_message": tool_name,
            "line": None,
            "column": None,
            "compilation_time": 0.0,
        }

    start_time = time.perf_counter()

    # Compile C
    if lang == "c":
        with tempfile.TemporaryDirectory() as temp_dir:
            src_file = os.path.join(temp_dir, "program.c")
            out_file = os.path.join(temp_dir, "program.exe" if os.name == "nt" else "program")
            with open(src_file, "w", encoding="utf-8") as f:
                f.write(code)

            cmd = [exe_path, "-O2", "-Wall", src_file, "-o", out_file]
            try:
                proc = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=8.0,
                    env=_get_sanitized_env(),
                )
                comp_time = time.perf_counter() - start_time
                if proc.returncode == 0:
                    return {
                        "success": True,
                        "language": "c",
                        "status": "compilation_successful",
                        "stdout": proc.stdout,
                        "stderr": proc.stderr,
                        "error_message": None,
                        "line": None,
                        "column": None,
                        "compilation_time": round(comp_time, 4),
                    }
                else:
                    line, col, msg = _parse_gcc_error(proc.stderr)
                    return {
                        "success": False,
                        "language": "c",
                        "status": "compilation_failed",
                        "stdout": proc.stdout,
                        "stderr": proc.stderr,
                        "error_message": msg or "Compilation failed.",
                        "line": line,
                        "column": col,
                        "compilation_time": round(comp_time, 4),
                    }
            except subprocess.TimeoutExpired:
                return {
                    "success": False,
                    "language": "c",
                    "status": "compilation_failed",
                    "stdout": "",
                    "stderr": "Compilation timed out after 8.0 seconds.",
                    "error_message": "Compilation timed out.",
                    "line": None,
                    "column": None,
                    "compilation_time": 8.0,
                }

    # Compile C++
    if lang in ("cpp", "c++", "cplusplus"):
        with tempfile.TemporaryDirectory() as temp_dir:
            src_file = os.path.join(temp_dir, "program.cpp")
            out_file = os.path.join(temp_dir, "program.exe" if os.name == "nt" else "program")
            with open(src_file, "w", encoding="utf-8") as f:
                f.write(code)

            cmd = [exe_path, "-O2", "-Wall", "-std=c++17", src_file, "-o", out_file]
            try:
                proc = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=8.0,
                    env=_get_sanitized_env(),
                )
                comp_time = time.perf_counter() - start_time
                if proc.returncode == 0:
                    return {
                        "success": True,
                        "language": "cpp",
                        "status": "compilation_successful",
                        "stdout": proc.stdout,
                        "stderr": proc.stderr,
                        "error_message": None,
                        "line": None,
                        "column": None,
                        "compilation_time": round(comp_time, 4),
                    }
                else:
                    line, col, msg = _parse_gcc_error(proc.stderr)
                    return {
                        "success": False,
                        "language": "cpp",
                        "status": "compilation_failed",
                        "stdout": proc.stdout,
                        "stderr": proc.stderr,
                        "error_message": msg or "Compilation failed.",
                        "line": line,
                        "column": col,
                        "compilation_time": round(comp_time, 4),
                    }
            except subprocess.TimeoutExpired:
                return {
                    "success": False,
                    "language": "cpp",
                    "status": "compilation_failed",
                    "stdout": "",
                    "stderr": "Compilation timed out after 8.0 seconds.",
                    "error_message": "Compilation timed out.",
                    "line": None,
                    "column": None,
                    "compilation_time": 8.0,
                }

    # Compile Java
    if lang == "java":
        class_name = _extract_java_class_name(code) or "Main"
        with tempfile.TemporaryDirectory() as temp_dir:
            src_file = os.path.join(temp_dir, f"{class_name}.java")
            with open(src_file, "w", encoding="utf-8") as f:
                f.write(code)

            cmd = [exe_path, src_file]
            try:
                proc = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=10.0,
                    env=_get_sanitized_env(),
                )
                comp_time = time.perf_counter() - start_time
                if proc.returncode == 0:
                    return {
                        "success": True,
                        "language": "java",
                        "status": "compilation_successful",
                        "stdout": proc.stdout,
                        "stderr": proc.stderr,
                        "error_message": None,
                        "line": None,
                        "column": None,
                        "compilation_time": round(comp_time, 4),
                    }
                else:
                    line, col, msg = _parse_java_error(proc.stderr)
                    return {
                        "success": False,
                        "language": "java",
                        "status": "compilation_failed",
                        "stdout": proc.stdout,
                        "stderr": proc.stderr,
                        "error_message": msg or "Java compilation failed.",
                        "line": line,
                        "column": col,
                        "compilation_time": round(comp_time, 4),
                    }
            except subprocess.TimeoutExpired:
                return {
                    "success": False,
                    "language": "java",
                    "status": "compilation_failed",
                    "stdout": "",
                    "stderr": "Java compilation timed out.",
                    "error_message": "Compilation timed out.",
                    "line": None,
                    "column": None,
                    "compilation_time": 10.0,
                }

    return {
        "success": False,
        "language": language,
        "status": "compilation_failed",
        "stdout": "",
        "stderr": f"Language '{language}' does not require compilation or is unsupported.",
        "error_message": "Language does not require compilation.",
        "line": None,
        "column": None,
        "compilation_time": 0.0,
    }


def execute_code_sandboxed(
    code: str,
    language: str,
    stdin_input: str = "",
) -> Dict[str, Any]:
    """Executes validated code in an isolated subprocess sandbox.
    
    Returns structured results including stdout, stderr, execution time, and error location.
    """
    lang = language.strip().lower()
    clean_code = code.strip() if code else ""

    if not clean_code:
        return {
            "success": False,
            "language": language,
            "status": "syntax_error",
            "stdout": "",
            "stderr": "No code provided to execute.",
            "error_type": "EmptyCodeError",
            "error_message": "Please write or paste code to run.",
            "line": None,
            "column": None,
            "execution_time": 0.0,
            "exit_code": 1,
        }

    avail, tool_name, exe_path = check_compiler_availability(lang)
    if not avail:
        return {
            "success": False,
            "language": language,
            "status": "tool_not_installed",
            "stdout": "",
            "stderr": tool_name,
            "error_type": "CompilerNotInstalled",
            "error_message": tool_name,
            "line": None,
            "column": None,
            "execution_time": 0.0,
            "exit_code": 1,
        }

    # Execute Python
    if lang in ("python", "py"):
        # First check syntax
        try:
            ast.parse(clean_code)
        except SyntaxError as syn_err:
            return {
                "success": False,
                "language": "python",
                "status": "syntax_error",
                "stdout": "",
                "stderr": f"SyntaxError: {syn_err.msg} (line {syn_err.lineno})",
                "error_type": "SyntaxError",
                "error_message": syn_err.msg,
                "line": syn_err.lineno,
                "column": syn_err.offset,
                "execution_time": 0.0,
                "exit_code": 1,
            }

        with tempfile.TemporaryDirectory() as temp_dir:
            script_path = os.path.join(temp_dir, "run.py")
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(clean_code)

            cmd = [sys.executable, "-u", script_path]
            return _run_subprocess_safe(cmd, cwd=temp_dir, stdin_input=stdin_input, language="python")

    # Execute JavaScript (Node.js)
    if lang in ("javascript", "js"):
        with tempfile.TemporaryDirectory() as temp_dir:
            script_path = os.path.join(temp_dir, "run.js")
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(clean_code)

            cmd = [exe_path, script_path]
            return _run_subprocess_safe(cmd, cwd=temp_dir, stdin_input=stdin_input, language="javascript")

    # Compile and Execute C
    if lang == "c":
        with tempfile.TemporaryDirectory() as temp_dir:
            src_file = os.path.join(temp_dir, "prog.c")
            exe_file = os.path.join(temp_dir, "prog.exe" if os.name == "nt" else "prog")
            with open(src_file, "w", encoding="utf-8") as f:
                f.write(clean_code)

            # Compile
            comp_proc = subprocess.run(
                [exe_path, "-O2", "-Wall", src_file, "-o", exe_file],
                capture_output=True,
                text=True,
                timeout=8.0,
                env=_get_sanitized_env(),
                cwd=temp_dir,
            )
            if comp_proc.returncode != 0:
                line, col, msg = _parse_gcc_error(comp_proc.stderr)
                return {
                    "success": False,
                    "language": "c",
                    "status": "compilation_failed",
                    "stdout": comp_proc.stdout,
                    "stderr": comp_proc.stderr,
                    "error_type": "CompilationError",
                    "error_message": msg or "C compilation failed.",
                    "line": line,
                    "column": col,
                    "execution_time": 0.0,
                    "exit_code": comp_proc.returncode,
                }

            # Run binary
            return _run_subprocess_safe([exe_file], cwd=temp_dir, stdin_input=stdin_input, language="c")

    # Compile and Execute C++
    if lang in ("cpp", "c++", "cplusplus"):
        with tempfile.TemporaryDirectory() as temp_dir:
            src_file = os.path.join(temp_dir, "prog.cpp")
            exe_file = os.path.join(temp_dir, "prog.exe" if os.name == "nt" else "prog")
            with open(src_file, "w", encoding="utf-8") as f:
                f.write(clean_code)

            # Compile
            comp_proc = subprocess.run(
                [exe_path, "-O2", "-Wall", "-std=c++17", src_file, "-o", exe_file],
                capture_output=True,
                text=True,
                timeout=8.0,
                env=_get_sanitized_env(),
                cwd=temp_dir,
            )
            if comp_proc.returncode != 0:
                line, col, msg = _parse_gcc_error(comp_proc.stderr)
                return {
                    "success": False,
                    "language": "cpp",
                    "status": "compilation_failed",
                    "stdout": comp_proc.stdout,
                    "stderr": comp_proc.stderr,
                    "error_type": "CompilationError",
                    "error_message": msg or "C++ compilation failed.",
                    "line": line,
                    "column": col,
                    "execution_time": 0.0,
                    "exit_code": comp_proc.returncode,
                }

            # Run binary
            return _run_subprocess_safe([exe_file], cwd=temp_dir, stdin_input=stdin_input, language="cpp")

    # Compile and Execute Java
    if lang == "java":
        class_name = _extract_java_class_name(clean_code) or "Main"
        java_run = shutil.which("java")
        if not java_run:
            return {
                "success": False,
                "language": "java",
                "status": "tool_not_installed",
                "stdout": "",
                "stderr": "Java runtime ('java') is not installed in PATH.",
                "error_type": "CompilerNotInstalled",
                "error_message": "Java runtime is not installed.",
                "line": None,
                "column": None,
                "execution_time": 0.0,
                "exit_code": 1,
            }

        with tempfile.TemporaryDirectory() as temp_dir:
            src_file = os.path.join(temp_dir, f"{class_name}.java")
            with open(src_file, "w", encoding="utf-8") as f:
                f.write(clean_code)

            # Compile
            comp_proc = subprocess.run(
                [exe_path, src_file],
                capture_output=True,
                text=True,
                timeout=10.0,
                env=_get_sanitized_env(),
                cwd=temp_dir,
            )
            if comp_proc.returncode != 0:
                line, col, msg = _parse_java_error(comp_proc.stderr)
                return {
                    "success": False,
                    "language": "java",
                    "status": "compilation_failed",
                    "stdout": comp_proc.stdout,
                    "stderr": comp_proc.stderr,
                    "error_type": "CompilationError",
                    "error_message": msg or "Java compilation failed.",
                    "line": line,
                    "column": col,
                    "execution_time": 0.0,
                    "exit_code": comp_proc.returncode,
                }

            # Run Java class
            return _run_subprocess_safe(
                [java_run, "-cp", temp_dir, class_name],
                cwd=temp_dir,
                stdin_input=stdin_input,
                language="java",
            )

    return {
        "success": False,
        "language": language,
        "status": "runtime_error",
        "stdout": "",
        "stderr": f"Execution for language '{language}' is not supported.",
        "error_type": "UnsupportedLanguage",
        "error_message": f"Language '{language}' execution is not supported.",
        "line": None,
        "column": None,
        "execution_time": 0.0,
        "exit_code": 1,
    }


def _run_subprocess_safe(
    cmd: list,
    cwd: str,
    stdin_input: str,
    language: str,
) -> Dict[str, Any]:
    """Helper executing subprocess with strict timeout, sanitized env, and error extraction."""
    start_time = time.perf_counter()
    stdin_bytes = stdin_input.encode("utf-8") if stdin_input else None

    try:
        proc = subprocess.run(
            cmd,
            input=stdin_bytes,
            capture_output=True,
            timeout=EXECUTION_TIMEOUT_SECONDS,
            cwd=cwd,
            env=_get_sanitized_env(),
        )
        exec_time = time.perf_counter() - start_time

        stdout = proc.stdout.decode("utf-8", errors="replace")[:MAX_OUTPUT_CHARS]
        stderr = proc.stderr.decode("utf-8", errors="replace")[:MAX_OUTPUT_CHARS]

        if proc.returncode == 0:
            return {
                "success": True,
                "language": language,
                "status": "execution_successful",
                "stdout": stdout,
                "stderr": stderr,
                "error_type": None,
                "error_message": None,
                "line": None,
                "column": None,
                "execution_time": round(exec_time, 4),
                "exit_code": 0,
            }
        else:
            # Runtime error detected
            line, col, err_type, err_msg = _extract_runtime_error_info(stderr, language)
            return {
                "success": False,
                "language": language,
                "status": "runtime_error",
                "stdout": stdout,
                "stderr": stderr,
                "error_type": err_type or "RuntimeError",
                "error_message": err_msg or f"Process exited with code {proc.returncode}",
                "line": line,
                "column": col,
                "execution_time": round(exec_time, 4),
                "exit_code": proc.returncode,
            }

    except subprocess.TimeoutExpired as timeout_exc:
        exec_time = time.perf_counter() - start_time
        stdout = (timeout_exc.stdout or b"").decode("utf-8", errors="replace")[:MAX_OUTPUT_CHARS]
        stderr = (timeout_exc.stderr or b"").decode("utf-8", errors="replace")[:MAX_OUTPUT_CHARS]
        return {
            "success": False,
            "language": language,
            "status": "execution_timeout",
            "stdout": stdout,
            "stderr": stderr,
            "error_type": "TimeoutExpired",
            "error_message": f"Execution timed out after {EXECUTION_TIMEOUT_SECONDS}s. The program may contain an infinite loop or is awaiting input.",
            "line": None,
            "column": None,
            "execution_time": round(exec_time, 4),
            "exit_code": 124,
        }
    except Exception as ex:
        exec_time = time.perf_counter() - start_time
        return {
            "success": False,
            "language": language,
            "status": "runtime_error",
            "stdout": "",
            "stderr": str(ex),
            "error_type": ex.__class__.__name__,
            "error_message": str(ex),
            "line": None,
            "column": None,
            "execution_time": round(exec_time, 4),
            "exit_code": 1,
        }


# ============================================================================
# Error Parsing Utilities
# ============================================================================

def _parse_gcc_error(stderr_text: str) -> Tuple[Optional[int], Optional[int], Optional[str]]:
    """Extracts line number, column, and message from GCC/Clang compiler stderr."""
    match = re.search(r":(\d+):(\d+):\s*(?:fatal\s+)?error:\s*(.*)", stderr_text)
    if match:
        try:
            return int(match.group(1)), int(match.group(2)), match.group(3).strip()
        except (ValueError, IndexError):
            pass
    # Fallback to line only
    match2 = re.search(r":(\d+):\s*(?:fatal\s+)?error:\s*(.*)", stderr_text)
    if match2:
        try:
            return int(match2.group(1)), None, match2.group(2).strip()
        except (ValueError, IndexError):
            pass
    return None, None, _extract_first_error_line(stderr_text)


def _parse_java_error(stderr_text: str) -> Tuple[Optional[int], Optional[int], Optional[str]]:
    """Extracts line number, column, and message from javac stderr."""
    match = re.search(r"\.java:(\d+):\s*error:\s*(.*)", stderr_text)
    if match:
        try:
            line = int(match.group(1))
            msg = match.group(2).strip()
            return line, None, msg
        except (ValueError, IndexError):
            pass
    return None, None, _extract_first_error_line(stderr_text)


def _parse_node_error_line(stderr_text: str) -> Tuple[Optional[int], Optional[int]]:
    """Extracts line and column from Node.js error trace."""
    match = re.search(r":(\d+)\n.*?\n\s*(\^)", stderr_text)
    if match:
        try:
            line = int(match.group(1))
            col = len(match.group(2))
            return line, col
        except Exception:
            pass
    match2 = re.search(r":(\d+):(\d+)", stderr_text)
    if match2:
        try:
            return int(match2.group(1)), int(match2.group(2))
        except Exception:
            pass
    return None, None


def _extract_first_error_line(text: str) -> Optional[str]:
    """Finds the first non-empty line containing error/exception keywords."""
    for line in text.splitlines():
        line_clean = line.strip()
        if not line_clean:
            continue
        if any(kw in line_clean.lower() for kw in ("error", "exception", "failed", "cannot find", "undefined")):
            return line_clean
    return text.strip().splitlines()[0] if text.strip() else None


def _extract_runtime_error_info(
    stderr_text: str,
    language: str,
) -> Tuple[Optional[int], Optional[int], Optional[str], Optional[str]]:
    """Extracts runtime exception name, message, and line number from traceback."""
    line = None
    col = None
    err_type = "RuntimeError"
    err_msg = _extract_first_error_line(stderr_text)

    if language == "python":
        # Extract traceback line
        lines_match = re.findall(r'File ".*?", line (\d+)', stderr_text)
        if lines_match:
            try:
                line = int(lines_match[-1])
            except ValueError:
                pass
        # Extract exception class and message (e.g. ZeroDivisionError: division by zero)
        ex_match = re.search(r'([A-Za-z]+Error|[A-Za-z]+Exception):\s*(.*)', stderr_text)
        if ex_match:
            err_type = ex_match.group(1)
            err_msg = f"{ex_match.group(1)}: {ex_match.group(2)}"

    elif language in ("javascript", "js"):
        line, col = _parse_node_error_line(stderr_text)
        ex_match = re.search(r'([A-Za-z]+Error):\s*(.*)', stderr_text)
        if ex_match:
            err_type = ex_match.group(1)
            err_msg = f"{ex_match.group(1)}: {ex_match.group(2)}"

    elif language in ("c", "cpp"):
        if "segmentation fault" in stderr_text.lower() or "sigsegv" in stderr_text.lower():
            err_type = "SegmentationFault"
            err_msg = "Segmentation Fault (Memory Access Violation / Null Pointer Dereference)"

    elif language == "java":
        ex_match = re.search(r'Exception in thread ".*?" ([a-zA-Z0-9_.]+Exception|[a-zA-Z0-9_.]+Error):\s*(.*)', stderr_text)
        if ex_match:
            err_type = ex_match.group(1).split(".")[-1]
            err_msg = f"{err_type}: {ex_match.group(2)}"
        line_match = re.search(r'\.java:(\d+)\)', stderr_text)
        if line_match:
            try:
                line = int(line_match.group(1))
            except ValueError:
                pass

    return line, col, err_type, err_msg


def _extract_java_class_name(code: str) -> Optional[str]:
    """Finds public class Name in Java source code."""
    match = re.search(r'public\s+class\s+([A-Za-z0-9_]+)', code)
    if match:
        return match.group(1)
    match_any = re.search(r'class\s+([A-Za-z0-9_]+)', code)
    if match_any:
        return match_any.group(1)
    return "Main"
