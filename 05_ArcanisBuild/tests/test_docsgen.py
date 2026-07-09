"""Tests for documentation generator."""

import os
import tempfile
import unittest

from arcanis_build.docsgen import DocGenerator, DocBlock


class TestDocBlock(unittest.TestCase):
    def test_docblock_to_markdown_with_symbol(self):
        block = DocBlock(
            source_file="src/main.arc",
            line=1,
            content="This is the main function",
            symbol="main",
            symbol_type="fn",
        )
        md = block.to_markdown()
        self.assertIn("main", md)
        self.assertIn("(fn)", md)
        self.assertIn("main.arc:1", md)

    def test_docblock_to_markdown_without_symbol(self):
        block = DocBlock(
            source_file="src/lib.arc",
            line=5,
            content="General module docs",
        )
        md = block.to_markdown()
        self.assertIn("General module docs", md)
        self.assertNotIn("###", md)


class TestDocGenerator(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.src_dir = os.path.join(self.temp_dir, "src")
        self.out_dir = os.path.join(self.temp_dir, "docs")
        os.makedirs(self.src_dir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_discover_sources_empty(self):
        gen = DocGenerator(source_dir=self.src_dir)
        sources = gen.discover_sources()
        self.assertEqual(len(sources), 0)

    def test_discover_sources(self):
        for f in ["main.arc", "lib.arc", "test.txt"]:
            with open(os.path.join(self.src_dir, f), "w") as fh:
                fh.write("// code")

        gen = DocGenerator(source_dir=self.src_dir)
        sources = gen.discover_sources()
        self.assertEqual(len(sources), 2)

    def test_extract_docblocks(self):
        src_file = os.path.join(self.src_dir, "main.arc")
        with open(src_file, "w") as f:
            f.write("""/// This is the main entry point
/// for the application
fn main() {
    print("hello");
}

/// Utility function
fn helper() {
}
""")
        gen = DocGenerator(source_dir=self.src_dir)
        blocks = gen.extract_docblocks(src_file)
        self.assertEqual(len(blocks), 2)
        self.assertEqual(blocks[0].symbol, "main")
        self.assertEqual(blocks[1].symbol, "helper")
        self.assertIn("main entry point", blocks[0].content)

    def test_extract_docblocks_no_docs(self):
        src_file = os.path.join(self.src_dir, "plain.arc")
        with open(src_file, "w") as f:
            f.write("fn foo() {}\nfn bar() {}\n")

        gen = DocGenerator(source_dir=self.src_dir)
        blocks = gen.extract_docblocks(src_file)
        self.assertEqual(len(blocks), 0)

    def test_generate_markdown(self):
        src_file = os.path.join(self.src_dir, "main.arc")
        with open(src_file, "w") as f:
            f.write("/// Documented function\nfn hello() {}\n")

        gen = DocGenerator(
            source_dir=self.src_dir,
            output_dir=self.out_dir,
            fmt="markdown",
        )
        files = gen.generate()
        md_files = [f for f in files if f.endswith(".md")]
        self.assertGreaterEqual(len(md_files), 1)
        self.assertTrue(os.path.exists(md_files[0]))

    def test_generate_json(self):
        src_file = os.path.join(self.src_dir, "main.arc")
        with open(src_file, "w") as f:
            f.write("/// JSON doc\nfn process() {}\n")

        gen = DocGenerator(
            source_dir=self.src_dir,
            output_dir=self.out_dir,
            fmt="json",
        )
        files = gen.generate()
        self.assertEqual(len(files), 1)
        self.assertTrue(files[0].endswith(".json"))

    def test_generate_index(self):
        for name in ["a.arc", "b.arc"]:
            with open(os.path.join(self.src_dir, name), "w") as f:
                f.write(f"/// {name}\nfn {name.replace('.', '_')}() {{}}\n")

        gen = DocGenerator(
            source_dir=self.src_dir,
            output_dir=self.out_dir,
        )
        files = gen.generate()
        index_files = [f for f in files if f.endswith("index.md")]
        self.assertEqual(len(index_files), 1)


if __name__ == "__main__":
    unittest.main()
