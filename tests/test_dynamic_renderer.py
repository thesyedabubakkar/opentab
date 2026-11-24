import pytest
from tools.dynamic_scene_renderer import render_scene_html

def test_render_all_components():
    components = [
        {"card_type": "window_preview", "card_data": {"window_title": "AI Studio REC"}},
        {"card_type": "comparison_matrix", "card_data": {"left_label": "Old", "right_label": "New", "stamp": "FREE"}},
        {"card_type": "step_guide", "card_data": {"step_num": "STEP 1", "title": "Download", "url": "github.com", "badge": "10%"}},
        {"card_type": "waveform_spec", "card_data": {"tool_name": "Kokoro", "device": "Laptop", "status": "Ready"}},
        {"card_type": "barchart_comparison", "card_data": {"title": "Views", "item1": "India", "item2": "USA"}},
        {"card_type": "pricing_breakdown", "card_data": {"items": [{"name": "Tool", "price": "$0"}]}},
        {"card_type": "cta_card", "card_data": {"action_keyword": "CODE", "stamp": "SENT"}}
    ]

    for c in components:
        sc = {
            "category_tag": "TEST",
            "part_label": "PART 01",
            "watermark_number": "01",
            "headline": "TEST TITLE",
            "subtext": "Sub",
            "progress_percent": 30,
            **c
        }
        html_out = render_scene_html(sc, topic="Test Topic")
        assert "<html>" in html_out
        assert "TEST TITLE" in html_out
        assert "bottom-scrub-bar" in html_out
        assert "scrub-ball" in html_out
        assert "30%" in html_out
