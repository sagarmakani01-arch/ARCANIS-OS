"""ArcanisVision - Computer vision system for image processing, object detection, and screen understanding."""

__version__ = "0.1.0"

from .config import Config, VisionConfig, DetectionConfig, ScreenConfig
from .image import ImageProcessor
from .detector import ObjectDetector
from .screen import ScreenAnalyzer
from .utils import (
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

__all__ = [
    "Config",
    "VisionConfig",
    "DetectionConfig",
    "ScreenConfig",
    "ImageProcessor",
    "ObjectDetector",
    "ScreenAnalyzer",
    "compute_mse",
    "compute_ssim",
    "rgb_to_hsv",
    "hsv_to_rgb",
    "rgb_to_grayscale",
    "bounding_box_intersection",
    "bounding_box_union",
    "bounding_box_iou",
    "resize_array",
]
