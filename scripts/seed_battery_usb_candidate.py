"""Apply only the reviewed tracker USB-detect net delta to a pinned pose/copper seed.

Application-specific migration, not a generic stale-board importer. The earlier
candidate is retained; current source owns pad nets. Discard all ordinary V5
copper before repairing V5/V3V8 with CopperScript. This seed is not routed proof.
"""
import argparse
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path

from pcbir.backends.kicad_pcb import KiCadPcbBackend, kicad_reference
from pcbir.backends.kicad_project import write_kicad_project
from pcbir.importers.kicad_mod import _children, _first, _parse_sexpr
from finish_routed_candidate import current_candidate, require
from probe_open_routes import ROOT, posed_source

PRIOR_SHA256 = '33adc8ec883a47288d467386e9e0c4992337eac120aa0909223fc6819cf4a270'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pcb', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    require(not args.output.exists(), 'Output exists; choose a new seed')
    require(sha256(args.pcb.read_bytes()).hexdigest() == PRIOR_SHA256,
            'Only the pinned, previously verified candidate can be migrated')
    source = posed_source(args.pcb)
    expected = {(kicad_reference(p.component), p.pad): n.name
                for n in source.nets for p in n.pads}
    tree = _parse_sexpr(args.pcb.read_text(), str(args.pcb))
    native_nets = {n[1]: n[2] for n in _children(tree, 'net')}
    native_nets.update({n.name: n.name for n in source.nets})
    observed = {}
    for fp in _children(tree, 'footprint'):
        ref = next(p[2] for p in _children(fp, 'property') if p[1] == 'Reference')
        for pad in _children(fp, 'pad'):
            net = _first(pad, 'net')
            if net:
                key = ref, pad[1]
                name = native_nets[net[1]]
                require(key not in observed or observed[key] == name, 'Conflicting duplicate lands')
                observed[key] = name
    changes = {key: (observed.get(key), expected.get(key)) for key in observed.keys() | expected.keys()
               if observed.get(key) != expected.get(key)}
    require(changes == {('U_MODEM', '24'): ('V5', 'V3V8')},
            f'Unexpected electrical changes: {changes}')
    require(not any(t.net == 'V5' for t in source.tracks)
            and not any(v.net == 'V5' for v in source.vias), 'V5 includes protected owner copper')
    seed = posed_source(args.pcb, with_copper=True)
    removed_tracks = sum(t.net == 'V5' for t in seed.tracks)
    removed_vias = sum(v.net == 'V5' for v in seed.vias)
    seed = replace(seed, tracks=tuple(t for t in seed.tracks if t.net != 'V5'),
                   vias=tuple(v for v in seed.vias if v.net != 'V5'))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_kicad_project(KiCadPcbBackend().generate(seed), args.output)
    # Ordinary resume guard remains strict; no migration exception is introduced.
    verified = current_candidate(args.output)
    require(len(verified.placements) == 83, 'Unexpected component count')
    document = {'prior_pcb_sha256': PRIOR_SHA256, 'production_ready': False,
                'changed_pad': 'U_MODEM.24', 'old_net': 'V5', 'new_net': 'V3V8',
                'discarded_v5_tracks': removed_tracks, 'discarded_v5_vias': removed_vias,
                'source_sha256': sha256((ROOT / 'board.copper').read_bytes()).hexdigest(),
                'seed_sha256': sha256(args.output.read_bytes()).hexdigest(),
                'required_repairs': ['V5', 'V3V8'], 'native_refill_drc_required': True}
    args.output.with_suffix('.migration.json').write_text(json.dumps(document, indent=2) + '\n')
    print(json.dumps(document), flush=True)


if __name__ == '__main__':
    main()
