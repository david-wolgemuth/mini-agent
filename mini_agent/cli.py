import argparse
import os
import sys

from .executor import execute_code
from .ollama import call_ollama
from .parser import extract_code_blocks, is_done
from .prompts import RESULT_SUFFIX, SYSTEM_PROMPT

MAX_AUTO_TURNS = 5


def _truncate_history(messages, max_chars=12000):
    """Keep system prompt + most recent messages within budget."""
    system = messages[0]
    rest = messages[1:]

    total = len(system["content"])
    keep = []
    for msg in reversed(rest):
        total += len(msg["content"])
        if total > max_chars:
            break
        keep.append(msg)
    keep.reverse()

    return [system] + keep


def main():
    parser = argparse.ArgumentParser(description="Mini Agent — local Python coding agent")
    parser.add_argument("--model", default="qwen2.5-coder:3b", help="Ollama model name")
    parser.add_argument("--ollama-url", default="http://localhost:11434", help="Ollama base URL")
    parser.add_argument("--confirm", action="store_true", help="Ask before executing code")
    parser.add_argument("--no-stream", action="store_true", help="Disable streaming output")
    parser.add_argument("prompt", nargs="*", help="Initial prompt (or omit for interactive mode)")
    args = parser.parse_args()

    messages = [{"role": "system", "content": SYSTEM_PROMPT.format(cwd=os.getcwd())}]
    namespace = {"__builtins__": __builtins__}

    initial_prompt = " ".join(args.prompt) if args.prompt else None

    print(f"mini-agent ({args.model})")
    print("ctrl-c to interrupt, ctrl-d to quit\n")

    while True:
        # Get user input
        if initial_prompt:
            user_input = initial_prompt
            initial_prompt = None
            print(f">>> {user_input}")
        else:
            try:
                user_input = input(">>> ")
            except (EOFError, KeyboardInterrupt):
                print("\nbye")
                break

        if not user_input.strip():
            continue

        messages.append({"role": "user", "content": user_input})

        # Agent loop: model responds, we execute, model reacts
        for turn in range(MAX_AUTO_TURNS):
            messages = _truncate_history(messages)

            try:
                response = call_ollama(
                    messages, args.model, args.ollama_url, stream=not args.no_stream
                )
            except Exception as e:
                print(f"\n[ollama error: {e}]")
                break

            messages.append({"role": "assistant", "content": response})

            if is_done(response):
                break

            code_blocks = extract_code_blocks(response)
            if not code_blocks:
                break

            code = "\n".join(code_blocks)

            if args.confirm:
                try:
                    answer = input("\nexecute? [y/n] ")
                except (EOFError, KeyboardInterrupt):
                    print("\nskipped")
                    break
                if answer.lower() != "y":
                    messages.append(
                        {"role": "user", "content": "User declined to execute the code."}
                    )
                    continue

            result = execute_code(code, namespace)

            # Build feedback message
            parts = []
            if result.stdout:
                parts.append(f"stdout:\n{result.stdout}")
            if result.stderr:
                parts.append(f"stderr:\n{result.stderr}")
            if result.exception:
                parts.append(f"error:\n{result.exception}")
            if not parts:
                parts.append("(no output)")

            feedback = "\n".join(parts)
            print(f"\n[exec] {feedback}")

            messages.append({"role": "user", "content": f"Execution result:\n{feedback}{RESULT_SUFFIX}"})

            # If nothing happened at all, don't auto-continue
            if not result.stdout and not result.stderr and not result.exception:
                break

            # Auto-continue so model sees the result (or error) and can react

        # Back to user input


if __name__ == "__main__":
    main()
