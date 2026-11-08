"""Three-element match for the LTE antenna on its fine-mesh impedance.

`copper synthesize-antenna` reports a two-element L-section; across B20 that
reaches only -5.3 dB. The board carries SIM7672X Figure 30 pi lands, so this
script searches E24 values for them on the report's simulated feed impedance,
with the 100 pF DC block in the chain and lossy parts (inductor Q 30,
capacitor Q 200, assumed, not part data). It scores each network by the worst
power delivered to the antenna over the band (mismatch and part loss) and
prints the worst return loss at the nominal values and at tolerance corners
(+-0.3 nH, +-0.25 pF). Simulation post-processing only, not bench data.

    python3 revisions/pcb-antennas-v1/lte_pi_match.py revisions/pcb-antennas-v1/lte-synthesis.json
"""
import itertools
import json
import math
import sys

import numpy as np

LOW, HIGH = 791e6, 862e6
QL, QC = 30.0, 200.0
DC_BLOCK = ("series", "C", 100e-12)
E24 = [1.0, 1.1, 1.2, 1.3, 1.5, 1.6, 1.8, 2.0, 2.2, 2.4, 2.7, 3.0, 3.3, 3.6, 3.9, 4.3, 4.7, 5.1,
       5.6, 6.2, 6.8, 7.5, 8.2, 9.1]


def element(kind, value, f):
    w = 2 * math.pi * f
    if kind == "L":
        return complex(w * value / QL, w * value)
    x = 1 / (w * value)
    return complex(x / QC, -x)


def metrics(band, network):
    """Worst return loss (dB) and worst delivered power (dB of available); antenna side first."""
    worst_s11, worst_gain = -math.inf, math.inf
    for f, z_ant in band:
        m = np.eye(2, dtype=complex)
        for position, kind, value in reversed(network):
            if kind is None:
                continue
            z = element(kind, value, f)
            m = m @ (np.array([[1, z], [0, 1]]) if position == "series" else np.array([[1, 0], [1 / z, 1]]))
        a, b, c, d = m.ravel()
        z_in = (a * z_ant + b) / (c * z_ant + d)
        worst_s11 = max(worst_s11, 20 * math.log10(abs((z_in - 50) / (z_in + 50))))
        v_in = z_in / (z_in + 50)  # 1 V source behind 50 ohm
        _, i_ant = np.linalg.solve(m, np.array([v_in, v_in / z_in]))
        delivered = abs(i_ant) ** 2 * z_ant.real / 2
        worst_gain = min(worst_gain, delivered / (1 / (8 * 50)))
    return worst_s11, 10 * math.log10(worst_gain)


def describe(kind, value):
    if kind is None:
        return "not fitted"
    return f"{value * 1e9:.1f} nH" if kind == "L" else f"{value * 1e12:.1f} pF"


def main(path):
    report = json.loads(open(path).read())
    band = [(float(p["frequency_hz"]), complex(*map(float, p["z_ohm"]))) for p in report["curve"]]
    band = [(f, z) for f, z in band if LOW <= f <= HIGH]
    inductors = [m * 10 ** e * 1e-9 for e in (0, 1) for m in E24 if m * 10 ** e <= 47]
    capacitors = [m * 10 ** e * 1e-12 for e in (0, 1) for m in E24 if m * 10 ** e <= 47]
    shunts = [("L", v) for v in inductors] + [("C", v) for v in capacitors] + [(None, None)]
    series = [("L", v) for v in inductors] + [("C", v) for v in capacitors]
    print("bare: worst S11 %.2f dB, worst delivered %.2f dB" % metrics(band, []))
    ranked = []
    for c2, r1, c1 in itertools.product(shunts, series, shunts):
        network = [DC_BLOCK, ("shunt", *c2), ("series", *r1), ("shunt", *c1)]
        s11, gain = metrics(band, network)
        ranked.append((gain, s11, c2, r1, c1))
    ranked.sort(key=lambda r: -r[0])
    for gain, s11, c2, r1, c1 in ranked[:5]:
        print(f"delivered {gain:.2f} dB, S11 {s11:.2f} dB: antenna-side shunt {describe(*c2)}, "
              f"series {describe(*r1)}, module-side shunt {describe(*c1)}")
    chosen = [DC_BLOCK, ("shunt", "L", 2.7e-9), ("series", "L", 1.5e-9), ("shunt", "C", 9.1e-12)]
    s11, gain = metrics(band, chosen)
    corners = []
    for da, db, dc in itertools.product((-0.3e-9, 0.3e-9), (-0.3e-9, 0.3e-9), (-0.25e-12, 0.25e-12)):
        corners.append(metrics(band, [DC_BLOCK, ("shunt", "L", 2.7e-9 + da), ("series", "L", 1.5e-9 + db),
                                      ("shunt", "C", 9.1e-12 + dc)])[0])
    print(f"chosen 2.7 nH / 1.5 nH / 9.1 pF: S11 {s11:.2f} dB, delivered {gain:.2f} dB, "
          f"tolerance corners S11 {max(corners):.2f} dB")


if __name__ == "__main__":
    main(sys.argv[1])
