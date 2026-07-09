from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from .config import Config
from .utils import compute_mse, rgb_to_grayscale


class ScreenAnalyzer:
    def __init__(self, config: Config | None = None):
        self.config = config or Config()

    def capture_screen(self, region: tuple[int, int, int, int] | None = None) -> NDArray[np.uint8]:
        w, h = self.config.screen.mock_capture_size
        if region:
            rx, ry, rw, rh = region
            w, h = rw, rh
        rng = np.random.RandomState(0)
        arr = rng.randint(0, 256, (h, w, 3), dtype=np.uint8)
        bg = 240
        arr[:h // 3, :, :] = bg
        arr[h // 3:2 * h // 3, :w // 3, :] = 200
        return arr

    def analyze_layout(self, arr: NDArray[np.uint8]) -> dict:
        gray = rgb_to_grayscale(arr) if arr.ndim == 3 else arr
        binary = self._threshold(gray)

        kernel = np.ones((3, 3), dtype=np.uint8)
        dilated = self._dilate(binary, kernel)

        blocks = self._find_blocks(dilated)
        elements = []
        img_h, img_w = arr.shape[:2]

        for bbox in blocks:
            x, y, w, h = bbox
            area = w * h
            aspect = w / h if h > 0 else 0
            mean_intensity = float(np.mean(gray[y:y + h, x:x + w]))

            if mean_intensity > 200:
                elem_type = "text_block"
            elif area > img_h * img_w * 0.3:
                elem_type = "background"
            else:
                elem_type = "ui_element"

            elements.append({
                "bbox": (x, y, w, h),
                "type": elem_type,
                "area": area,
                "aspect_ratio": round(aspect, 2),
            })

        elements.sort(key=lambda e: e["area"], reverse=True)
        return {"elements": elements, "image_size": (img_w, img_h)}

    def compare_screenshots(
        self, img1: NDArray[np.uint8], img2: NDArray[np.uint8]
    ) -> dict:
        if img1.shape != img2.shape:
            raise ValueError("Screenshots must have the same dimensions")

        mse = compute_mse(img1.astype(np.float64), img2.astype(np.float64))
        diff = np.abs(img1.astype(np.float64) - img2.astype(np.float64))
        diff_gray = np.mean(diff, axis=2) if diff.ndim == 3 else diff
        changed = diff_gray > self.config.screen.diff_threshold * 255
        changed_pct = float(np.mean(changed))

        diff_map = (diff_gray / diff_gray.max() * 255).astype(np.uint8) if diff_gray.max() > 0 else diff_gray.astype(np.uint8)

        return {
            "mse": mse,
            "changed_percentage": round(changed_pct, 4),
            "diff_map": diff_map,
        }

    def extract_roi(
        self, arr: NDArray[np.uint8], min_area: int | None = None
    ) -> list[dict]:
        min_a = min_area or self.config.screen.roi_min_area
        gray = rgb_to_grayscale(arr) if arr.ndim == 3 else arr
        binary = self._threshold(gray)
        kernel = np.ones((3, 3), dtype=np.uint8)
        dilated = self._dilate(binary, kernel)
        bboxes = self._find_blocks(dilated)

        result = []
        for bbox in bboxes:
            x, y, w, h = bbox
            area = w * h
            if area < min_a:
                continue
            region = arr[y:y + h, x:x + w]
            mean_color = tuple(int(v) for v in region.mean(axis=(0, 1))) if arr.ndim == 3 else (int(region.mean()),)
            result.append({
                "bbox": (x, y, w, h),
                "area": area,
                "mean_color": mean_color,
            })

        result.sort(key=lambda r: r["area"], reverse=True)
        return result

    def _threshold(self, gray: NDArray[np.uint8], threshold: int = 128) -> NDArray[np.uint8]:
        return (gray < threshold).astype(np.uint8)

    def _dilate(self, mask: NDArray[np.uint8], kernel: NDArray[np.uint8]) -> NDArray[np.uint8]:
        kh, kw = kernel.shape
        pad_h, pad_w = kh // 2, kw // 2
        padded = np.pad(mask, ((pad_h, pad_h), (pad_w, pad_w)), mode="constant", constant_values=0)
        result = np.zeros_like(mask)
        h, w = mask.shape
        for i in range(h):
            for j in range(w):
                patch = padded[i:i + kh, j:j + kw]
                if np.any(patch[kernel == 1] == 1):
                    result[i, j] = 1
        return result

    def _find_blocks(self, mask: NDArray[np.uint8]) -> list[tuple[int, int, int, int]]:
        h, w = mask.shape
        visited = np.zeros((h, w), dtype=bool)
        bboxes = []

        for i in range(h):
            for j in range(w):
                if mask[i, j] == 1 and not visited[i, j]:
                    min_i, min_j = i, j
                    max_i, max_j = i, j
                    stack = [(i, j)]
                    visited[i, j] = True
                    while stack:
                        ci, cj = stack.pop()
                        min_i = min(min_i, ci)
                        min_j = min(min_j, cj)
                        max_i = max(max_i, ci)
                        max_j = max(max_j, cj)
                        for di in [-1, 0, 1]:
                            for dj in [-1, 0, 1]:
                                ni, nj = ci + di, cj + dj
                                if 0 <= ni < h and 0 <= nj < w and not visited[ni, nj] and mask[ni, nj] == 1:
                                    visited[ni, nj] = True
                                    stack.append((ni, nj))
                    bboxes.append((min_j, min_i, max_j - min_j + 1, max_i - min_i + 1))
        return bboxes
