"""
QML style file generation.

Produces minimal valid QGIS QML XML for common vector styling cases:
  - Single symbol (no color_by)
  - Graduated renderer (numeric column)
  - Categorized renderer (string/categorical column)

No dependencies beyond stdlib.
"""

from xml.etree.ElementTree import Element, SubElement, tostring

# Default color ramps — each is a list of (r, g, b) tuples.
_COLOR_RAMPS = {
    "RdYlGn": [
        (215, 25, 28), (253, 174, 97), (255, 255, 191),
        (166, 217, 106), (26, 150, 65),
    ],
    "Blues": [
        (239, 243, 255), (189, 215, 231), (107, 174, 214),
        (49, 130, 189), (8, 81, 156),
    ],
    "Reds": [
        (254, 229, 217), (252, 174, 145), (251, 106, 74),
        (222, 45, 38), (165, 15, 21),
    ],
    "Viridis": [
        (68, 1, 84), (59, 82, 139), (33, 145, 140),
        (94, 201, 98), (253, 231, 37),
    ],
    "Greys": [
        (247, 247, 247), (204, 204, 204), (150, 150, 150),
        (99, 99, 99), (37, 37, 37),
    ],
}

_DEFAULT_FILL = (70, 130, 180)  # steel blue
_DEFAULT_STROKE = (50, 50, 50)


def _rgb(color: tuple[int, int, int], alpha: int = 255) -> str:
    return f"{color[0]},{color[1]},{color[2]},{alpha}"


def _interpolate_colors(
    ramp_name: str, n: int,
) -> list[tuple[int, int, int]]:
    """Pick n evenly spaced colors from a named ramp."""
    stops = _COLOR_RAMPS.get(ramp_name, _COLOR_RAMPS["RdYlGn"])
    if n <= 1:
        return [stops[len(stops) // 2]]
    result = []
    for i in range(n):
        t = i / (n - 1)
        pos = t * (len(stops) - 1)
        lo = int(pos)
        hi = min(lo + 1, len(stops) - 1)
        frac = pos - lo
        r = int(stops[lo][0] + frac * (stops[hi][0] - stops[lo][0]))
        g = int(stops[lo][1] + frac * (stops[hi][1] - stops[lo][1]))
        b = int(stops[lo][2] + frac * (stops[hi][2] - stops[lo][2]))
        result.append((r, g, b))
    return result


_SYMBOL_CLASS = {
    "marker": "SimpleMarker",
    "line": "SimpleLine",
    "fill": "SimpleFill",
}

_SYMBOL_PROPS = {
    "marker": {
        "color": None, "outline_color": None,
        "size": "3", "name": "circle",
    },
    "line": {
        "line_color": None, "line_width": "0.5",
    },
    "fill": {
        "color": None, "outline_color": None,
        "outline_width": "0.26", "style": "solid",
    },
}


def _make_symbol_element(
    parent: Element, color: tuple[int, int, int], alpha: int = 255,
    name: str = "0", symbol_type: str = "fill",
) -> Element:
    """Create a minimal QGIS symbol element."""
    sym = SubElement(parent, "symbol", type=symbol_type, name=name, alpha="1")
    cls = _SYMBOL_CLASS.get(symbol_type, "SimpleFill")
    layer = SubElement(sym, "layer", {"class": cls, "pass": "0"})
    template = _SYMBOL_PROPS.get(symbol_type, _SYMBOL_PROPS["fill"])
    for k, v in template.items():
        if v is None:
            v = _rgb(color, alpha) if "outline" not in k else _rgb(_DEFAULT_STROKE)
        SubElement(layer, "prop", k=k, v=v)
    return sym


def _qgis_root(renderer: Element) -> Element:
    """Wrap a renderer element in the required <qgis> root."""
    root = Element("qgis")
    root.append(renderer)
    return root


def _to_xml_string(root: Element) -> str:
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + tostring(
        root, encoding="unicode",
    )


def make_single_symbol_qml(
    opacity: float = 1.0, symbol_type: str = "fill",
) -> str:
    """Generate QML for a single-symbol renderer."""
    renderer = Element("renderer-v2", type="singleSymbol")
    symbols = SubElement(renderer, "symbols")
    alpha = int(opacity * 255)
    _make_symbol_element(symbols, _DEFAULT_FILL, alpha, symbol_type=symbol_type)
    return _to_xml_string(_qgis_root(renderer))


def make_graduated_qml(
    values: list[float],
    column: str,
    n_classes: int = 5,
    color_ramp: str = "RdYlGn",
    opacity: float = 1.0,
    symbol_type: str = "fill",
) -> str:
    """Generate QML for a graduated renderer with equal-interval breaks."""
    if not values:
        return make_single_symbol_qml(opacity, symbol_type)
    vmin, vmax = min(values), max(values)
    n = min(n_classes, len(set(values)))
    if n < 2 or vmin == vmax:
        return make_single_symbol_qml(opacity, symbol_type)

    colors = _interpolate_colors(color_ramp, n)
    alpha = int(opacity * 255)
    step = (vmax - vmin) / n

    renderer = Element("renderer-v2", type="graduatedSymbol", attr=column)
    symbols = SubElement(renderer, "symbols")
    ranges = SubElement(renderer, "ranges")

    for i in range(n):
        lo = vmin + i * step
        hi = vmin + (i + 1) * step
        sym_name = str(i)
        _make_symbol_element(
            symbols, colors[i], alpha, name=sym_name, symbol_type=symbol_type,
        )
        SubElement(ranges, "range", {
            "lower": f"{lo:.6f}",
            "upper": f"{hi:.6f}",
            "symbol": sym_name,
            "label": f"{lo:.2f} - {hi:.2f}",
        })

    return _to_xml_string(_qgis_root(renderer))


def make_categorized_qml(
    categories: list[str],
    column: str,
    color_ramp: str = "RdYlGn",
    opacity: float = 1.0,
    symbol_type: str = "fill",
) -> str:
    """Generate QML for a categorized renderer."""
    if not categories:
        return make_single_symbol_qml(opacity, symbol_type)

    unique = sorted(set(categories))
    colors = _interpolate_colors(color_ramp, len(unique))
    alpha = int(opacity * 255)

    renderer = Element("renderer-v2", type="categorizedSymbol", attr=column)
    symbols = SubElement(renderer, "symbols")
    cats = SubElement(renderer, "categories")

    for i, value in enumerate(unique):
        sym_name = str(i)
        _make_symbol_element(
            symbols, colors[i], alpha, name=sym_name, symbol_type=symbol_type,
        )
        SubElement(cats, "category", {
            "value": str(value),
            "symbol": sym_name,
            "label": str(value),
        })

    return _to_xml_string(_qgis_root(renderer))
