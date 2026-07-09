from __future__ import annotations

import numpy as np
from numpy.typing import NDArray


def compute_mse(img1: NDArray[np.floating], img2: NDArray[np.floating]) -> float:
    if img1.shape != img2.shape:
        raise ValueError("Images must have the same shape")
    return float(np.mean((img1.astype(np.float64) - img2.astype(np.float64)) ** 2))


def _gaussian_kernel(size: int, sigma: float) -> NDArray[np.floating]:
    ax = np.arange(size) - size // 2
    xx, yy = np.meshgrid(ax, ax)
    kernel = np.exp(-(xx**2 + yy**2) / (2 * sigma**2))
    return kernel / kernel.sum()


def compute_ssim(
    img1: NDArray[np.floating],
    img2: NDArray[np.floating],
    window_size: int = 7,
    c1: float = 0.01**2,
    c2: float = 0.03**2,
) -> float:
    if img1.shape != img2.shape:
        raise ValueError("Images must have the same shape")

    if img1.ndim == 3:
        channel_scores = []
        for ch in range(img1.shape[2]):
            channel_scores.append(
                compute_ssim(img1[:, :, ch], img2[:, :, ch], window_size, c1, c2)
            )
        return float(np.mean(channel_scores))

    img1_f = img1.astype(np.float64)
    img2_f = img2.astype(np.float64)

    kernel = _gaussian_kernel(window_size, window_size / 5.0)

    pad = window_size // 2
    img1_p = np.pad(img1_f, pad, mode="reflect")
    img2_p = np.pad(img2_f, pad, mode="reflect")

    h, w = img1_f.shape
    mu1 = np.zeros_like(img1_f)
    mu2 = np.zeros_like(img2_f)
    sig1_sq = np.zeros_like(img1_f)
    sig2_sq = np.zeros_like(img1_f)
    sig12 = np.zeros_like(img1_f)

    for i in range(h):
        for j in range(w):
            patch1 = img1_p[i : i + window_size, j : j + window_size]
            patch2 = img2_p[i : i + window_size, j : j + window_size]
            m1 = np.sum(patch1 * kernel)
            m2 = np.sum(patch2 * kernel)
            mu1[i, j] = m1
            mu2[i, j] = m2
            v1 = np.sum((patch1 - m1) ** 2 * kernel)
            v2 = np.sum((patch2 - m2) ** 2 * kernel)
            c = np.sum((patch1 - m1) * (patch2 - m2) * kernel)
            sig1_sq[i, j] = v1
            sig2_sq[i, j] = v2
            sig12[i, j] = c

    numerator = (2 * mu1 * mu2 + c1) * (2 * sig12 + c2)
    denominator = (mu1**2 + mu2**2 + c1) * (sig1_sq + sig2_sq + c2)
    ssim_map = numerator / denominator
    return float(np.mean(ssim_map))


def rgb_to_hsv(img: NDArray[np.uint8]) -> NDArray[np.floating]:
    rgb = img.astype(np.float64) / 255.0
    r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
    max_c = np.max(rgb, axis=2)
    min_c = np.min(rgb, axis=2)
    diff = max_c - min_c

    h = np.zeros_like(max_c)
    s = np.zeros_like(max_c)
    v = max_c

    mask_diff = diff > 0
    mask_max_r = mask_diff & (max_c == r)
    mask_max_g = mask_diff & (max_c == g) & ~mask_max_r
    mask_max_b = mask_diff & (max_c == b) & ~mask_max_r & ~mask_max_g

    h[mask_max_r] = 60.0 * ((g[mask_max_r] - b[mask_max_r]) / diff[mask_max_r] % 6)
    h[mask_max_g] = 60.0 * ((b[mask_max_g] - r[mask_max_g]) / diff[mask_max_g] + 2)
    h[mask_max_b] = 60.0 * ((r[mask_max_b] - g[mask_max_b]) / diff[mask_max_b] + 4)
    h[h < 0] += 360.0

    s[mask_diff] = diff[mask_diff] / max_c[mask_diff]

    result = np.stack([h / 360.0, s, v], axis=2)
    return result


