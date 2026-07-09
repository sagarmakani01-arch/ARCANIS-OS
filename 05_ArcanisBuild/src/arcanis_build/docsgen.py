"""Documentation generator - extracts docs from ArcanisLang source files."""

import os
import re
from typing import List, Optional


class DocBlock:
    def __init__(self, source_file: str, line: int, content: str,
                 symbol: str = None, symbol_type: str = None):
        self.source_file = source_file
        self.line = line
        self.content = content
        self.symbol = symbol
        self.symbol_type = symbol_type

    def to_markdown(self) -> str:
        header = f"### `{self.symbol}`" if self.symbol else ""
        type_info = f" *({self.symbol_type})*" if self.symbol_type else ""
        location = f"\n\n*Source: {self.source_file}:{self.line}*"
        return f"{header}{type_info}\n\n{self.content}{location}"


class DocGenerator:
    def __init__(self, source_dir: str = "src", output_dir: str = "docs/build", fmt: str = "markdown"):
        self.source_dir = source_dir
        self.output_dir = output_dir
        self.format = fmt

    def discover_sources(self) -> List[str]:
        sources = []
        for root, _, files in os.walk(self.source_dir):
            for f in files:
                if f.endswith(".arc"):
                    sources.append(os.path.join(root, f))
        return sorted(sources)

    def extract_docblocks(self, filepath: str) -> List[DocBlock]:
        docblocks = []
        with open(filepath, "r") as f:
            lines = f.readlines()

        i = 0
        while i < len(lines):
            line = lines[i]

            doc_match = re.match(r'^\s*///\s*(.*)', line)
            if doc_match:
                content = [doc_match.group(1)]
                start_line = i + 1
                i += 1
                while i < len(lines):
                    cont_match = re.match(r'^\s*///\s*(.*)', lines[i])
                    if cont_match:
                        content.append(cont_match.group(1))
                        i += 1
                    else:
                        break

                doc_text = "\n".join(content)

                symbol = None
                symbol_type = None
                if i < len(lines):
                    decl_match = re.match(
                        r'^\s*(fn|func|function|class|struct|module|const|var|type)\s+(\w+)',
                        lines[i]
                    )
                    if decl_match:
                        symbol_type = decl_match.group(1)
                        symbol = decl_match.group(2)

                docblocks.append(DocBlock(
                    source_file=filepath,
                    line=start_line,
                    content=doc_text,
                    symbol=symbol,
                    symbol_type=symbol_type,
                ))
            else:
                i += 1

        return docblocks

    def generate(self) -> List[str]:
        os.makedirs(self.output_dir, exist_ok=True)
        sources = self.discover_sources()
        output_files = []

        all_blocks = []
        for src in sources:
            blocks = self.extract_docblocks(src)
            all_blocks.extend(blocks)

        if self.format == "markdown":
            output_files.extend(self._generate_markdown(all_blocks, sources))
        elif self.format == "json":
            output_files.append(self._generate_json(all_blocks))

        return output_files

    def _generate_markdown(self, blocks: List[DocBlock], sources: List[str]) -> List[str]:
        output_files = []

        for src in sources:
            rel_path = os.path.relpath(src, self.source_dir)
            doc_name = os.path.splitext(rel_path)[0].replace(os.sep, "_")
            output_path = os.path.join(self.output_dir, f"{doc_name}.md")

            src_blocks = [b for b in blocks if b.source_file == src]

            with open(output_path, "w") as f:
                f.write(f"# {os.path.basename(src)}\n\n")
                f.write(f"*Generated documentation from `{rel_path}`*\n\n")

                if not src_blocks:
                    f.write("*No documentation comments found.*\n")
                else:
                    for block in src_blocks:
                        f.write(block.to_markdown())
                        f.write("\n\n---\n\n")

            output_files.append(output_path)

        if len(sources) > 1:
            index_path = os.path.join(self.output_dir, "index.md")
            with open(index_path, "w") as f:
                f.write("# API Documentation\n\n")
                f.write(f"Generated from {len(sources)} source files.\n\n")
                for src in sources:
                    rel = os.path.relpath(src, self.source_dir)
                    doc_name = os.path.splitext(os.path.basename(rel))[0]
                    f.write(f"- [{rel}]({doc_name}.md)\n")
            output_files.append(index_path)

        return output_files

    def _generate_json(self, blocks: List[DocBlock]) -> str:
        import json
        data = []
        for block in blocks:
            data.append({
                "file": block.source_file,
                "line": block.line,
                "content": block.content,
                "symbol": block.symbol,
                "symbol_type": block.symbol_type,
            })

        output_path = os.path.join(self.output_dir, "docs.json")
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)
        return output_path
