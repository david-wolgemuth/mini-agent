import re

_CODE_BLOCK_RE = re.compile(r"```python\s*\n(.*?)```", re.DOTALL)


_TRAILING_DONE_RE = re.compile(r"\bDONE\s*$", re.IGNORECASE)


def extract_code_blocks(text):
    """Extract all ```python fenced code blocks from text.

    Returns list of code strings, or empty list if none found.
    Strips trailing DONE if the model put it inside a code block.
    """
    blocks = _CODE_BLOCK_RE.findall(text)
    return [_TRAILING_DONE_RE.sub("", b).rstrip() for b in blocks]


def is_done(text):
    """Check if the model signaled it's finished.

    Looks at text outside of code blocks.
    """
    outside = _CODE_BLOCK_RE.sub("", text).strip().rstrip(".")
    return outside.upper().endswith("DONE")
