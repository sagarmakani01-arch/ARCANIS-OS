import io
import os
import tempfile

import numpy as np
import pytest
from PIL import Image

from arcanis_vision.config import Config, VisionConfig, DetectionConfig, ScreenConfig
from arcanis_vision.image import ImageProcessor
from arcanis_vision.detector import ObjectDetector
from arcanis_vision.screen import ScreenAnalyzer
from arcanis_vision.utils import (
    compute_mse,
    compute_ssim,
    rgb_to_hsv,
    hsv_to_rgb,
    rgb_to_grayscale,
    bounding_box_intersection,
    bounding_box_union,
    bounding_box_iou,
    resize_array,
)


def _make_rgb_image(width=100, height=100, color=(128, 64, 32)):
    arr = np.zeros((height, width, 3), dtype=np.uint8)
    arr[:, :] = color
    return arr


def _make_gradient_image(width=100, height=100):
    arr = np.zeros((height, width, 3), dtype=np.uint8)
    for i in range(height):
        for j in range(width):
            arr[i, j] = [int(i / height * 255), int(j / width * 255), 128]
    return arr


def _make_pil_image(width=100, height=100, color=(128, 64, 32)):
    return Image.fromarray(_make_rgb_image(width, height, color))


class TestConfig:
    def test_vision_config_defaults(self):
        cfg = VisionConfig()
        assert cfg.default_resize_method == "lanczos"
        assert cfg.default_thumbnail_size == (128, 128)
        assert cfg.max_image_size == (8192, 8192)

    def test_detection_config_defaults(self):
        cfg = DetectionConfig()
        assert cfg.skin_color_lower == (0, 20, 70)
        assert cfg.skin_color_upper == (50, 150, 255)
        assert cfg.edge_low_threshold == 50
        assert cfg.edge_high_threshold == 150
        assert cfg.dominant_color_count == 5

    def test_screen_config_defaults(self):
        cfg = ScreenConfig()
        assert cfg.mock_capture_size == (1920, 1080)
        assert cfg.layout_min_block_size == 30
        assert cfg.diff_threshold == 0.1

    def test_config_creation(self):
        cfg = Config()
        assert isinstance(cfg.vision, VisionConfig)
        assert isinstance(cfg.detection, DetectionConfig)
        assert isinstance(cfg.screen, ScreenConfig)

    def test_config_to_dict(self):
        cfg = Config()
        d = cfg.to_dict()
        assert "vision" in d
        assert "detection" in d
        assert "screen" in d
        assert d["vision"]["default_resize_method"] == "lanczos"

    def test_custom_config(self):
        cfg = Config(
            vision=VisionConfig(default_thumbnail_size=(64, 64)),
            detection=DetectionConfig(dominant_color_count=3),
        )
        assert cfg.vision.default_thumbnail_size == (64, 64)
        assert cfg.detection.dominant_color_count == 3


