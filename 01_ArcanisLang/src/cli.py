import sys
import os
import traceback

def main():
    args = sys.argv[1:]
    if not args:
        run_repl()
        return
    if args[0] in ('-h', '--help'):
        print_help()
        return
    if args[0] in ('-v', '--version'):
        print("ArcanisLang v0.1.0")
        return
    filepath = args[0]
    if not os.path.exists(filepath):
        print(f"Error: file not found: {filepath}", file=sys.stderr)
        sys.exit(1)
    run_file(filepath)

def run_file(path):
    from . import run_source
    with open(path, "r", encoding="utf-8") as f:
        source = f.read()
    try:
        result = run_source(source, path)
        if result is not None:
            print(result)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if os.environ.get("ARCANIS_DEBUG"):
            traceback.print_exc()
        sys.exit(1)

def run_repl():
    from . import run_source
    print("ArcanisLang v0.1.0 - Interactive Shell")
    print("Type 'exit' to quit, 'help' for help")
    buffer = ""
    while True:
        try:
            prompt = "... " if buffer else ">>> "
            line = input(prompt)
            if line.strip() == "exit":
                break
            if line.strip() == "help":
                print("ArcanisLang - A beginner-friendly programming language")
                print("  - Variables: x = 42")
                print("  - Functions: fun greet(name): return 'Hello ' + name")
                print("  - Loops: for i in range(5): print(i)")
                print("  - Classes: class Person: fun init(self, n): self.name = n")
                continue
            buffer += line + "\n"
            try:
                result = run_source(buffer, "<repl>")
                if result is not None:
                    print(result)
                buffer = ""
            except (SyntaxError, Exception):
                if not buffer.strip():
                    buffer = ""
                else:
                    try:
                        compile(buffer + "\n", "<repl>", "exec")
                        print("Syntax error")
                        buffer = ""
                    except:
                        pass
        except (EOFError, KeyboardInterrupt):
            print()
            break

def print_help():
    print("Usage: arcanis [options] [file.arc]")
    print()
    print("Options:")
    print("  <file.arc>     Run an ArcanisLang script")
    print("  -h, --help     Show this help message")
    print("  -v, --version  Show version")
    print()
    print("Without arguments, starts the interactive REPL.")

if __name__ == "__main__":
    main()
