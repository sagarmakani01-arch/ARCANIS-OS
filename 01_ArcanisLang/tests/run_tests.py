#!/usr/bin/env python3
import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def run_all():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    test_dir = os.path.dirname(__file__)
    for file in os.listdir(test_dir):
        if file.startswith("test_") and file.endswith(".py"):
            module_name = file[:-3]
            try:
                module = __import__(f"tests.{module_name}", fromlist=[module_name])
                suite.addTest(loader.loadTestsFromModule(module))
            except Exception as e:
                print(f"Warning: Could not load {module_name}: {e}", file=sys.stderr)

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_all()
    sys.exit(0 if success else 1)
