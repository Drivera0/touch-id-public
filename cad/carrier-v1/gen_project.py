"""
gen_project.py -- carrier-v1.kicad_pro, so the board opens as a project with
real design rules instead of KiCad's defaults.

Rules are JLCPCB's 2-layer capability, deliberately a little conservative:
this board's tightest features are the 0.400 mm pogo row gap and the 0.325 mm
smallest pad-to-pad, both of which clear these limits comfortably.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_carrier as G

HERE = os.path.dirname(os.path.abspath(__file__))
OUT  = os.path.join(HERE, "carrier-v1.kicad_pro")

pro = {
  "board": {
    "3dviewports": [], "design_settings": {
      "defaults": {
        "board_outline_line_width": 0.1,
        "copper_line_width": 0.2, "copper_text_size_h": 1.0,
        "copper_text_size_v": 1.0, "copper_text_thickness": 0.15,
        "other_line_width": 0.15, "silk_line_width": 0.15,
        "silk_text_size_h": 0.8, "silk_text_size_v": 0.8,
        "silk_text_thickness": 0.12,
      },
      "diff_pair_dimensions": [], "drc_exclusions": [],
      "rules": {
        "copper_edge_clearance": 0.3,
        "max_error": 0.005,
        "min_clearance": 0.2,               # JLC 2-layer standard
        "min_connection": 0.0,
        "min_copper_edge_clearance": 0.3,
        "min_hole_clearance": 0.25,
        "min_hole_to_hole": 0.5,            # O1.05 holes on 2.00 pitch -> 0.95
        "min_microvia_diameter": 0.2, "min_microvia_drill": 0.1,
        "min_resolved_spokes": 2,
        "min_silk_clearance": 0.0,
        "min_text_height": 0.55, "min_text_thickness": 0.08,
        "min_through_hole_diameter": 0.3,
        "min_track_width": 0.2,
        "min_via_annular_width": 0.13,
        "min_via_diameter": 0.4,
        "solder_mask_to_copper_clearance": 0.0,
        "use_height_for_length_calcs": True,
      },
      "rule_severities": {},
      "track_widths": [0.0, 0.5, 0.8],
      "via_dimensions": [{"diameter": 0.8, "drill": 0.4}],
      "zones_allow_external_fillets": False,
    },
    "layer_presets": [], "viewports": [],
  },
  "boards": [], "cvpcb": {"equivalence_files": []},
  "libraries": {"pinned_footprint_libs": [], "pinned_symbol_libs": []},
  "meta": {"filename": "carrier-v1.kicad_pro", "version": 3},
  "net_settings": {
    "classes": [{
      "bus_width": 12, "clearance": 0.2, "diff_pair_gap": 0.25,
      "diff_pair_via_gap": 0.25, "diff_pair_width": 0.2, "line_style": 0,
      "microvia_diameter": 0.3, "microvia_drill": 0.1, "name": "Default",
      "pcb_color": "rgba(0, 0, 0, 0.000)", "schematic_color": "rgba(0, 0, 0, 0.000)",
      "track_width": 0.5, "via_diameter": 0.8, "via_drill": 0.4,
      "wire_width": 6,
    }, {
      "bus_width": 12, "clearance": 0.2, "diff_pair_gap": 0.25,
      "diff_pair_via_gap": 0.25, "diff_pair_width": 0.2, "line_style": 0,
      "microvia_diameter": 0.3, "microvia_drill": 0.1, "name": "Power",
      "pcb_color": "rgba(0, 0, 0, 0.000)", "schematic_color": "rgba(0, 0, 0, 0.000)",
      "track_width": 0.8, "via_diameter": 0.8, "via_drill": 0.4,
      "wire_width": 6,
    }],
    "meta": {"version": 4},
    "net_colors": None, "netclass_assignments": None,
    "netclass_patterns": [{"netclass": "Power", "pattern": "VSTOR"},
                          {"netclass": "Power", "pattern": "GND"}],
  },
  "pcbnew": {
    "last_paths": {"gencad": "", "idf": "", "netlist": "", "plot": "",
                   "pos_files": "", "specctra_dsn": "", "step": "",
                   "svg": "", "vrml": ""},
    "page_layout_descr_file": "",
  },
  "schematic": {}, "sheets": [], "text_variables": {},
}

json.dump(pro, open(OUT, "w"), indent=2)
print("wrote", OUT)
print(f"  min_clearance     {pro['board']['design_settings']['rules']['min_clearance']} mm"
      f"   (board's tightest pad gap is 0.325)")
print(f"  min_track_width   {pro['board']['design_settings']['rules']['min_track_width']} mm"
      f"   (narrowest track on the board is 0.5)")
print(f"  min_hole_to_hole  {pro['board']['design_settings']['rules']['min_hole_to_hole']} mm"
      f"   (pogo row is 2.00 pitch, O1.05 -> 0.95)")
print(f"  netclasses: Default 0.5 mm, Power 0.8 mm (VSTOR, GND)")
