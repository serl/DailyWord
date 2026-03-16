import io

from PIL import Image, PngImagePlugin

import tests.test_dailyword.conftest as conftest_mod
from tests.test_dailyword.conftest import FuzzyPNGSnapshotExtension


def make_png(width, height, color=200) -> bytes:
    img = Image.new("L", (width, height), color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


class TestMatches:
    def setup_method(self):
        self.ext = FuzzyPNGSnapshotExtension()

    def test_identical_images_match(self):
        data = make_png(10, 10)
        assert self.ext.matches(serialized_data=data, snapshot_data=data) is True
        assert self.ext._last_diff_info is None

    def test_different_size_does_not_match(self):
        small = make_png(10, 10)
        large = make_png(20, 20)
        assert self.ext.matches(serialized_data=small, snapshot_data=large) is False
        assert self.ext._last_diff_info["reason"] == "size_mismatch"
        assert self.ext._last_diff_info["actual_size"] == (10, 10)
        assert self.ext._last_diff_info["expected_size"] == (20, 20)

    def test_small_pixel_diff_within_tolerance_matches(self):
        """Pixels differing by <= pixel_tolerance (2) should match."""
        img = Image.new("L", (10, 10), 200)
        img.putpixel((0, 0), 202)  # diff of 2, exactly at tolerance
        img.putpixel((1, 0), 199)  # diff of 1
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        modified = buf.getvalue()

        original = make_png(10, 10, 200)
        assert (
            self.ext.matches(serialized_data=modified, snapshot_data=original) is True
        )
        assert self.ext._last_diff_info is None

    def test_pixel_diff_exceeding_tolerance_but_below_threshold_matches(self):
        """Many pixels differ by > tolerance, but fraction <= pixel_threshold (0.5%)."""
        # 100x100 = 10000 pixels. 0.5% = 50 pixels.
        # Change 40 pixels (0.4%) by more than tolerance.
        img = Image.new("L", (100, 100), 200)
        for i in range(40):
            img.putpixel((i, 0), 210)  # diff of 10, exceeds tolerance of 2
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        modified = buf.getvalue()

        original = make_png(100, 100, 200)
        assert (
            self.ext.matches(serialized_data=modified, snapshot_data=original) is True
        )

    def test_pixel_diff_exceeding_threshold_does_not_match(self):
        """Large area differs significantly -> False."""
        # 10x10 = 100 pixels. Change 50 pixels (50%) by more than tolerance.
        img = Image.new("L", (10, 10), 200)
        for y in range(5):
            for x in range(10):
                img.putpixel((x, y), 100)  # diff of 100
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        modified = buf.getvalue()

        original = make_png(10, 10, 200)
        assert (
            self.ext.matches(serialized_data=modified, snapshot_data=original) is False
        )
        info = self.ext._last_diff_info
        assert info["reason"] == "pixel_mismatch"
        assert info["total_pixels"] == 100
        assert info["exceeding"] == 50
        assert info["max_diff"] == 100
        assert info["fraction"] == 0.5

    def test_invalid_image_data_does_not_match(self):
        valid = make_png(10, 10)
        invalid = b"not an image at all"
        assert self.ext.matches(serialized_data=valid, snapshot_data=invalid) is False
        assert self.ext._last_diff_info is None

    def test_non_grayscale_images_converted(self):
        """RGB images that are otherwise identical should match (L-mode conversion path)."""
        # Build two PNGs with identical pixel content but different raw bytes
        # to avoid the early identity shortcut and exercise the L-mode conversion.
        img1 = Image.new("RGB", (10, 10), (200, 200, 200))
        img2 = Image.new("RGB", (10, 10), (200, 200, 200))
        meta = PngImagePlugin.PngInfo()
        meta.add_text("Comment", "force different bytes")
        buf1 = io.BytesIO()
        img1.save(buf1, format="PNG")
        buf2 = io.BytesIO()
        img2.save(buf2, format="PNG", pnginfo=meta)

        data1 = buf1.getvalue()
        data2 = buf2.getvalue()
        assert data1 != data2  # sanity: bytes differ
        assert self.ext.matches(serialized_data=data1, snapshot_data=data2) is True


class TestDiffLines:
    def setup_method(self):
        self.ext = FuzzyPNGSnapshotExtension()

    def test_diff_lines_no_info_delegates_to_super(self):
        """When _last_diff_info is None, delegates to parent (doesn't crash)."""
        self.ext._last_diff_info = None
        data = make_png(10, 10)
        lines = list(self.ext.diff_lines(data, data))
        # Parent should produce some output (at minimum not crash)
        assert isinstance(lines, list)

    def test_diff_lines_size_mismatch(self):
        small = make_png(10, 10)
        large = make_png(20, 20)
        self.ext.matches(serialized_data=small, snapshot_data=large)

        lines = list(self.ext.diff_lines(small, large))
        assert any("size mismatch" in line.lower() for line in lines)
        assert any("(10, 10)" in line for line in lines)
        assert any("(20, 20)" in line for line in lines)

    def test_diff_lines_pixel_mismatch_saves_images(self, tmp_path, monkeypatch):
        monkeypatch.setattr(conftest_mod, "DIFF_OUTPUT_DIR", tmp_path)
        # Reset counter for predictable file names
        FuzzyPNGSnapshotExtension._diff_counter = 0

        img = Image.new("L", (10, 10), 200)
        for y in range(5):
            for x in range(10):
                img.putpixel((x, y), 100)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        modified = buf.getvalue()
        original = make_png(10, 10, 200)

        self.ext.matches(serialized_data=modified, snapshot_data=original)
        lines = list(self.ext.diff_lines(modified, original))

        assert any("mismatch" in line.lower() for line in lines)
        assert any("50 / 100" in line for line in lines)

        assert (tmp_path / "diff_001__expected.png").exists()
        assert (tmp_path / "diff_001__actual.png").exists()
        assert (tmp_path / "diff_001__diff.png").exists()
        assert FuzzyPNGSnapshotExtension._diff_counter == 1
