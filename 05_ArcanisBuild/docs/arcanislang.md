# ArcanisLang Integration

ArcanisBuild is designed to work seamlessly with ArcanisLang and is built with future ArcanisOS support in mind.

## ArcanisLang Source Files

ArcanisLang source files use the `.arc` extension. Documentation comments use `///`:

```arc
/// This is a documentation comment
/// that will be extracted by the docs generator
fn documented_function() {
    // implementation
}
```

## Build Pipeline

```
.arc Source ──► ArcanisLang Compiler (arcanisc) ──► .o / .arcanisbc ──► Linker ──► Executable/Library
```

## Compiler Interface

The build engine invokes the ArcanisLang compiler (`arcanisc`) with:

```
arcanisc -o <output> [flags] [sources...] [-- [linker_flags]]
```

Target type flags:
- `--build-exe` for executables
- `--build-lib` for libraries
- `--build-obj` for object files

## Dependency Tracking

ArcanisBuild tracks dependencies at the file level using SHA-256 hashes. When a source file changes, only the affected targets and their dependents are rebuilt.

## ArcanisOS Roadmap

Future versions will add:
- Native cross-compilation targeting ArcanisOS
- ArcanisOS package format generation
- Kernel module build support
- System image assembly
