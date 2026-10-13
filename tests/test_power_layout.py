"""Physical contracts, not RF/power qualification or production approval."""
from dataclasses import replace
from pathlib import Path
import sys
import unittest
from pcbir.footprints import FootprintResolver
from pcbir.loader import load_design
from pcbir.physicalize import PrototypePhysicalOptions, resolved_physicalize
from pcbir.hard_macros import apply_hard_macro_scene, validate_hard_macros
from pcbir.drc import run_physical_drc, PhysicalDrcPolicy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from probe_power_macros import isolated_probe


class PowerLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.design = load_design(ROOT / "board.copper", locked=True, offline=True)
        cls.physical = resolved_physicalize(cls.design,
            FootprintResolver(base_directory=ROOT, locked=True, offline=True),
            PrototypePhysicalOptions(copper_layers=6, fabrication_profile="jlcpcb-six-layer"))

    def test_cardinal_rotations_and_port_consumers(self):
        for scene, count in (("logic-power-macro.json", 9), ("modem-power-macro.json", 11)):
            for rotation in (0, 90, 180, 270):
                with self.subTest(scene=scene, rotation=rotation):
                    b = isolated_probe(self.physical, ROOT / scene, rotation)
                    validate_hard_macros(b)
                    self.assertEqual(len(b.rigid_clusters[0].members), count)
                    self.assertEqual(len([p for p in b.placements if p.reference.startswith("PROBE_")]),
                                     3 if count == 11 else 2)

    def test_lost_owner_copper_is_rejected(self):
        b = isolated_probe(self.physical, ROOT / "logic-power-macro.json")
        for field in ("tracks", "vias", "polygons"):
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "immutable hard-macro"):
                replace(b, **{field: getattr(b, field)[1:]})

    def test_changed_pad_binding_is_rejected(self):
        b = isolated_probe(self.physical, ROOT / "modem-power-macro.json")
        macros = b.hard_macros
        binding = macros[0].pad_bindings[0]
        with self.assertRaisesRegex(ValueError, "bindings changed"):
            replace(b, hard_macros=(replace(macros[0], pad_bindings=(replace(binding, net="GND"), *macros[0].pad_bindings[1:])),))

    def test_changed_footprint_is_rejected(self):
        pose = next(p for p in self.physical.placements if p.reference == "PWR/U_LOGIC")
        footprints = dict(self.physical.footprints)
        f = footprints[pose.footprint]
        p = f.pads[0]
        footprints[pose.footprint] = replace(f, pads=(replace(p,
            position=replace(p.position, x_nm=p.position.x_nm + 1000)), *f.pads[1:]))
        with self.assertRaisesRegex(ValueError, "footprint .*mismatch"):
            replace(self.physical, footprints=footprints)

    def test_macro_branches_with_actual_host_rail_widths(self):
        for scene in ("logic-power-macro.json", "modem-power-macro.json"):
            with self.subTest(scene=scene):
                b = isolated_probe(self.physical, ROOT / scene, port_consumers=False)
                nets = {n.name for n in b.nets}
                b = replace(b, net_routing_rules=tuple(r for r in self.physical.net_routing_rules if r.net in nets))
                report = run_physical_drc(b, policy=PhysicalDrcPolicy(False))
                self.assertFalse([f for f in report.findings if f.code == "DRC-TRACK-WIDTH"])
                self.assertTrue([f for f in report.findings if f.code == "DRC-MACRO-WIDTH-CONTRACT"])
                self.assertEqual(next(r.width_nm for r in b.net_routing_rules if r.net == "PWR/VSYS"), 800000)

    def test_clock_and_distribution_contracts(self):
        rules = {r.net: r for r in self.physical.net_routing_rules}
        for net in ("NRF_XC1", "NRF_XC2"):
            r = rules[net]
            self.assertEqual(r.topology, "tree")
            self.assertEqual(r.max_vias, 0)
            self.assertEqual(r.max_length_nm, 8000000)
            self.assertEqual([l.value for l in r.allowed_layers], ["F.Cu"])
        self.assertEqual(rules["NRF_DEC3"].max_length_nm, 2000000)
        self.assertEqual(rules["NRF_DEC3"].max_vias, 0)
        self.assertGreater(rules["NRF_DEC3"].priority, rules["NRF_XC1"].priority)
        self.assertGreater(rules["NRF_DEC3"].priority, rules["NRF_XC2"].priority)
        self.assertGreater(rules["NRF_XC2"].priority, rules["NRF_XC1"].priority)
        poses = {r.reference: r for r in self.physical.placement_rules}
        self.assertEqual(poses["C_DEC3"].fixed_position.x_nm, 85030000)
        self.assertEqual(poses["C_DEC3"].fixed_rotation_degrees, 0)
        self.assertEqual(poses["R_RESET_NRF"].fixed_position.x_nm, 84000000)
        for net in ("V3V8", "PWR/VSYS", "PWR/BAT"):
            self.assertEqual(rules[net].width_nm, 800000)
            self.assertEqual(rules[net].breakout_width_nm, 240000)

    def test_modem_enable_port_is_a_front_lead_in_not_a_bare_via(self):
        b = isolated_probe(self.physical, ROOT / "modem-power-macro.json", port_consumers=False)
        macro = b.hard_macros[0]
        port = next(p for p in macro.ports if p.name == "EN")
        self.assertEqual(port.layer.value, "F.Cu")
        self.assertEqual(port.position.x_nm, 8800000)
        self.assertTrue(any(t.net == port.net and t.layer == port.layer and t.end == port.position
                            for t in macro.tracks))
        self.assertFalse(any(v.position == port.position for v in macro.vias))

    def test_quiet_support_parts_stay_in_compact_source_placements(self):
        rules = {r.reference: r for r in self.physical.placement_rules}
        expected = {"U_MODEM_LEVEL": (20500000, 42000000),
                    "U_MODEM_KEY": (12000000, 40000000),
                    "U_MODEM_STATUS": (4500000, 30000000),
                    "R_CC_OUT1": (37200000, 59900000),
                    "PWR/R_ILIM": (64600000, 38000000),
                    "PWR/R_ISET": (71200000, 38550000)}
        for ref, position in expected.items():
            with self.subTest(reference=ref):
                self.assertEqual((rules[ref].fixed_position.x_nm, rules[ref].fixed_position.y_nm), position)

    def test_translator_bypasses_use_generic_pin_association_not_fixed_poses(self):
        rules = {r.reference: r for r in self.physical.placement_rules}
        links = {l.capacitor.component: l for l in self.physical.decoupling_links}
        for reference, target, pad in (("C_LEVEL_A", "U_MODEM_LEVEL", "7"),
                                       ("C_LEVEL_B", "U_MODEM_LEVEL", "6"),
                                       ("C_STATUS_A", "U_MODEM_STATUS", "7"),
                                       ("C_STATUS_B", "U_MODEM_STATUS", "6")):
            with self.subTest(reference=reference):
                self.assertTrue(reference not in rules or rules[reference].fixed_position is None)
                self.assertEqual((links[reference].target.component, links[reference].target.pad), (target, pad))
                self.assertEqual(links[reference].return_net, "GND")


if __name__ == "__main__":
    unittest.main()
