import contextlib
import io
import signal
import traceback
from dataclasses import dataclass


@dataclass
class ExecutionResult:
    stdout: str
    stderr: str
    exception: str | None


class _Timeout:
    """Context manager for execution timeout using SIGALRM."""

    def __init__(self, seconds):
        self.seconds = seconds

    def __enter__(self):
        if self.seconds > 0:
            signal.signal(signal.SIGALRM, self._handler)
            signal.alarm(self.seconds)
        return self

    def __exit__(self, *args):
        if self.seconds > 0:
            signal.alarm(0)

    @staticmethod
    def _handler(signum, frame):
        raise TimeoutError("Code execution timed out")


def execute_code(code, namespace, timeout=30):
    """Execute Python code in a persistent namespace.

    Captures stdout/stderr and any exceptions.
    """
    stdout_buf = io.StringIO()
    stderr_buf = io.StringIO()
    exception = None

    try:
        with (
            _Timeout(timeout),
            contextlib.redirect_stdout(stdout_buf),
            contextlib.redirect_stderr(stderr_buf),
        ):
            exec(code, namespace)
    except TimeoutError as e:
        exception = str(e)
    except Exception:
        exception = traceback.format_exc()

    return ExecutionResult(
        stdout=stdout_buf.getvalue(),
        stderr=stderr_buf.getvalue(),
        exception=exception,
    )
