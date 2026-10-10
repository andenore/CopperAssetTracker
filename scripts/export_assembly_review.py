"""Candidate BOM/CPL for review only; does not approve or mutate selections."""
import argparse
import csv
import json
from pathlib import Path
from hashlib import sha256
from zipfile import ZipFile, ZIP_DEFLATED

from pcbir.assembly import check_assembly, load_lock
from pcbir.backends.kicad_pcb import kicad_reference
from pcbir.loader import load_design
from pcbir.manufacturing_files import write_jlcpcb_cpl

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fabrication', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    design = load_design(ROOT / 'board.copper', locked=True, offline=True)
    lock = load_lock(ROOT / 'assembly.lock')
    report = check_assembly(design.electrical, lock)
    if any(i['code'] != 'REVIEW_REQUIRED' for i in report['issues']):
        raise ValueError('Stale, incomplete or non-exact assembly selections')
    drc = json.loads((args.fabrication / 'drc.json').read_text())
    if drc['violations'] or drc['unconnected_items']:
        raise ValueError('Native routing must be clean before placement review')
    positions = args.fabrication / 'positions-kicad.csv'
    with positions.open(newline='', encoding='utf-8-sig') as stream:
        rows = list(csv.DictReader(stream))
    by_ref = {r['Ref']: r for r in rows}
    refs = {kicad_reference(s.reference) for s in lock.selections}
    if len(by_ref) != len(rows) or set(by_ref) != refs or len(refs) != len(lock.selections):
        raise ValueError('Exact native placement/selection reference equality required')
    args.output.mkdir(parents=True, exist_ok=False)
    grouped = {}
    for s in lock.selections:
        ref = kicad_reference(s.reference)
        key = s.mpn, by_ref[ref]['Package'], s.supplier_part
        grouped.setdefault(key, []).append(ref)
    with (args.output / 'candidate-bom.csv').open('w', newline='', encoding='utf-8') as stream:
        writer = csv.writer(stream)
        writer.writerow(('Comment', 'Designator', 'Footprint', 'LCSC Part #'))
        for (mpn, footprint, supplier), references in sorted(grouped.items()):
            writer.writerow((mpn, ','.join(sorted(references)), footprint, supplier))
    write_jlcpcb_cpl(positions, args.output / 'candidate-cpl.csv', references=refs)
    report.update(qualified_release=False, status='BOM APPROVED - CPL/BOARD QUALIFICATION PENDING' if report['passed'] else 'CANDIDATE - BOM REVIEW PENDING',
                  bom_approved=report['passed'], placement_reviewed=False,
                  live_stock_checked=False,
                  native_placement_count=len(refs), grouped_bom_rows=len(grouped),
                  source_lock_sha256=sha256((ROOT / 'assembly.lock').read_bytes()).hexdigest(),
                  position_csv_sha256=sha256(positions.read_bytes()).hexdigest())
    (args.output / 'review-status.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    (args.output / 'READ-ME-FIRST.txt').write_text(
        'CANDIDATE ASSEMBLY DATA - NOT APPROVED FOR ORDER\n'
        'BOM selections follow assembly.lock; their approval does not approve CPL.\n'
        'Verify placement polarity, centroid and JLC-specific rotation in the PCBA\n'
        'preview. Live stock is not checked. RF/power/thermal/ESD and independent CAM\n'
        'qualification remain required. These CSV files are for engineering review.\n')
    files = sorted(p for p in args.output.iterdir() if p.is_file())
    (args.output / 'SHA256SUMS').write_text(''.join(
        f'{sha256(p.read_bytes()).hexdigest()}  {p.name}\n' for p in files))
    with ZipFile(args.output / 'assembly-review.zip', 'w', compression=ZIP_DEFLATED) as archive:
        for path in [*files, args.output / 'SHA256SUMS']:
            archive.write(path, path.name)
    print(f'Candidate assembly review: {len(refs)} placements, {len(grouped)} BOM rows; '
          f'{report["reviewed_count"]} approved selections. Not an order-ready package.')


if __name__ == '__main__':
    main()
