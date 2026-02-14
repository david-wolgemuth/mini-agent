# mini-agent

A minimal coding agent powered by local LLMs via [Ollama](https://ollama.com). Runs bash or Python in a loop — the model writes code, it gets executed, the model sees the result, and keeps going until done.

## Setup

```
uv sync
```

Requires [Ollama](https://ollama.com) running locally with a model pulled (default: `qwen2.5-coder:3b`).

## Usage

```
mini-agent                        # interactive mode
mini-agent "list all python files" # one-shot prompt
mini-agent --python "read config"  # prefer python over bash
mini-agent --model llama3 "..."    # use a different model
mini-agent --confirm "rm *.log"    # ask before each execution
```

## Example Session

````
$ uv run mini-agent 'explore the codebase'
mini-agent (qwen2.5-coder:3b)
ctrl-c to interrupt, ctrl-d to quit

>>> explore the codebase
```bash
tree mini-agent
```

[exec] stderr:
bash: line 1: tree: command not found

error:
exit code 127
```bash
find .
```

[exec] stdout:
.
./.venv
...
./mini_agent
./mini_agent/prompts.py
./mini_agent/parser.py
./mini_agent/executor.py
./mini_agent/__main__.py
./mini_agent/__init__.py
./mini_agent/cli.py
./mini_agent/ollama.py
./uv.lock
./pyproject.toml
./Makefile

```bash
git status
```

[exec] stdout:
On branch main
Your branch is up to date with 'origin/main'.
...

```bash
git log --oneline
```

DONE
>>> read a few of the most important files
```bash
cat mini_agent/cli.py
cat mini_agent/ollama.py
cat mini_agent/prompts.py
```

[exec] stdout:
import argparse
import os
import sys
...

DONE
>>> what is this project about
This project is a minimal Python coding agent that leverages local Large
Language Models (LLMs) via Ollama for interaction. It provides tools to
execute code in Python and Bash, a system prompt builder, and examples
of how to use its features.
DONE
>>> that is a better description for the readme ; echo that into the readme
```bash
echo "A minimal Python coding agent powered by local LLMs via Ollama." >> README.md
```

[exec] (no output)
DONE
>>> summarize the diff
```bash
git diff
```

[exec] stdout:
diff --git a/mini_agent/cli.py b/mini_agent/cli.py
...

DONE
>>> stage changes and make a commit
```bash
git add mini_agent/cli.py mini_agent/ollama.py mini_agent/prompts.py README.md
git commit -m "Update README.md content"
```

[exec] stdout:
[main a466434] Update README.md content
 4 files changed, 97 insertions(+), 26 deletions(-)
 create mode 100644 README.md

DONE
````

The agent recovers from errors (e.g. `tree` not found), reads files across
multiple turns, answers questions in plain text, and executes commands —
all driven by a 3b parameter model.

*This README was drafted by a human with help from the mini-agent itself.*
