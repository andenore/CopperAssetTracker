"""Source placement and routing contracts, not RF/power qualification or production approval."""
from pathlib import Path
import unittest

from copper_cli import compile_board, fixed_placements, nanometres, part, query, routing_rules

ROOT = Path(__file__).resolve().parents[1]


class PowerLayoutTests(unittest.TestCase):
    def test_clock_and_distribution_contracts(self):
        rules = routing_rules()
        for net in ("NRF_XC1", "NRF_XC2"):
            r = rules[net]
            self.assertEqual(r["topology"], "tree")
            self.assertEqual(r["max_vias"], 0)
            self.assertEqual(nanometres(r["max_length"]), 8000000)
            self.assertEqual(r["allowed_layers"], "F.Cu")
        self.assertEqual(nanometres(rules["NRF_DEC3"]["max_length"]), 2000000)
        self.assertEqual(rules["NRF_DEC3"]["max_vias"], 0)
        self.assertGreater(rules["NRF_DEC3"]["priority"], rules["NRF_XC1"]["priority"])
        self.assertGreater(rules["NRF_DEC3"]["priority"], rules["NRF_XC2"]["priority"])
        self.assertGreater(rules["NRF_XC2"]["priority"], rules["NRF_XC1"]["priority"])
        poses = fixed_placements()
        self.assertEqual(nanometres(poses["C_DEC3"]["x"]), 85030000)
        self.assertEqual(poses["C_DEC3"]["rotation"], 0)
        self.assertEqual(nanometres(poses["R_RESET_NRF"]["x"]), 84000000)
        for net in ("V3V8", "PWR/VSYS", "PWR/BAT"):
            self.assertEqual(nanometres(rules[net]["width"]), 800000)
            self.assertEqual(nanometres(rules[net]["breakout_width"]), 240000)

    def test_quiet_support_parts_stay_in_compact_source_placements(self):
        poses = fixed_placements()
        expected = {"U_MODEM_LEVEL": (20500000, 42000000),
                    "U_MODEM_KEY": (12000000, 40000000),
                    "U_MODEM_STATUS": (4500000, 30000000),
                    "R_CC_OUT1": (37200000, 59900000),
                    "PWR/R_ILIM": (64600000, 38000000),
                    "PWR/R_ISET": (71200000, 38550000)}
        for ref, position in expected.items():
            with self.subTest(reference=ref):
                self.assertEqual((nanometres(poses[ref]["x"]), nanometres(poses[ref]["y"])), position)

    def test_translator_bypasses_use_generic_pin_association_not_fixed_poses(self):
        poses = fixed_placements()
        design = compile_board()
        for reference, target, pin, pad in (("C_LEVEL_A", "U_MODEM_LEVEL", "VCCA", "7"),
                                            ("C_LEVEL_B", "U_MODEM_LEVEL", "VCCB", "6"),
                                            ("C_STATUS_A", "U_MODEM_STATUS", "VCCA", "7"),
                                            ("C_STATUS_B", "U_MODEM_STATUS", "VCCB", "6")):
            with self.subTest(reference=reference):
                self.assertNotIn(reference, poses)
                capacitor = query("component", reference)["component"]
                self.assertEqual(capacitor["properties"], {"role": "decoupling", "decouples": f"{target}.{pin}"})
                translator = query("component", target)["component"]
                self.assertEqual(part(design, translator["part"])["pins"][pin]["number"], pad)
                returns = [p["nets"] for p in capacitor["pin_list"] if "GND" in p["nets"]]
                self.assertEqual(returns, [["GND"]])

    def test_build_recipe_does_not_repeat_source_macro_bindings(self):
        configuration = (ROOT / 'Makefile').read_text() + (ROOT / 'make/targets/main.mk').read_text()
        self.assertNotIn('--hard-macro', configuration)


if __name__ == "__main__":
    unittest.main()
