"""ArcanisShell — .arc script execution.

A minimal, safe line-oriented scripting language for automation. Each line
is parsed through the same CommandParser the interactive shell uses, so
scripts reuse the traditional command set. Blank lines and `#` comments
are ignored. Scripts run under the sandbox and permission policy just like
interactive AI actions.
"""

from __future__ import annotations


from .errors import ShellRuntimeError
from .parser import CommandParser, TraditionalCommand
from .commands import CommandContext, Registry


def run_script(source: str, ctx: CommandContext, registry: Registry | None = None) -> str:
    """Execute an .arc script string and return combined stdout."""
    reg = registry or ctx.registry
    if reg is None:
        raise ShellRuntimeError("no command registry available for script execution")
    parser = CommandParser(known_commands=reg.names())
    outputs: list[str] = []
    for lineno, raw in enumerate(source.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        try:
            parsed = parser.parse(line)
        except Exception as exc:  # noqa: BLE001
            raise ShellRuntimeError(f"line {lineno}: {exc}") from exc
        if isinstance(parsed, TraditionalCommand):
            cmd = reg.get(parsed.name)
            if cmd is None:
                raise ShellRuntimeError(f"line {lineno}: unknown command {parsed.name}")
            result = cmd.fn(parsed.args, parsed.flags, ctx)
            if not result.success:
                raise ShellRuntimeError(f"line {lineno}: {result.stderr}")
            if result.stdout:
                outputs.append(result.stdout)
        else:
            # Natural-language line inside a script is not executed.
            raise ShellRuntimeError(f"line {lineno}: natural language not allowed in scripts")
    return "\n".join(outputs)