class TestUtils:
    def test_compute_mse_identical(self):
        arr = _make_rgb_image()
        mse = compute_mse(arr.astype(np.float64), arr.astype(np.float64))
        assert mse == 0.0

    def test_compute_mse_different(self):
        a = np.zeros((10, 10, 3), dtype=np.float64)
        b = np.ones((10, 10, 3), dtype=np.float64) * 255
        mse = compute_mse(a, b)
        assert mse > 0

    def test_compute_mse_shape_mismatch(self):
        a = np.zeros((10, 10, 3), dtype=np.float64)
        b = np.zeros((20, 20, 3), dtype=np.float64)
        with pytest.raises(ValueError):
            compute_mse(a, b)

    def test_compute_ssim_identical(self):
        arr = _make_rgb_image().astype(np.float64)
        ssim = compute_ssim(arr, arr)
        assert ssim > 0.99

    def test_compute_ssim_different(self):
        a = np.zeros((30, 30), dtype=np.float64)
        b = np.ones((30, 30), dtype=np.float64) * 255
        ssim = compute_ssim(a, b)
        assert ssim < 0.5

    def test_compute_ssim_shape_mismatch(self):
        a = np.zeros((10, 10), dtype=np.float64)
        b = np.zeros((20, 20), dtype=np.float64)
        with pytest.raises(ValueError):
            compute_ssim(a, b)

    def test_compute_ssim_rgb(self):
        arr = _make_gradient_image().astype(np.float64)
        ssim = compute_ssim(arr, arr)
        assert ssim > 0.99

    def test_rgb_to_hsv(self):
        arr = _make_rgb_image(10, 10, (255, 0, 0))
        hsv = rgb_to_hsv(arr)
        assert hsv.shape == (10, 10, 3)
        assert 0 <= hsv[:, :, 0].min() <= hsv[:, :, 0].max() <= 1.0
        assert 0 <= hsv[:, :, 1].min() <= hsv[:, :, 1].max() <= 1.0
        assert 0 <= hsv[:, :, 2].min() <= hsv[:, :, 2].max() <= 1.0

    def test_hsv_to_rgb(self):
        hsv = np.zeros((10, 10, 3), dtype=np.float64)
        hsv[:, :, 0] = 0.0
        hsv[:, :, 1] = 1.0
        hsv[:, :, 2] = 1.0
        rgb = hsv_to_rgb(hsv)
        assert rgb.shape == (10, 10, 3)
        assert rgb.dtype == np.uint8
        assert np.allclose(rgb[:, :, 0], 255)
        assert np.allclose(rgb[:, :, 1], 0)
        assert np.allclose(rgb[:, :, 2], 0)

    def test_rgb_to_grayscale(self):
        arr = _make_rgb_image(10, 10, (100, 150, 200))
        gray = rgb_to_grayscale(arr)
        assert gray.shape == (10, 10)
        assert gray.dtype == np.uint8

    def test_rgb_to_grayscale_already_gray(self):
        arr = np.full((10, 10), 128, dtype=np.uint8)
        gray = rgb_to_grayscale(arr)
        np.testing.assert_array_equal(gray, arr)

    def test_bounding_box_intersection(self):
        box1 = (0, 0, 10, 10)
        box2 = (5, 5, 10, 10)
        inter = bounding_box_intersection(box1, box2)
        assert inter is not None
        assert inter == (5, 5, 5, 5)

    def test_bounding_box_intersection_none(self):
        box1 = (0, 0, 10, 10)
        box2 = (20, 20, 10, 10)
        inter = bounding_box_intersection(box1, box2)
        assert inter is None

    def test_bounding_box_union(self):
        box1 = (0, 0, 10, 10)
        box2 = (5, 5, 10, 10)
        u = bounding_box_union(box1, box2)
        assert u == (0, 0, 15, 15)

    def test_bounding_box_iou_perfect(self):
        box = (0, 0, 10, 10)
        iou = bounding_box_iou(box, box)
        assert abs(iou - 1.0) < 1e-6

    def test_bounding_box_iou_none(self):
        box1 = (0, 0, 10, 10)
        box2 = (50, 50, 10, 10)
        iou = bounding_box_iou(box1, box2)
        assert iou == 0.0

    def test_bounding_box_iou_partial(self):
        box1 = (0, 0, 10, 10)
        box2 = (5, 0, 10, 10)
        iou = bounding_box_iou(box1, box2)
        assert 0 < iou < 1

    def test_resize_array(self):
        arr = _make_rgb_image(50, 50)
        resized = resize_array(arr, 25, 25)
        assert resized.shape == (25, 25, 3)

    def test_resize_array_methods(self):
        arr = _make_rgb_image(50, 50)
        for method in ["nearest", "bilinear", "bicubic", "lanczos"]:
            resized = resize_array(arr, 25, 25, method=method)
            assert resized.shape == (25, 25, 3)


