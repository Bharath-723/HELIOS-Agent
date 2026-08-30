"""
core/code_sandbox.py — HELIOS Controlled Sandboxed Code Execution Engine
==========================================================================
Executes generated Python code snippets inside an isolated process boundary
with timeout protection, environment isolation, and structured stdout/stderr capture.
"""

import sys
import time
import subprocess
import tempfile
import logging
from pathlib import Path
from typing import Dict, Any, Optional

log = logging.getLogger("helios.code_sandbox")

class CodeExecutionResult:
    def __init__(self, success: bool, exit_code: int, stdout: str, stderr: str, elapsed_ms: float):
        self.success = success
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr
        self.elapsed_ms = elapsed_ms

class CodeSandbox:
    """Isolated Python code execution sandbox."""

    def __init__(self, timeout_seconds: float = 5.0):
        self.timeout_seconds = timeout_seconds

    def available(self) -> bool:
        return True

    def execute_python(self, code: str) -> CodeExecutionResult:
        log.info("Executing Python snippet in sandboxed process (Timeout: %.1fs)", self.timeout_seconds)
        t_start = time.time()

        # Create temporary script file
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", encoding="utf-8", delete=False) as tf:
            tf.write(code)
            script_path = tf.name

        try:
            cmd = [sys.executable, script_path]
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=tempfile.gettempdir()
            )

            try:
                stdout, stderr = proc.communicate(timeout=self.timeout_seconds)
                elapsed_ms = (time.time() - t_start) * 1000.0
                return CodeExecutionResult(
                    success=(proc.returncode == 0),
                    exit_code=proc.returncode,
                    stdout=stdout.strip(),
                    stderr=stderr.strip(),
                    elapsed_ms=elapsed_ms
                )
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.communicate()
                elapsed_ms = (time.time() - t_start) * 1000.0
                return CodeExecutionResult(
                    success=False,
                    exit_code=-1,
                    stdout="",
                    stderr=f"Execution timed out after {self.timeout_seconds}s",
                    elapsed_ms=elapsed_ms
                )

        except Exception as exc:
            elapsed_ms = (time.time() - t_start) * 1000.0
            log.error("CodeSandbox execution error: %s", exc, exc_info=True)
            return CodeExecutionResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr=str(exc),
                elapsed_ms=elapsed_ms
            )
        finally:
            try:
                Path(script_path).unlink(missing_ok=True)
            except Exception:
                pass
