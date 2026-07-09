from __future__ import annotations

from dataclasses import dataclass, field, asdict


@dataclass
class VisionConfig:
    default_resize_method: str = "lanczos"
    default_thumbnail_size: tuple[int, int] = (128, 128)
    max_image_size: tuple[int, int] = (8192, 8192)


@dataclass
class DetectionConfig:
    skin_color_lower: tuple[int, int, int] = (0, 20, 70)
    skin_color_upper: tuple[int, int, int] = (50, 150, 255)
    edge_low_threshold: int = 50
    edge_high_threshold: int = 150
    min_text_region_size: int = 50
    dominant_color_count: int = 5
    dominant_color_max_iter: int = 20


@dataclass
class ScreenConfig:
    mock_capture_size: tuple[int, int] = (1920, 1080)
    layout_min_block_size: int = 30
    diff_threshold: float = 0.1
    roi_min_area: int = 200


@dataclass
class Config:
    vision: VisionConfig = field(default_factory=VisionConfig)
    detection: DetectionConfig = field(default_factory=DetectionConfig)
    screen: ScreenConfig = field(default_factory=ScreenConfig)

    def to_dict(self) -> dict:
        return asdict(self)
