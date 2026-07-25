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


def test_mobile_navigation_closes_on_escape_and_restores_button_focus():
    navbar_text = (REPO_ROOT / "components" / "shared" / "navbar.tsx").read_text()

    assert 'event.key !== "Escape"' in navbar_text
    assert 'document.addEventListener("keydown", closeOnEscape)' in navbar_text
    assert 'document.removeEventListener("keydown", closeOnEscape)' in navbar_text
    assert "mobileMenuButtonRef.current?.focus()" in navbar_text


def test_performance_timeline_renders_single_run_models_as_markers():
    chart_text = (
        REPO_ROOT / "components" / "charts" / "performance-line-chart.tsx"
    ).read_text()
    timeline_text = (
        REPO_ROOT / "components" / "dashboard" / "performance-timeline.tsx"
    ).read_text()

    assert "modelPointCounts[model.id] <= 1" in chart_text
    assert "{ r: 5, strokeWidth: 2, fill: model.color }" in chart_text
    assert "one completed run are shown as colored" in timeline_text