class TestImageProcessor:
    def test_load_from_bytes(self):
        img = _make_pil_image(50, 50)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        data = buf.getvalue()
        processor = ImageProcessor()
        loaded = processor.load_from_bytes(data)
        assert loaded.size == (50, 50)

    def test_load_from_numpy(self):
        arr = _make_rgb_image(50, 50)
        processor = ImageProcessor()
        img = processor.load_from_numpy(arr)
        assert img.size == (50, 50)
        assert img.mode == "RGB"

    def test_to_numpy(self):
        img = _make_pil_image(50, 50)
        processor = ImageProcessor()
        arr = processor.to_numpy(img)
        assert arr.shape == (50, 50, 3)
        assert arr.dtype == np.uint8

    def test_resize(self):
        img = _make_pil_image(100, 100)
        processor = ImageProcessor()
        resized = processor.resize(img, 50, 50)
        assert resized.size == (50, 50)

    def test_resize_methods(self):
        img = _make_pil_image(100, 100)
        processor = ImageProcessor()
        for method in ["nearest", "bilinear", "bicubic", "lanczos"]:
            resized = processor.resize(img, 50, 50, method=method)
            assert resized.size == (50, 50)

    def test_crop(self):
        img = _make_pil_image(100, 100)
        processor = ImageProcessor()
        cropped = processor.crop(img, 10, 20, 30, 40)
        assert cropped.size == (30, 40)

    def test_rotate(self):
        img = _make_pil_image(100, 50)
        processor = ImageProcessor()
        rotated = processor.rotate(img, 90)
        assert rotated.size[0] > 0
        assert rotated.size[1] > 0

    def test_rotate_no_expand(self):
        img = _make_pil_image(100, 100)
        processor = ImageProcessor()
        rotated = processor.rotate(img, 45, expand=False)
        assert rotated.size == (100, 100)

    def test_flip_horizontal(self):
        img = _make_pil_image(100, 50)
        processor = ImageProcessor()
        flipped = processor.flip_horizontal(img)
        assert flipped.size == (100, 50)

    def test_flip_vertical(self):
        img = _make_pil_image(100, 50)
        processor = ImageProcessor()
        flipped = processor.flip_vertical(img)
        assert flipped.size == (100, 50)

    def test_convert_format_png(self):
        img = _make_pil_image(50, 50)
        processor = ImageProcessor()
        data = processor.convert_format(img, "PNG")
        assert len(data) > 0
        assert data[:4] == b"\x89PNG"

    def test_convert_format_jpeg(self):
        img = _make_pil_image(50, 50)
        processor = ImageProcessor()
        data = processor.convert_format(img, "JPEG")
        assert len(data) > 0

    def test_apply_filter_blur(self):
        img = _make_pil_image(50, 50)
        processor = ImageProcessor()
        blurred = processor.apply_filter(img, "blur")
        assert blurred.size == img.size

    def test_apply_filter_sharpen(self):
        img = _make_pil_image(50, 50)
        processor = ImageProcessor()
        sharpened = processor.apply_filter(img, "sharpen")
        assert sharpened.size == img.size

    def test_apply_filter_edge_detect(self):
        img = _make_pil_image(50, 50)
        processor = ImageProcessor()
        edges = processor.apply_filter(img, "edge_detect")
        assert edges.size == img.size

    def test_apply_filter_invalid(self):
        img = _make_pil_image(50, 50)
        processor = ImageProcessor()
        with pytest.raises(ValueError):
            processor.apply_filter(img, "nonexistent")

    def test_thumbnail_default(self):
        img = _make_pil_image(200, 300)
        processor = ImageProcessor()
        thumb = processor.thumbnail(img)
        assert thumb.size[0] <= 128
        assert thumb.size[1] <= 128

    def test_thumbnail_custom(self):
        img = _make_pil_image(200, 300)
        processor = ImageProcessor()
        thumb = processor.thumbnail(img, max_size=(64, 64))
        assert thumb.size[0] <= 64
        assert thumb.size[1] <= 64

    def test_extract_exif_no_exif(self):
        img = _make_pil_image(50, 50)
        processor = ImageProcessor()
        exif = processor.extract_exif(img)
        assert isinstance(exif, dict)

    def test_numpy_blur(self):
        arr = _make_rgb_image(20, 20)
        processor = ImageProcessor()
        blurred = processor.numpy_blur(arr, radius=2)
        assert blurred.shape == arr.shape
        assert blurred.dtype == np.uint8

    def test_numpy_blur_grayscale(self):
        arr = np.random.randint(0, 256, (20, 20), dtype=np.uint8)
        processor = ImageProcessor()
        blurred = processor.numpy_blur(arr, radius=2)
        assert blurred.shape == arr.shape

    def test_numpy_edge_detect(self):
        arr = _make_gradient_image(20, 20)
        processor = ImageProcessor()
        edges = processor.numpy_edge_detect(arr)
        assert edges.shape == (20, 20)
        assert edges.dtype == np.uint8

    def test_numpy_sharpen(self):
        arr = _make_rgb_image(20, 20)
        processor = ImageProcessor()
        sharpened = processor.numpy_sharpen(arr)
        assert sharpened.shape == arr.shape
        assert sharpened.dtype == np.uint8

    def test_load_from_file(self):
        img = _make_pil_image(50, 50)
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            img.save(f.name)
            path = f.name
        try:
            processor = ImageProcessor()
            loaded = processor.load_from_file(path)
            assert loaded.size == (50, 50)
        finally:
            os.remove(path)


