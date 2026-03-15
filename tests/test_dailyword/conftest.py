import io
from collections.abc import Iterator
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from PIL import Image, ImageChops, ImageEnhance
from syrupy.extensions.image import PNGImageSnapshotExtension

if TYPE_CHECKING:
    from syrupy.types import SerializableData, SerializedData

DIFF_OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent / "snapshot_diffs"


class FuzzyPNGSnapshotExtension(PNGImageSnapshotExtension):
    """PNG snapshot extension with fuzzy pixel-level comparison.

    Handles sub-pixel rendering differences between platforms (macOS vs Linux)
    caused by FreeType anti-aliasing variations.
    """

    pixel_tolerance: int = 2
    pixel_threshold: float = 0.005

    _last_diff_info: dict | None = None
    _diff_counter: int = 0

    def matches(
        self,
        *,
        serialized_data: SerializableData,
        snapshot_data: SerializableData,
    ) -> bool:
        if serialized_data == snapshot_data:
            self._last_diff_info = None
            return True

        try:
            actual_img = Image.open(io.BytesIO(serialized_data))
            expected_img = Image.open(io.BytesIO(snapshot_data))
        except Exception:
            self._last_diff_info = None
            return False

        if actual_img.size != expected_img.size:
            self._last_diff_info = {
                "reason": "size_mismatch",
                "actual_size": actual_img.size,
                "expected_size": expected_img.size,
            }
            return False

        if actual_img.mode != "L":
            actual_img = actual_img.convert("L")
        if expected_img.mode != "L":
            expected_img = expected_img.convert("L")

        diff_img = ImageChops.difference(actual_img, expected_img)
        diff_data = list(diff_img.get_flattened_data())
        total_pixels = len(diff_data)
        exceeding = sum(1 for d in diff_data if d > self.pixel_tolerance)
        max_diff = max(diff_data) if diff_data else 0
        fraction = exceeding / total_pixels if total_pixels else 0.0

        if fraction <= self.pixel_threshold:
            self._last_diff_info = None
            return True

        self._last_diff_info = {
            "reason": "pixel_mismatch",
            "actual_img": actual_img,
            "expected_img": expected_img,
            "diff_img": diff_img,
            "total_pixels": total_pixels,
            "exceeding": exceeding,
            "max_diff": max_diff,
            "fraction": fraction,
        }
        return False

    def diff_lines(
        self,
        serialized_data: SerializedData,
        snapshot_data: SerializedData,
    ) -> Iterator[str]:
        info = self._last_diff_info
        if not info:
            yield from super().diff_lines(serialized_data, snapshot_data)
            return

        if info["reason"] == "size_mismatch":
            yield f"Image size mismatch: expected {info['expected_size']}, got {info['actual_size']}"
            return

        FuzzyPNGSnapshotExtension._diff_counter += 1
        counter = FuzzyPNGSnapshotExtension._diff_counter

        DIFF_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        prefix = f"diff_{counter:03d}"

        expected_path = DIFF_OUTPUT_DIR / f"{prefix}__expected.png"
        actual_path = DIFF_OUTPUT_DIR / f"{prefix}__actual.png"
        diff_path = DIFF_OUTPUT_DIR / f"{prefix}__diff.png"

        info["expected_img"].save(str(expected_path))
        info["actual_img"].save(str(actual_path))
        enhanced_diff = ImageEnhance.Contrast(info["diff_img"]).enhance(10.0)
        enhanced_diff.save(str(diff_path))

        yield "Snapshot image mismatch:"
        yield f"  Image size: {info['actual_img'].size[0]}x{info['actual_img'].size[1]}"
        yield f"  Pixel tolerance: {self.pixel_tolerance} (max per-pixel diff allowed)"
        yield f"  Pixel threshold: {self.pixel_threshold:.2%} (max fraction of mismatched pixels)"
        yield f"  Pixels exceeding tolerance: {info['exceeding']} / {info['total_pixels']} ({info['fraction']:.4%})"
        yield f"  Max pixel difference: {info['max_diff']}"
        yield "  Diff images saved:"
        yield f"    Expected: {expected_path}"
        yield f"    Actual:   {actual_path}"
        yield f"    Diff:     {diff_path}"


@pytest.fixture
def snapshot_png(snapshot):
    return snapshot.use_extension(FuzzyPNGSnapshotExtension)
