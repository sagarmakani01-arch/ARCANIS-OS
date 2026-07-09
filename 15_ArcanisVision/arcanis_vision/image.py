from __future__ import annotations

import io
from typing import Any

import numpy as np
from numpy.typing import NDArray
from PIL import Image, ImageFilter, ExifTags

from .config import Config
from .utils import rgb_to_grayscale, resize_array


class ImageProcessor:
    def __init__(self, config: Config | None = None):
        self.config = config or Config()

    def load_from_file(self, path: str) -> Image.Image:
        return Image.open(path).convert("RGB")

    def load_from_bytes(self, data: bytes) -> Image.Image:
        return Image.open(io.BytesIO(data)).convert("RGB")

    def load_from_numpy(self, arr: NDArray[np.uint8]) -> Image.Image:
        return Image.fromarray(arr).convert("RGB")

    def to_numpy(self, img: Image.Image) -> NDArray[np.uint8]:
        return np.array(img)

    def resize(
        self,
        img: Image.Image,
        width: int,
        height: int,
        method: str = "lanczos",
    ) -> Image.Image:
        method_map = {
            "nearest": Image.NEAREST,
            "bilinear": Image.BILINEAR,
            "bicubic": Image.BICUBIC,
            "lanczos": Image.LANCZOS,
        }
        resample = method_map.get(method, Image.LANCZOS)
        return img.resize((width, height), resample)

    def crop(
        self,
        img: Image.Image,
        x: int,
        y: int,
        width: int,
        height: int,
    ) -> Image.Image:
        return img.crop((x, y, x + width, y + height))

    def rotate(self, img: Image.Image, degrees: float, expand: bool = True) -> Image.Image:
        return img.rotate(-degrees, expand=expand, resample=Image.BICUBIC)

    def flip_horizontal(self, img: Image.Image) -> Image.Image:
        return img.transpose(Image.FLIP_LEFT_RIGHT)

    def flip_vertical(self, img: Image.Image) -> Image.Image:
        return img.transpose(Image.FLIP_TOP_BOTTOM)

    def convert_format(self, img: Image.Image, fmt: str) -> bytes:
        buf = io.BytesIO()
        img.save(buf, format=fmt.upper())
        return buf.getvalue()

    def apply_filter(self, img: Image.Image, filter_name: str) -> Image.Image:
        filter_map = {
            "blur": ImageFilter.GaussianBlur(radius=3),
            "sharpen": ImageFilter.SHARPEN,
            "edge_detect": ImageFilter.FIND_EDGES,
            "emboss": ImageFilter.EMBOSS,
            "smooth": ImageFilter.SMOOTH,
            "smooth_more": ImageFilter.SMOOTH_MORE,
        }
        pil_filter = filter_map.get(filter_name)
        if pil_filter is None:
            raise ValueError(f"Unknown filter: {filter_name}")
        return img.filter(pil_filter)

    def thumbnail(self, img: Image.Image, max_size: tuple[int, int] | None = None) -> Image.Image:
        size = max_size or self.config.vision.default_thumbnail_size
        thumb = img.copy()
        thumb.thumbnail(size, Image.LANCZOS)
        return thumb

    def extract_exif(self, img: Image.Image) -> dict[str, Any]:
        raw_exif = img.getexif()
        if not raw_exif:
            return {}
        result = {}
        for tag_id, value in raw_exif.items():
            tag_name = ExifTags.TAGS.get(tag_id, str(tag_id))
            try:
                if isinstance(value, bytes):
                    value = value.decode("utf-8", errors="replace")
                result[tag_name] = value
            except Exception:
                result[tag_name] = str(value)
        return result

    def numpy_blur(self, arr: NDArray[np.uint8], radius: int = 3) -> NDArray[np.uint8]:
        if arr.ndim == 2:
            return self._numpy_blur_2d(arr, radius)
        channels = [self._numpy_blur_2d(arr[:, :, c], radius) for c in range(arr.shape[2])]
        return np.stack(channels, axis=2)

    def _numpy_blur_2d(self, arr: NDArray[np.uint8], radius: int) -> NDArray[np.uint8]:
        kernel_size = 2 * radius + 1
        kernel = np.ones((kernel_size, kernel_size), dtype=np.float64) / (kernel_size * kernel_size)
        h, w = arr.shape
        pad = radius
        padded = np.pad(arr.astype(np.float64), pad, mode="reflect")
        result = np.zeros_like(arr, dtype=np.float64)
        for i in range(h):
            for j in range(w):
                result[i, j] = np.sum(padded[i : i + kernel_size, j : j + kernel_size] * kernel)
        return result.clip(0, 255).astype(np.uint8)

    def numpy_edge_detect(self, arr: NDArray[np.uint8]) -> NDArray[np.uint8]:
        gray = rgb_to_grayscale(arr) if arr.ndim == 3 else arr
        grad_x = np.zeros_like(gray, dtype=np.float64)
        grad_y = np.zeros_like(gray, dtype=np.float64)
        h, w = gray.shape
        gray_f = gray.astype(np.float64)
        for i in range(1, h - 1):
            for j in range(1, w - 1):
                grad_x[i, j] = (
                    -gray_f[i - 1, j - 1] + gray_f[i - 1, j + 1]
                    - 2 * gray_f[i, j - 1] + 2 * gray_f[i, j + 1]
                    - gray_f[i + 1, j - 1] + gray_f[i + 1, j + 1]
                )
                grad_y[i, j] = (
                    -gray_f[i - 1, j - 1] - 2 * gray_f[i - 1, j] - gray_f[i - 1, j + 1]
                    + gray_f[i + 1, j - 1] + 2 * gray_f[i + 1, j] + gray_f[i + 1, j + 1]
                )
        magnitude = np.sqrt(grad_x**2 + grad_y**2)
        magnitude = (magnitude / magnitude.max() * 255) if magnitude.max() > 0 else magnitude
        return magnitude.astype(np.uint8)

    def numpy_sharpen(self, arr: NDArray[np.uint8]) -> NDArray[np.uint8]:
        kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]], dtype=np.float64)
        return self._apply_convolution(arr, kernel)

    def _apply_convolution(
        self, arr: NDArray[np.uint8], kernel: NDArray[np.floating]
    ) -> NDArray[np.uint8]:
        k_size = kernel.shape[0]
        pad = k_size // 2
        if arr.ndim == 3:
            channels = [
                self._apply_convolution(arr[:, :, c], kernel) for c in range(arr.shape[2])
            ]
            return np.stack(channels, axis=2)
        padded = np.pad(arr.astype(np.float64), pad, mode="reflect")
        h, w = arr.shape
        result = np.zeros_like(arr, dtype=np.float64)
        for i in range(h):
            for j in range(w):
                result[i, j] = np.sum(
                    padded[i : i + k_size, j : j + k_size] * kernel
                )
        return result.clip(0, 255).astype(np.uint8)
