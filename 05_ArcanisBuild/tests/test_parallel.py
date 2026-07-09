"""Tests for parallel executor."""

import unittest
import time

from arcanis_build.parallel import ParallelExecutor


class TestParallelExecutor(unittest.TestCase):
    def test_submit_and_wait(self):
        executor = ParallelExecutor(max_workers=4)

        def dummy():
            return 42

        executor.submit("task1", dummy)
        result = executor.wait_all()
        self.assertEqual(result["results"]["task1"], 42)
        self.assertEqual(len(result["errors"]), 0)
        self.assertEqual(result["total"], 1)

    def test_multiple_tasks(self):
        executor = ParallelExecutor(max_workers=2)

        def add(a, b):
            return a + b

        executor.submit("t1", add, 1, 2)
        executor.submit("t2", add, 3, 4)
        executor.submit("t3", add, 5, 6)

        result = executor.wait_all()
        self.assertEqual(result["results"]["t1"], 3)
        self.assertEqual(result["results"]["t2"], 7)
        self.assertEqual(result["results"]["t3"], 11)
        self.assertEqual(len(result["errors"]), 0)

    def test_task_failure(self):
        executor = ParallelExecutor(max_workers=2)

        def failing():
            raise ValueError("oops")

        executor.submit("fail", failing)
        result = executor.wait_all()
        self.assertEqual(len(result["errors"]), 1)
        self.assertIn("oops", result["errors"][0][1])

    def test_map(self):
        executor = ParallelExecutor(max_workers=4)
        result = executor.map(lambda x: x * 2, [1, 2, 3, 4])
        self.assertEqual(result, [2, 4, 6, 8])

    def test_context_manager(self):
        with ParallelExecutor(max_workers=2) as executor:
            executor.submit("t", lambda: "ok")
            result = executor.wait_all()
        self.assertEqual(result["results"]["t"], "ok")

    def test_max_workers_default(self):
        executor = ParallelExecutor(max_workers=0)
        self.assertGreater(executor.max_workers, 0)


if __name__ == "__main__":
    unittest.main()