class TestObjectDetector:
    def test_detect_faces_returns_list(self):
        arr = np.zeros((80, 80, 3), dtype=np.uint8)
        arr[20:60, 20:60] = [180, 140, 100]
        detector = ObjectDetector()
        faces = detector.detect_faces(arr)
        assert isinstance(faces, list)

    def test_detect_faces_non_rgb_raises(self):
        arr = np.zeros((80, 80), dtype=np.uint8)
        detector = ObjectDetector()
        with pytest.raises(ValueError):
            detector.detect_faces(arr)

    def test_detect_faces_with_skin_region(self):
        arr = np.zeros((100, 100, 3), dtype=np.uint8)
        arr[30:70, 30:70] = [170, 130, 90]
        detector = ObjectDetector()
        faces = detector.detect_faces(arr)
        assert len(faces) >= 0
        if faces:
            assert "bbox" in faces[0]
            assert "confidence" in faces[0]

    def test_detect_edges(self):
        arr = _make_gradient_image(30, 30)
        detector = ObjectDetector()
        edges = detector.detect_edges(arr)
        assert edges.shape == (30, 30)
        assert edges.dtype == np.uint8
        assert edges.max() <= 255

    def test_detect_edges_custom_threshold(self):
        arr = _make_gradient_image(30, 30)
        detector = ObjectDetector()
        edges = detector.detect_edges(arr, low_threshold=10, high_threshold=50)
        assert edges.shape == (30, 30)

    def test_detect_text_regions(self):
        arr = _make_rgb_image(60, 20, (255, 255, 255))
        arr[5:15, 5:55] = [0, 0, 0]
        detector = ObjectDetector()
        regions = detector.detect_text_regions(arr)
        assert isinstance(regions, list)

    def test_detect_colors(self):
        arr = np.zeros((50, 50, 3), dtype=np.uint8)
        arr[:25, :] = [255, 0, 0]
        arr[25:, :] = [0, 0, 255]
        detector = ObjectDetector()
        colors = detector.detect_colors(arr, n_colors=2)
        assert len(colors) == 2
        assert all("color" in c and "percentage" in c for c in colors)
        total_pct = sum(c["percentage"] for c in colors)
        assert abs(total_pct - 1.0) < 0.01

    def test_detect_colors_default(self):
        arr = _make_rgb_image(50, 50, (100, 200, 50))
        detector = ObjectDetector()
        colors = detector.detect_colors(arr)
        assert len(colors) == 5

    def test_morphological_operations(self):
        arr = np.zeros((20, 20), dtype=np.uint8)
        arr[5:15, 5:15] = 1
        detector = ObjectDetector()
        kernel = np.ones((3, 3), dtype=np.uint8)
        opened = detector._morphological_open(arr, kernel)
        closed = detector._morphological_close(arr, kernel)
        assert opened.shape == arr.shape
        assert closed.shape == arr.shape

    def test_connected_components(self):
        mask = np.zeros((20, 20), dtype=np.uint8)
        mask[2:5, 2:5] = 1
        mask[10:13, 10:13] = 1
        detector = ObjectDetector()
        bboxes = detector._connected_components(mask)
        assert len(bboxes) == 2

    def test_adaptive_threshold(self):
        gray = np.random.randint(0, 256, (20, 20), dtype=np.uint8)
        detector = ObjectDetector()
        binary = detector._adaptive_threshold(gray, block_size=5)
        assert binary.shape == gray.shape
        assert set(np.unique(binary)).issubset({0, 1})

    def test_sobel_gradients(self):
        gray = np.random.randint(0, 256, (20, 20), dtype=np.uint8)
        detector = ObjectDetector()
        gx, gy = detector._sobel_gradients(gray)
        assert gx.shape == gray.shape
        assert gy.shape == gray.shape


