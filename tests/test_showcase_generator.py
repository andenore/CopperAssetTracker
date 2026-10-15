"""Presentation data is read from native geometry, never invented or repaired."""
import importlib.util
from pathlib import Path
import json

import pytest


def load_generator():
    source = Path(__file__).resolve().parents[1] / "scripts/generate_readme_assets.py"
    spec = importlib.util.spec_from_file_location("tracker_figure_refresh", source)
    module = importlib.util.module_from_spec(spec)
    import sys
    sys.path.insert(0, str(source.parent))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)
    return module


def test_figure_refresh_rejects_wrong_native_board_before_rendering(tmp_path):
    module = load_generator()
    pcb = tmp_path / "board.kicad_pcb"
    pcb.write_text("wrong board")
    (tmp_path / "snapshot.json").write_text(json.dumps({"pcb_sha256": "0" * 64}))
    with pytest.raises(ValueError, match="does not describe this PCB"):
        module.refresh_figures(pcb, "unused", tmp_path / "unused.py", tmp_path)


def test_figure_refresh_preserves_historical_source_and_review_evidence(tmp_path, monkeypatch):
    module = load_generator()
    pcb = tmp_path / "board.kicad_pcb"
    pcb.write_text("recorded native board")
    drc = tmp_path / "drc.json"
    drc.write_text("recorded DRC")
    snapshot = {"pcb_sha256": module.digest(pcb), "native_drc_sha256": module.digest(drc),
                "canonical_source_status": "historical_input_before_macro_definition_migration",
                "source_sha256": "retained source", "route_report_sha256": "retained routing",
                "qualified_release": False, "rendered_assets": {}}
    module.write_json(tmp_path / "snapshot.json", snapshot)
    def fake_render(pcb, cli, renderer, output):
        for name in (*module.VIEWS, "rendering.json"):
            (output / name).write_text("new illustration")
        return {"renderer_sha256": "renderer"}
    monkeypatch.setattr(module, "render_assets", fake_render)
    module.refresh_figures(pcb, "unused", tmp_path / "renderer.py", tmp_path)
    refreshed = json.loads((tmp_path / "snapshot.json").read_text())
    for key in snapshot.keys() - {"rendered_assets"}:
        assert refreshed[key] == snapshot[key]
    assert "routing-all.svg" in refreshed["rendered_assets"]


def test_native_placement_excerpt_preserves_native_references_and_plain_units(tmp_path):
    source = Path(__file__).resolve().parents[1] / "scripts/generate_readme_assets.py"
    spec = importlib.util.spec_from_file_location("tracker_showcase_generator", source)
    module = importlib.util.module_from_spec(spec)
    import sys
    sys.path.insert(0, str(source.parent))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)
    pcb = tmp_path / "fixture.kicad_pcb"
    pcb.write_text('''(kicad_pcb
      (footprint "CopperScript:Cap" (property "Reference" "C_MCU") (at 53.599976 21.190002 90))
      (footprint "CopperScript:Modem" (property "Reference" "U_MODEM_U") (at 20 24))
      (footprint "Other" (property "Reference" "R1") (at 1 2)))''')
    data = module.native_placement_excerpt(pcb)
    assert "millimetres" in data["units"]
    assert [p["reference"] for p in data["placements"]] == ["C_MCU", "U_MODEM_U"]
    assert data["placements"][0]["position_mm"] == {"x": "53.599976", "y": "21.190002"}
    assert data["placements"][1]["position_mm"] == {"x": "20", "y": "24"}
    assert data["placements"][1]["rotation_degrees"] == "0"
