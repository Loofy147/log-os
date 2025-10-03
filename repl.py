# repl.py
import sys
from core.parser import parse
from core.interpreter import evaluate
from core.environment import create_global_env
from core.errors import LogosError
from core.utils import lisp_str

def main():
    """Starts the Read-Eval-Print Loop for Log-Os."""
    global_env = create_global_env()
    print("Log-Os 0.0.1 REPL")
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