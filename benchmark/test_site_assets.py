from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent


def test_layout_metadata_references_svg_favicon():
    layout_text = (REPO_ROOT / "app" / "layout.tsx").read_text()

    assert "icons:" in layout_text
    assert '"/favicon.svg"' in layout_text


def test_favicon_svg_uses_brand_palette():
    svg_text = (REPO_ROOT / "public" / "favicon.svg").read_text()

    assert "<svg" in svg_text
    assert "#22c55e" in svg_text
    assert "#3b82f6" in svg_text
    assert "#06b6d4" in svg_text
