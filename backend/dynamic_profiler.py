"""Dynamic runtime execution & profiling engine for UMCAO.

Measures actual wall-clock execution time, peak memory allocation,
and standard output in an isolated subprocess with strict timeouts.
"""

import sys
import subprocess
import json
import tempfile
import os
from typing import Dict, Any


RUNNER_SCRIPT = """
import sys
import time
import tracemalloc
import io
import contextlib

def run_isolated():
    code_file = sys.argv[1]
    with open(code_file, 'r', encoding='utf-8') as f:
        code_text = f.read()

    # Capture stdout
    stdout_buf = io.StringIO()
    tracemalloc.start()
    start_time = time.perf_counter_ns()
    err_msg = None
    success = False

    try:
        with contextlib.redirect_stdout(stdout_buf):
            # Execute code in clean global dictionary
            exec_globals = {"__name__": "__main__"}
            exec(code_text, exec_globals)
        success = True
    except Exception as e:
        err_msg = f"{type(e).__name__}: {str(e)}"
    finally:
        end_time = time.perf_counter_ns()
        current_mem, peak_mem = tracemalloc.get_traced_memory()
        tracemalloc.stop()

    elapsed_ms = round((end_time - start_time) / 1_000_000, 3)
    peak_kb = round(peak_mem / 1024, 2)
    output = stdout_buf.getvalue()
    if len(output) > 2000:
        output = output[:2000] + "... (output truncated)"

    result = {
        "success": success,
        "runtime_ms": elapsed_ms,
        "peak_memory_kb": peak_kb,
        "stdout": output,
        "error": err_msg,
    }
    print("---UMCAO_PROFILE_START---")
    print(json.dumps(result))
    print("---UMCAO_PROFILE_END---")

if __name__ == '__main__':
    run_isolated()
"""


def profile_python_code(code: str, timeout_seconds: float = 3.0) -> Dict[str, Any]:
    """Safely runs code in a subprocess with time and memory tracking."""
    if not code or not code.strip():
        return {
            "enabled": False,
            "executed": False,
            "runtime_ms": 0.0,
            "peak_memory_kb": 0.0,
            "stdout": "",
            "error": "Empty code snippet provided.",
            "status": "skipped",
        }

    # Write code and runner script to temporary files
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as code_f:
        code_f.write(code)
        code_path = code_f.name

    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as runner_f:
        runner_f.write(RUNNER_SCRIPT)
        runner_path = runner_f.name

    python_executable = sys.executable

    try:
        proc = subprocess.run(
            [python_executable, runner_path, code_path],
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )

        stdout = proc.stdout or ""
        stderr = proc.stderr or ""

        if "---UMCAO_PROFILE_START---" in stdout:
            part = stdout.split("---UMCAO_PROFILE_START---")[1]
            json_str = part.split("---UMCAO_PROFILE_END---")[0].strip()
            data = json.loads(json_str)

            return {
                "enabled": True,
                "executed": True,
                "runtime_ms": data.get("runtime_ms", 0.0),
                "peak_memory_kb": data.get("peak_memory_kb", 0.0),
                "stdout": data.get("stdout", ""),
                "error": data.get("error"),
                "status": "completed" if data.get("success") else "runtime_error",
            }
        else:
            return {
                "enabled": True,
                "executed": False,
                "runtime_ms": 0.0,
                "peak_memory_kb": 0.0,
                "stdout": "",
                "error": stderr.strip() or "Process terminated without profile output.",
                "status": "failed",
            }
    except subprocess.TimeoutExpired:
        return {
            "enabled": True,
            "executed": False,
            "runtime_ms": timeout_seconds * 1000,
            "peak_memory_kb": 0.0,
            "stdout": "",
            "error": f"Execution timed out ({timeout_seconds}s limit exceeded). Possible infinite loop or slow recursion.",
            "status": "timeout",
        }
    except Exception as e:
        return {
            "enabled": True,
            "executed": False,
            "runtime_ms": 0.0,
            "peak_memory_kb": 0.0,
            "stdout": "",
            "error": str(e),
            "status": "error",
        }
    finally:
        try:
            if os.path.exists(code_path):
                os.remove(code_path)
            if os.path.exists(runner_path):
                os.remove(runner_path)
        except Exception:
            pass
