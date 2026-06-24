from pathlib import Path

import cv2
import numpy as np
import pytest

from flowpilot.screen import ScreenMatcher, ScreenRegion


def test_find_template_returns_screen_coordinates(tmp_path: Path) -> None:
    rng = np.random.default_rng(42)
    template = rng.integers(0, 256, size=(12, 18, 3), dtype=np.uint8)
    screen = np.zeros((80, 120, 3), dtype=np.uint8)
    screen[25:37, 40:58] = template
    template_path = tmp_path / "button.png"
    assert cv2.imwrite(str(template_path), template)

    result = ScreenMatcher().find_template(
        template_path,
        threshold=0.99,
        region=ScreenRegion(left=100, top=200, width=120, height=80),
        screen=screen,
    )

    assert result is not None
    assert result.center == (149, 231)
    assert result.confidence == pytest.approx(1.0)


def test_template_larger_than_screen_is_not_a_match(tmp_path: Path) -> None:
    template = np.zeros((30, 30, 3), dtype=np.uint8)
    template_path = tmp_path / "large.png"
    assert cv2.imwrite(str(template_path), template)

    result = ScreenMatcher().find_template(
        template_path,
        screen=np.zeros((10, 10, 3), dtype=np.uint8),
    )

    assert result is None


def test_threshold_must_be_a_probability(tmp_path: Path) -> None:
    template_path = tmp_path / "template.png"
    assert cv2.imwrite(str(template_path), np.zeros((3, 3, 3), dtype=np.uint8))

    with pytest.raises(ValueError, match="between 0 and 1"):
        ScreenMatcher().find_template(template_path, threshold=1.2)
