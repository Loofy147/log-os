# repl.py
import sys
from core.parser import parse, parse_stream
from core.interpreter import evaluate
from core.environment import create_global_env
from core.errors import LogosError
from core.utils import lisp_str

def main():
    """Starts the Read-Eval-Print Loop for Log-Os."""
    global_env = create_global_env(evaluate)

    # Load the kernel and core libraries to bootstrap the language
    core_files = ["kernel.l0", "core/evaluators.l0", "core/orchestrator.l0", "stdlib/core.l0"]
    try:
        for core_file in core_files:
            with open(core_file) as f:
                source = f.read()
            asts = parse_stream(source)
            for ast in asts:
                evaluate(ast, global_env)
            print(f"Loaded {core_file}.")
    except FileNotFoundError as e:
        print(f"Warning: {e.filename} not found. Language may be in a degraded state.")
    except LogosError as e:
        print(f"FATAL: Error loading core file: {e}")
        return

    print("\nLog-Os 0.0.1 REPL")
    print("Press Ctrl+C to exit.")

    while True:
        try:
            source = input("log-os> ")
            if not source.strip():
                continue

            ast = parse(source)
            result = evaluate(ast, global_env)

            if result is not None:
                print(lisp_str(result))

        except (LogosError, NameError) as e:
            print(f"Error: {e}", file=sys.stderr)
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            break
        except Exception as e:
            print(f"An unexpected Python error occurred: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()