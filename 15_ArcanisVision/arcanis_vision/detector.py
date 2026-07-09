from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from .config import Config
from .utils import rgb_to_hsv, rgb_to_grayscale


class ObjectDetector:
    def __init__(self, config: Config | None = None):
        self.config = config or Config()

    def detect_faces(self, arr: NDArray[np.uint8]) -> list[dict]:
        if arr.ndim != 3 or arr.shape[2] != 3:
            raise ValueError("Input must be an RGB image (H, W, 3)")

        hsv = rgb_to_hsv(arr)
        h, s, v = hsv[:, :, 0], hsv[:, :, 1], hsv[:, :, 2]

        lower = self.config.detection.skin_color_lower
        upper = self.config.detection.skin_color_upper

        h_low, s_low, v_low = lower[0] / 360.0, lower[1] / 255.0, lower[2] / 255.0
        h_high, s_high, v_high = upper[0] / 360.0, upper[1] / 255.0, upper[2] / 255.0

        skin_mask = (
            (h >= h_low)
            & (h <= h_high)
            & (s >= s_low)
            & (s <= s_high)
            & (v >= v_low)
            & (v <= v_high)
        ).astype(np.uint8)

        kernel = np.ones((5, 5), dtype=np.uint8)
        skin_mask = self._morphological_open(skin_mask, kernel)
        skin_mask = self._morphological_close(skin_mask, kernel)

        regions = self._connected_components(skin_mask)
        faces = []
        img_h, img_w = arr.shape[:2]
        min_size = min(img_h, img_w) * 0.02
        max_size = min(img_h, img_w) * 0.8

        for bbox in regions:
            x, y, w, h = bbox
            if w < min_size or h < min_size:
                continue
            if w > max_size or h > max_size:
                continue
            aspect = w / h if h > 0 else 0
            if 0.3 < aspect < 3.0:
                area = w * h
                faces.append({
                    "bbox": (x, y, w, h),
                    "confidence": min(1.0, area / (img_h * img_w * 0.01)),
                })

        faces.sort(key=lambda f: f["confidence"], reverse=True)
        return faces

    def detect_edges(
        self,
        arr: NDArray[np.uint8],
        low_threshold: int | None = None,
        high_threshold: int | None = None,
    ) -> NDArray[np.uint8]:
        gray = rgb_to_grayscale(arr) if arr.ndim == 3 else arr
        grad_x, grad_y = self._sobel_gradients(gray)
        magnitude = np.sqrt(grad_x**2 + grad_y**2)
        mag_max = magnitude.max()
        if mag_max > 0:
            magnitude = (magnitude / mag_max * 255)

        low = low_threshold or self.config.detection.edge_low_threshold
        high = high_threshold or self.config.detection.edge_high_threshold

        edges = np.zeros_like(gray)
        strong = magnitude >= high
        weak = (magnitude >= low) & (magnitude < high)
        edges[strong] = 255

        h, w = gray.shape
        for i in range(1, h - 1):
            for j in range(1, w - 1):
                if weak[i, j]:
                    if np.any(edges[i - 1 : i + 2, j - 1 : j + 2] == 255):
                        edges[i, j] = 255

        return edges.astype(np.uint8)

    def _sobel_gradients(self, gray: NDArray[np.uint8]) -> tuple[NDArray[np.floating], NDArray[np.floating]]:
        h, w = gray.shape
        gray_f = gray.astype(np.float64)
        gx = np.zeros_like(gray_f)
        gy = np.zeros_like(gray_f)
        for i in range(1, h - 1):
            for j in range(1, w - 1):
                gx[i, j] = (
                    -gray_f[i - 1, j - 1] + gray_f[i - 1, j + 1]
                    - 2 * gray_f[i, j - 1] + 2 * gray_f[i, j + 1]
                    - gray_f[i + 1, j - 1] + gray_f[i + 1, j + 1]
                )
                gy[i, j] = (
                    -gray_f[i - 1, j - 1] - 2 * gray_f[i - 1, j] - gray_f[i - 1, j + 1]
                    + gray_f[i + 1, j - 1] + 2 * gray_f[i + 1, j] + gray_f[i + 1, j + 1]
                )
        return gx, gy

    def detect_text_regions(self, arr: NDArray[np.uint8]) -> list[dict]:
        gray = rgb_to_grayscale(arr) if arr.ndim == 3 else arr
        binary = self._adaptive_threshold(gray)

        kernel_h = np.ones((1, 20), dtype=np.uint8)
        kernel_v = np.ones((5, 1), dtype=np.uint8)
        dilated_h = self._dilate(binary, kernel_h)
        dilated_v = self._dilate(binary, kernel_v)
        combined = self._erode(dilated_h & dilated_v, np.ones((3, 3), dtype=np.uint8))

        regions = self._connected_components(combined)
        result = []
        min_size = self.config.detection.min_text_region_size

        for bbox in regions:
            x, y, w, h = bbox
            if w < min_size or h < 10:
                continue
            aspect = w / h if h > 0 else 0
            if aspect > 1.0:
                result.append({
                    "bbox": (x, y, w, h),
                    "type": "text_line",
                    "aspect_ratio": aspect,
                })

        return result

    def detect_colors(
        self, arr: NDArray[np.uint8], n_colors: int | None = None
    ) -> list[dict]:
        n = n_colors or self.config.detection.dominant_color_count
        pixels = arr.reshape(-1, 3).astype(np.float64)
        max_iter = self.config.detection.dominant_color_max_iter

        centroids = self._kmeans(pixels, n, max_iter)

        labels = self._assign_clusters(pixels, centroids)
        counts = np.bincount(labels, minlength=n)

        result = []
        total = len(labels)
        for i, c in enumerate(centroids):
            color = tuple(int(v) for v in c)
            pct = counts[i] / total
            result.append({
                "color": color,
                "percentage": round(pct, 4),
            })

        result.sort(key=lambda r: r["percentage"], reverse=True)
        return result

    def _kmeans(
        self, pixels: NDArray[np.floating], k: int, max_iter: int
    ) -> NDArray[np.floating]:
        rng = np.random.RandomState(42)
        indices = rng.choice(len(pixels), k, replace=False)
        centroids = pixels[indices].copy()

        for _ in range(max_iter):
            labels = self._assign_clusters(pixels, centroids)
            new_centroids = np.zeros_like(centroids)
            for j in range(k):
                mask = labels == j
                if mask.any():
                    new_centroids[j] = pixels[mask].mean(axis=0)
                else:
                    new_centroids[j] = centroids[j]
            if np.allclose(centroids, new_centroids, atol=1e-4):
                break
            centroids = new_centroids

        return centroids

    def _assign_clusters(
        self, pixels: NDArray[np.floating], centroids: NDArray[np.floating]
    ) -> NDArray[np.intp]:
        dists = np.sqrt(
            ((pixels[:, np.newaxis, :] - centroids[np.newaxis, :, :]) ** 2).sum(axis=2)
        )
        return dists.argmin(axis=1)

    def _morphological_open(
        self, mask: NDArray[np.uint8], kernel: NDArray[np.uint8]
    ) -> NDArray[np.uint8]:
        eroded = self._erode(mask, kernel)
        return self._dilate(eroded, kernel)

    def _morphological_close(
        self, mask: NDArray[np.uint8], kernel: NDArray[np.uint8]
    ) -> NDArray[np.uint8]:
        dilated = self._dilate(mask, kernel)
        return self._erode(dilated, kernel)

    def _erode(self, mask: NDArray[np.uint8], kernel: NDArray[np.uint8]) -> NDArray[np.uint8]:
        kh, kw = kernel.shape
        pad_h, pad_w = kh // 2, kw // 2
        padded = np.pad(mask, ((pad_h, pad_h), (pad_w, pad_w)), mode="constant", constant_values=0)
        result = np.zeros_like(mask)
        h, w = mask.shape
        for i in range(h):
            for j in range(w):
                patch = padded[i : i + kh, j : j + kw]
                if np.all(patch[kernel == 1] == 1):
                    result[i, j] = 1
        return result

    def _dilate(self, mask: NDArray[np.uint8], kernel: NDArray[np.uint8]) -> NDArray[np.uint8]:
        kh, kw = kernel.shape
        pad_h, pad_w = kh // 2, kw // 2
        padded = np.pad(mask, ((pad_h, pad_h), (pad_w, pad_w)), mode="constant", constant_values=0)
        result = np.zeros_like(mask)
        h, w = mask.shape
        for i in range(h):
            for j in range(w):
                patch = padded[i : i + kh, j : j + kw]
                if np.any(patch[kernel == 1] == 1):
                    result[i, j] = 1
        return result

    def _connected_components(self, mask: NDArray[np.uint8]) -> list[tuple[int, int, int, int]]:
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

    def _adaptive_threshold(
        self, gray: NDArray[np.uint8], block_size: int = 15, c: int = 10
    ) -> NDArray[np.uint8]:
        h, w = gray.shape
        result = np.zeros((h, w), dtype=np.uint8)
        pad = block_size // 2
        padded = np.pad(gray.astype(np.float64), pad, mode="reflect")
        ph, pw = padded.shape
        integral = np.zeros((ph + 1, pw + 1), dtype=np.float64)
        integral[1:, 1:] = np.cumsum(np.cumsum(padded, axis=0), axis=1)

        for i in range(h):
            for j in range(w):
                y1 = i
                x1 = j
                y2 = i + block_size
                x2 = j + block_size
                total = integral[y2, x2] - integral[y1, x2] - integral[y2, x1] + integral[y1, x1]
                mean = total / (block_size * block_size)
                if gray[i, j] > mean - c:
                    result[i, j] = 1
        return result
