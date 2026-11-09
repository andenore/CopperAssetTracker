"""DC-safe matching values for a synthesized antenna, on its fine-mesh impedance.

`copper synthesize-antenna` reports the best ideal two-element L-section,
whatever its topology. Some of those put a shunt inductor straight onto the
radio pin, which is then DC-shorted to ground; whether the nRF52832 ANT pin
and the SIM7672X ANT_MAIN tolerate that is not established, so this search
rejects any shunt inductor without a series capacitor between it and the
radio. It searches E24 parts for the board's matching lands on the report's
simulated feed impedance, with lossy parts (inductor Q 30, capacitor Q 200,
assumed, not part data), ranks networks by the worst power delivered to the
antenna over the band (mismatch and part loss), and prints the worst return
loss at nominal values and at tolerance corners. Simulation post-processing
only, not bench data.

    python3 revisions/pcb-antennas-v1/match_search.py ble revisions/pcb-antennas-v1/ble-synthesis.json
    python3 revisions/pcb-antennas-v1/match_search.py lte revisions/pcb-antennas-v1/lte-synthesis.json

Topologies (antenna side first):
- ble: two lands after Nordic's L1: an L-section, series then shunt or shunt
  then series.
- lte: SIM7672X Figure 30: 100 pF DC block (R2), shunt C2, series R1, shunt
  C1; either shunt may be left unfitted.
"""
import itertools
import json
import math
import sys

import numpy as np

QL, QC = 30.0, 200.0
BANDS = {"ble": (2400e6, 2483.5e6), "lte": (791e6, 862e6)}
TOLERANCE = {"ble": (0.1e-9, 0.1e-12), "lte": (0.3e-9, 0.25e-12)}
E24 = [1.0, 1.1, 1.2, 1.3, 1.5, 1.6, 1.8, 2.0, 2.2, 2.4, 2.7, 3.0, 3.3, 3.6, 3.9, 4.3, 4.7, 5.1,
       5.6, 6.2, 6.8, 7.5, 8.2, 9.1]
INDUCTORS = sorted({round(m * 10 ** e, 6) * 1e-9 for e in (-1, 0, 1) for m in E24 if 0.5 <= m * 10 ** e <= 47})
CAPACITORS = sorted({round(m * 10 ** e, 6) * 1e-12 for e in (-1, 0, 1) for m in E24 if 0.3 <= m * 10 ** e <= 47})
PARTS = [("L", v) for v in INDUCTORS] + [("C", v) for v in CAPACITORS]
DC_BLOCK = ("series", "C", 100e-12)


def impedance(kind, value, w):
    """Element impedance at angular frequencies `w` (array)."""
    if kind == "L":
        return w * value / QL + 1j * w * value
    x = 1 / (w * value)
    return x / QC - 1j * x


def metrics(band, network):
    """Worst return loss (dB) and worst delivered power (dB of available); antenna side first."""
    w, z_ant = band
    a, b, c, d = np.ones_like(z_ant), np.zeros_like(z_ant), np.zeros_like(z_ant), np.ones_like(z_ant)
    for position, kind, value in reversed(network):  # cascade from the radio towards the antenna
        if kind is None:
            continue
        z = impedance(kind, value, w)
        if position == "series":
            b, d = a * z + b, c * z + d
        else:
            a, c = a + b / z, c + d / z
    z_in = (a * z_ant + b) / (c * z_ant + d)
    worst_s11 = 20 * math.log10(np.max(np.abs((z_in - 50) / (z_in + 50))))
    # 1 V source behind 50 ohm: antenna current and delivered power over available power.
    i_ant = 1 / (a * z_ant + b + 50 * (c * z_ant + d))
    gain = np.abs(i_ant) ** 2 * z_ant.real / 2 / (1 / (8 * 50))
    return worst_s11, 10 * math.log10(np.min(gain))


def dc_safe(network):
    """No shunt inductor without a series capacitor between it and the radio."""
    for i, (position, kind, _) in enumerate(network):
        if position == "shunt" and kind == "L":
            if not any(p == "series" and k == "C" for p, k, _ in network[i + 1:]):
                return False
    return True


def candidates(antenna):
    if antenna == "ble":
        for a, b in itertools.product(PARTS, PARTS):
            yield [("series", *a), ("shunt", *b)]
            yield [("shunt", *a), ("series", *b)]
    else:
        shunts = PARTS + [(None, None)]
        for c2, r1, c1 in itertools.product(shunts, PARTS, shunts):
            yield [DC_BLOCK, ("shunt", *c2), ("series", *r1), ("shunt", *c1)]


def describe(network):
    parts = []
    for position, kind, value in network:
        if kind is None:
            parts.append(f"{position} not fitted")
        else:
            parts.append(f"{position} " + (f"{value * 1e9:.1f} nH" if kind == "L" else f"{value * 1e12:.1f} pF"))
    return ", ".join(parts)


def corners(antenna, band, network):
    dl, dc = TOLERANCE[antenna]
    worst = -math.inf
    variable = [i for i, (_, k, _) in enumerate(network) if k is not None and network[i] != DC_BLOCK]
    for signs in itertools.product((-1, 1), repeat=len(variable)):
        varied = list(network)
        for i, sign in zip(variable, signs):
            position, kind, value = varied[i]
            varied[i] = (position, kind, value + sign * (dl if kind == "L" else dc))
        worst = max(worst, metrics(band, varied)[0])
    return worst


def main(antenna, path):
    low, high = BANDS[antenna]
    report = json.loads(open(path).read())
    points = [(float(p["frequency_hz"]), complex(*map(float, p["z_ohm"]))) for p in report["curve"]]
    points = [(f, z) for f, z in points if low <= f <= high]
    band = (np.array([2 * math.pi * f for f, _ in points]), np.array([z for _, z in points]))
    print("bare: worst S11 %.2f dB, worst delivered %.2f dB" % metrics(band, []))
    ranked = sorted(((*metrics(band, n), n) for n in candidates(antenna) if dc_safe(n)), key=lambda r: -r[1])
    for s11, gain, network in ranked[:5]:
        print(f"delivered {gain:.2f} dB, S11 {s11:.2f} dB, tolerance corners S11 "
              f"{corners(antenna, band, network):.2f} dB (antenna side first): {describe(network)}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
