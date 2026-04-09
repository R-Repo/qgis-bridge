import xml.etree.ElementTree as ET
import pytest
from qgis_bridge._style import (
    make_single_symbol_qml,
    make_graduated_qml,
    make_categorized_qml,
    _interpolate_colors,
)


def _parse(qml: str) -> ET.Element:
    return ET.fromstring(qml)


class TestSingleSymbol:
    def test_produces_valid_xml(self):
        root = _parse(make_single_symbol_qml())
        assert root.tag == "qgis"

    def test_renderer_type(self):
        root = _parse(make_single_symbol_qml())
        renderer = root.find("renderer-v2")
        assert renderer.get("type") == "singleSymbol"

    def test_has_one_symbol(self):
        root = _parse(make_single_symbol_qml())
        symbols = root.findall(".//symbol")
        assert len(symbols) == 1

    def test_opacity(self):
        root = _parse(make_single_symbol_qml(opacity=0.5))
        prop = root.find(".//prop[@k='color']")
        # alpha channel should be ~127
        alpha = int(prop.get("v").split(",")[3])
        assert 125 <= alpha <= 129


class TestGraduated:
    def test_creates_correct_class_count(self):
        values = list(range(100))
        root = _parse(make_graduated_qml(values, "score", n_classes=5))
        ranges = root.findall(".//range")
        assert len(ranges) == 5

    def test_attr_matches_column(self):
        root = _parse(make_graduated_qml([1, 2, 3], "val"))
        renderer = root.find("renderer-v2")
        assert renderer.get("attr") == "val"

    def test_falls_back_to_single_when_all_same(self):
        root = _parse(make_graduated_qml([5, 5, 5], "x"))
        renderer = root.find("renderer-v2")
        assert renderer.get("type") == "singleSymbol"

    def test_empty_values_falls_back(self):
        root = _parse(make_graduated_qml([], "x"))
        renderer = root.find("renderer-v2")
        assert renderer.get("type") == "singleSymbol"

    def test_ranges_cover_full_extent(self):
        values = [10.0, 20.0, 30.0, 40.0, 50.0]
        root = _parse(make_graduated_qml(values, "v", n_classes=3))
        ranges = root.findall(".//range")
        lower = float(ranges[0].get("lower"))
        upper = float(ranges[-1].get("upper"))
        assert lower == pytest.approx(10.0)
        assert upper == pytest.approx(50.0)


class TestCategorized:
    def test_creates_category_per_unique_value(self):
        cats = ["A", "B", "C", "A", "B"]
        root = _parse(make_categorized_qml(cats, "type"))
        categories = root.findall(".//category")
        assert len(categories) == 3

    def test_attr_matches_column(self):
        root = _parse(make_categorized_qml(["X"], "col"))
        renderer = root.find("renderer-v2")
        assert renderer.get("attr") == "col"

    def test_empty_categories_falls_back(self):
        root = _parse(make_categorized_qml([], "x"))
        renderer = root.find("renderer-v2")
        assert renderer.get("type") == "singleSymbol"

    def test_categories_are_sorted(self):
        cats = ["C", "A", "B"]
        root = _parse(make_categorized_qml(cats, "x"))
        values = [c.get("value") for c in root.findall(".//category")]
        assert values == ["A", "B", "C"]


class TestColorInterpolation:
    def test_single_color(self):
        colors = _interpolate_colors("RdYlGn", 1)
        assert len(colors) == 1

    def test_correct_count(self):
        colors = _interpolate_colors("Blues", 7)
        assert len(colors) == 7

    def test_unknown_ramp_falls_back(self):
        colors = _interpolate_colors("NonExistent", 3)
        assert len(colors) == 3
