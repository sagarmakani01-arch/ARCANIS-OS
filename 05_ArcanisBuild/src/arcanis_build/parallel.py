"""Parallel task execution for concurrent builds."""

from concurrent.futures import ThreadPoolExecutor, as_completed, Future
from typing import Callable, List, Any, Dict, Optional
import os
import threading


class ParallelExecutor:
    def __init__(self, max_workers: int = None):
        if max_workers is None or max_workers <= 0:
            max_workers = os.cpu_count() or 4
        self.max_workers = max_workers
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._futures: List[Future] = []
        self._results: Dict[str, Any] = {}
        self._lock = threading.Lock()

    def submit(self, task_id: str, fn: Callable, *args, **kwargs) -> Future:
        future = self._executor.submit(fn, *args, **kwargs)
        with self._lock:
            self._futures.append((task_id, future))
        return future

    def wait_all(self, progress_callback: Callable = None) -> Dict[str, Any]:
        total = len(self._futures)
        completed = 0
        errors = []

        for task_id, future in self._futures:
            try:
                result = future.result()
                with self._lock:
                    self._results[task_id] = result
                completed += 1
                if progress_callback:
                    progress_callback(task_id, completed, total, None)
            except Exception as e:
                completed += 1
                errors.append((task_id, str(e)))
                if progress_callback:
                    progress_callback(task_id, completed, total, str(e))

        self._futures.clear()
        return {"results": self._results, "errors": errors, "total": total, "success": total - len(errors)}

    def map(self, fn: Callable, items: List[Any]) -> List[Any]:
        return list(self._executor.map(fn, items))

    def shutdown(self, wait=True):
        self._executor.shutdown(wait=wait)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()
