import re
from dataclasses import dataclass

_PYTHON_BLOCK_RE = re.compile(r"```python\s*\n(.*?)```", re.DOTALL)
_BASH_BLOCK_RE = re.compile(r"```(?:bash|sh)\s*\n(.*?)```", re.DOTALL)
_ANY_BLOCK_RE = re.compile(r"```(?:python|bash|sh)\s*\n(.*?)```", re.DOTALL)
_TRAILING_DONE_RE = re.compile(r"\bDONE\s*$", re.IGNORECASE)


@dataclass
class CodeBlock:
    code: str
    lang: str  # "python" or "bash"


def extract_code_blocks(text):
    """Extract fenced python and bash code blocks from text.

    Returns list of CodeBlock with lang and code.
    Strips trailing DONE if the model put it inside a code block.
    """
    blocks = []
    for m in re.finditer(r"```(python|bash|sh)\s*\n(.*?)```", text, re.DOTALL):
        lang = "bash" if m.group(1) in ("bash", "sh") else "python"
        code = _TRAILING_DONE_RE.sub("", m.group(2)).rstrip()
        if code:
            blocks.append(CodeBlock(code=code, lang=lang))
    return blocks


def is_done(text):
    """Check if the model signaled it's finished.

    Looks at text outside of code blocks.
    """
    outside = _ANY_BLOCK_RE.sub("", text).strip().rstrip(".")
    return outside.upper().endswith("DONE")
