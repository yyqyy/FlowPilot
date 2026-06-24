from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import mss
import numpy as np


@dataclass(frozen=True, slots=True)
class ScreenRegion:
    left: int
    top: int
    width: int
    height: int

    def as_mss_monitor(self) -> dict[str, int]:
        return {
            "left": self.left,
            "top": self.top,
            "width": self.width,
            "height": self.height,
        }


@dataclass(frozen=True, slots=True)
class MatchResult:
    left: int
    top: int
    width: int
    height: int
    confidence: float

    @property
    def center(self) -> tuple[int, int]:
        return self.left + self.width // 2, self.top + self.height // 2


class ScreenMatcher:
    def capture(self, region: ScreenRegion | None = None) -> np.ndarray:
        """Capture the virtual desktop or a region as a BGR image."""
        with mss.mss() as capture:
            monitor = region.as_mss_monitor() if region else capture.monitors[0]
            frame = np.asarray(capture.grab(monitor))
        return cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

    def save_capture(self, path: Path, region: ScreenRegion | None = None) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        if not cv2.imwrite(str(path), self.capture(region)):
            raise OSError(f"Could not write screenshot to {path}")

    def find_template(
        self,
        template_path: Path,
        *,
        threshold: float = 0.85,
        region: ScreenRegion | None = None,
        screen: np.ndarray | None = None,
    ) -> MatchResult | None:
        if not 0 <= threshold <= 1:
            raise ValueError("Threshold must be between 0 and 1.")
        template = cv2.imread(str(template_path), cv2.IMREAD_COLOR)
        if template is None:
            raise FileNotFoundError(f"Template image could not be read: {template_path}")

        haystack = screen if screen is not None else self.capture(region)
        if haystack.ndim != 3 or haystack.shape[2] != 3:
            raise ValueError("Screen image must be a BGR image with three channels.")

        template_height, template_width = template.shape[:2]
        screen_height, screen_width = haystack.shape[:2]
        if template_width > screen_width or template_height > screen_height:
            return None

        scores = cv2.matchTemplate(haystack, template, cv2.TM_CCOEFF_NORMED)
        _, confidence, _, location = cv2.minMaxLoc(scores)
        if confidence < threshold:
            return None

        offset_x = region.left if region else 0
        offset_y = region.top if region else 0
        return MatchResult(
            left=location[0] + offset_x,
            top=location[1] + offset_y,
            width=template_width,
            height=template_height,
            confidence=float(confidence),
        )

