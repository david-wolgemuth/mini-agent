import argparse
import os
import sys

from .executor import execute_bash, execute_code
from .ollama import call_ollama
from .parser import extract_code_blocks, is_done
from .prompts import result_suffix, build_system_prompt

MAX_AUTO_TURNS = 20


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
    parser = argparse.ArgumentParser(description="Mini Agent — local coding agent")
    parser.add_argument("--model", default="qwen2.5-coder:3b", help="Ollama model name")
    parser.add_argument("--ollama-url", default="http://localhost:11434", help="Ollama base URL")
    parser.add_argument("--confirm", action="store_true", help="Ask before executing code")
    parser.add_argument("--no-stream", action="store_true", help="Disable streaming output")
    lang_group = parser.add_mutually_exclusive_group()
    lang_group.add_argument("--bash", action="store_const", const="bash", dest="lang", help="Use bash by default (default)")
    lang_group.add_argument("--python", action="store_const", const="python", dest="lang", help="Use python by default")
    parser.set_defaults(lang="bash")
    parser.add_argument("prompt", nargs="*", help="Initial prompt (or omit for interactive mode)")
    args = parser.parse_args()

    messages = [{"role": "system", "content": build_system_prompt(os.getcwd(), args.lang)}]
    namespace = {"__builtins__": __builtins__}

    initial_prompt = " ".join(args.prompt) if args.prompt else None

    print(f"mini-agent ({args.model})")
    print("ctrl-c to interrupt, ctrl-d to quit\n")

    waiting_for_quit = False

    while True:
        # Get user input
        if initial_prompt:
            user_input = initial_prompt
            initial_prompt = None
            print(f">>> {user_input}")
        else:
            try:
                user_input = input(">>> ")
                waiting_for_quit = False
            except KeyboardInterrupt:
                if waiting_for_quit:
                    print("\nbye")
                    break
                print("\nctrl-c again to quit")
                waiting_for_quit = True
                continue
            except EOFError:
                print("\nbye")
                break

        if not user_input.strip():
            continue

        messages.append({"role": "user", "content": user_input})
        current_request = user_input

        # Agent loop: model responds, we execute, model reacts
        for turn in range(MAX_AUTO_TURNS):
            messages = _truncate_history(messages)

            try:
                response = call_ollama(
                    messages, args.model, args.ollama_url, stream=not args.no_stream
                )
            except KeyboardInterrupt:
                print("\n[interrupted]")
                break
            except Exception as e:
                print(f"\n[ollama error: {e}]")
                break

            messages.append({"role": "assistant", "content": response})

            if is_done(response):
                break

            code_blocks = extract_code_blocks(response)
            if not code_blocks:
                # Model responded with text instead of code — nudge it back
                messages.append(
                    {"role": "user", "content": result_suffix(current_request)}
                )
                continue

            # Execute all code blocks, collect results
            skipped = False
            interrupted = False
            all_parts = []
            for block in code_blocks:
                if args.confirm:
                    try:
                        answer = input(f"\nexecute {block.lang}? [y/n] ")
                    except (EOFError, KeyboardInterrupt):
                        print("\nskipped")
                        skipped = True
                        break
                    if answer.lower() != "y":
                        skipped = True
                        break

                try:
                    if block.lang == "bash":
                        result = execute_bash(block.code)
                    else:
                        result = execute_code(block.code, namespace)
                except KeyboardInterrupt:
                    print("\n[interrupted]")
                    interrupted = True
                    break

                if result.stdout:
                    all_parts.append(f"stdout:\n{result.stdout}")
                if result.stderr:
                    all_parts.append(f"stderr:\n{result.stderr}")
                if result.exception:
                    all_parts.append(f"error:\n{result.exception}")

            if interrupted:
                break

            if skipped:
                messages.append(
                    {"role": "user", "content": "User declined to execute the code."}
                )
                continue

            if not all_parts:
                all_parts.append("(no output)")

            feedback = "\n".join(all_parts)
            print(f"\n[exec] {feedback}")

            messages.append({"role": "user", "content": f"Execution result:\n{feedback}{result_suffix(current_request)}"})

        # Back to user input


if __name__ == "__main__":
    main()