class TestScreenAnalyzer:
    def test_capture_screen_full(self):
        analyzer = ScreenAnalyzer()
        arr = analyzer.capture_screen()
        assert arr.ndim == 3
        assert arr.shape[2] == 3

    def test_capture_screen_region(self):
        analyzer = ScreenAnalyzer()
        arr = analyzer.capture_screen(region=(100, 100, 200, 200))
        assert arr.shape == (200, 200, 3)

    def test_analyze_layout(self):
        arr = np.zeros((100, 100, 3), dtype=np.uint8)
        arr[10:40, 10:90] = 255
        arr[50:80, 10:50] = 200
        analyzer = ScreenAnalyzer()
        layout = analyzer.analyze_layout(arr)
        assert "elements" in layout
        assert "image_size" in layout
        assert layout["image_size"] == (100, 100)
        assert isinstance(layout["elements"], list)

    def test_compare_screenshots_identical(self):
        arr = _make_rgb_image(50, 50)
        analyzer = ScreenAnalyzer()
        result = analyzer.compare_screenshots(arr, arr)
        assert result["mse"] == 0.0
        assert result["changed_percentage"] == 0.0
        assert result["diff_map"].shape == (50, 50)

    def test_compare_screenshots_different(self):
        a = np.zeros((50, 50, 3), dtype=np.uint8)
        b = np.ones((50, 50, 3), dtype=np.uint8) * 255
        analyzer = ScreenAnalyzer()
        result = analyzer.compare_screenshots(a, b)
        assert result["mse"] > 0
        assert result["changed_percentage"] > 0

    def test_compare_screenshots_shape_mismatch(self):
        a = np.zeros((50, 50, 3), dtype=np.uint8)
        b = np.zeros((100, 100, 3), dtype=np.uint8)
        analyzer = ScreenAnalyzer()
        with pytest.raises(ValueError):
            analyzer.compare_screenshots(a, b)

    def test_extract_roi(self):
        arr = np.zeros((100, 100, 3), dtype=np.uint8)
        arr[10:30, 10:30] = [255, 0, 0]
        arr[50:80, 50:80] = [0, 0, 255]
        analyzer = ScreenAnalyzer()
        rois = analyzer.extract_roi(arr, min_area=100)
        assert isinstance(rois, list)
        for roi in rois:
            assert "bbox" in roi
            assert "area" in roi
            assert "mean_color" in roi

    def test_extract_roi_default_min_area(self):
        arr = np.zeros((100, 100, 3), dtype=np.uint8)
        arr[10:50, 10:50] = [128, 128, 128]
        analyzer = ScreenAnalyzer()
        rois = analyzer.extract_roi(arr)
        assert isinstance(rois, list)

    def test_threshold(self):
        gray = np.array([[50, 150], [200, 100]], dtype=np.uint8)
        analyzer = ScreenAnalyzer()
        binary = analyzer._threshold(gray, threshold=128)
        expected = np.array([[1, 0], [0, 1]], dtype=np.uint8)
        np.testing.assert_array_equal(binary, expected)

    def test_dilate(self):
        mask = np.zeros((10, 10), dtype=np.uint8)
        mask[4, 4] = 1
        analyzer = ScreenAnalyzer()
        kernel = np.ones((3, 3), dtype=np.uint8)
        dilated = analyzer._dilate(mask, kernel)
        assert dilated[3:6, 3:6].all()
        assert dilated.sum() > 1

    def test_find_blocks(self):
        mask = np.zeros((20, 20), dtype=np.uint8)
        mask[2:5, 2:5] = 1
        mask[10:15, 10:15] = 1
        analyzer = ScreenAnalyzer()
        blocks = analyzer._find_blocks(mask)
        assert len(blocks) == 2


class TestLoadFromBytes:
    def test_roundtrip_png(self):
        img = _make_pil_image(50, 50)
        processor = ImageProcessor()
        data = processor.convert_format(img, "PNG")
        loaded = processor.load_from_bytes(data)
        assert loaded.size == img.size

    def test_roundtrip_jpeg(self):
        img = _make_pil_image(50, 50)
        processor = ImageProcessor()
        data = processor.convert_format(img, "JPEG")
        loaded = processor.load_from_bytes(data)
        assert loaded.size == img.size


class TestIntegration:
    def test_full_pipeline(self):
        arr = _make_gradient_image(200, 200)
        processor = ImageProcessor()
        detector = ObjectDetector()

        img = processor.load_from_numpy(arr)
        resized = processor.resize(img, 100, 100)
        blurred = processor.apply_filter(resized, "blur")
        edges = processor.apply_filter(blurred, "edge_detect")
        edges_arr = processor.to_numpy(edges)

        assert edges_arr.shape == (100, 100, 3)

        faces = detector.detect_faces(processor.to_numpy(resized))
        assert isinstance(faces, list)

        colors = detector.detect_colors(processor.to_numpy(resized), n_colors=3)
        assert len(colors) == 3

    def test_screen_pipeline(self):
        analyzer = ScreenAnalyzer()
        arr1 = analyzer.capture_screen()
        arr2 = analyzer.capture_screen()

        comparison = analyzer.compare_screenshots(arr1, arr2)
        assert "mse" in comparison
        assert "changed_percentage" in comparison

        layout = analyzer.analyze_layout(arr1)
        assert len(layout["elements"]) >= 0

        rois = analyzer.extract_roi(arr1)
        assert isinstance(rois, list)