def hsv_to_rgb(img: NDArray[np.floating]) -> NDArray[np.uint8]:
    h, s, v = img[:, :, 0], img[:, :, 1], img[:, :, 2]
    h = h * 360.0

    c = v * s
    x = c * (1 - np.abs((h / 60.0) % 2 - 1))
    m = v - c

    r = np.zeros_like(h)
    g = np.zeros_like(h)
    b = np.zeros_like(h)

    mask0 = (h >= 0) & (h < 60)
    mask1 = (h >= 60) & (h < 120)
    mask2 = (h >= 120) & (h < 180)
    mask3 = (h >= 180) & (h < 240)
    mask4 = (h >= 240) & (h < 300)
    mask5 = h >= 300

    r[mask0], g[mask0], b[mask0] = c[mask0], x[mask0], 0
    r[mask1], g[mask1], b[mask1] = x[mask1], c[mask1], 0
    r[mask2], g[mask2], b[mask2] = 0, c[mask2], x[mask2]
    r[mask3], g[mask3], b[mask3] = 0, x[mask3], c[mask3]
    r[mask4], g[mask4], b[mask4] = x[mask4], 0, c[mask4]
    r[mask5], g[mask5], b[mask5] = c[mask5], 0, x[mask5]

    r = ((r + m) * 255).clip(0, 255).astype(np.uint8)
    g = ((g + m) * 255).clip(0, 255).astype(np.uint8)
    b = ((b + m) * 255).clip(0, 255).astype(np.uint8)

    return np.stack([r, g, b], axis=2)


def rgb_to_grayscale(img: NDArray[np.uint8]) -> NDArray[np.uint8]:
    if img.ndim == 2:
        return img.copy()
    return (
        0.2989 * img[:, :, 0].astype(np.float64)
        + 0.5870 * img[:, :, 1].astype(np.float64)
        + 0.1140 * img[:, :, 2].astype(np.float64)
    ).clip(0, 255).astype(np.uint8)


def bounding_box_intersection(
    box1: tuple[int, int, int, int],
    box2: tuple[int, int, int, int],
) -> tuple[int, int, int, int] | None:
    x1, y1, w1, h1 = box1
    x2, y2, w2, h2 = box2
    x_overlap = max(0, min(x1 + w1, x2 + w2) - max(x1, x2))
    y_overlap = max(0, min(y1 + h1, y2 + h2) - max(y1, y2))
    if x_overlap == 0 or y_overlap == 0:
        return None
    ix = max(x1, x2)
    iy = max(y1, y2)
    return (ix, iy, x_overlap, y_overlap)


def bounding_box_union(
    box1: tuple[int, int, int, int],
    box2: tuple[int, int, int, int],
) -> tuple[int, int, int, int]:
    x1, y1, w1, h1 = box1
    x2, y2, w2, h2 = box2
    x_min = min(x1, x2)
    y_min = min(y1, y2)
    x_max = max(x1 + w1, x2 + w2)
    y_max = max(y1 + h1, y2 + h2)
    return (x_min, y_min, x_max - x_min, y_max - y_min)


def bounding_box_iou(
    box1: tuple[int, int, int, int],
    box2: tuple[int, int, int, int],
) -> float:
    inter = bounding_box_intersection(box1, box2)
    if inter is None:
        return 0.0
    _, _, iw, ih = inter
    inter_area = iw * ih
    area1 = box1[2] * box1[3]
    area2 = box2[2] * box2[3]
    union_area = area1 + area2 - inter_area
    if union_area == 0:
        return 0.0
    return inter_area / union_area


def resize_array(
    arr: NDArray[np.uint8],
    width: int,
    height: int,
    method: str = "lanczos",
) -> NDArray[np.uint8]:
    from PIL import Image

    img = Image.fromarray(arr)
    method_map = {
        "nearest": Image.NEAREST,
        "bilinear": Image.BILINEAR,
        "bicubic": Image.BICUBIC,
        "lanczos": Image.LANCZOS,
    }
    resample = method_map.get(method, Image.LANCZOS)
    resized = img.resize((width, height), resample)
    return np.array(resized)
