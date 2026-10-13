import hashlib
import json
import os
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
REVISION = ROOT/'revisions/rf-layout-v1'


def test_selection_keeps_external_antenna_and_exact_stackup_outside_cpl_approval():
    antenna = json.loads((REVISION/'antenna-selection.json').read_text())
    cellular = antenna['cellular']
    assert cellular['mpn'] == 'FXUB16.07.0150AQ'
    assert cellular['eu_lte_bands'] == [1, 3, 7, 8, 20, 28]
    assert cellular['assembly_scope'] == 'external installation after PCBA; not a CPL item'
    assert not cellular['installation']['verified_fit']
    assert not antenna['qualified_release']
    assert antenna['gnss']['antenna_type'] == 'passive'
    fabrication = json.loads((REVISION/'fabrication-selection.json').read_text())
    assert fabrication['selected_profile'] == 'JLC06161H-3313'
    assert fabrication['material'] == 'Nan Ya Plastics NP-155F'
    assert fabrication['nominal_order_thickness_um'] == 1600
    assert not fabrication['cellular_feed']['supplier_acceptance_received']


def test_completed_inspection_never_becomes_design_or_production_approval():
    review = json.loads((REVISION/'cellular-design-review.json').read_text())
    assert review['review_complete']
    assert review['decision'] == 'changes_required'
    assert not review['rf_design_approved'] and not review['qualified_release']
    assert not review['observations']['full_path_impedance_verified']
    assert not review['observations']['pcb_bytes_changed']
    assert {f['id'] for f in review['findings']} >= {'rf-esd', 'matching-dc-isolation', 'launch-return-model', 'prototype-rf'}
    assert all(f['status'] != 'pass' for f in review['findings'])
    assert not review['verification']['full_copperlib_suite_completed']


def test_qualification_plan_requires_external_antenna_evidence_not_only_pcb_geometry():
    plan = json.loads((REVISION/'cellular-engineering-plan.json').read_text())
    assert {c['scope'] for c in plan['contracts']} == {'cellular', 'cellular-antenna'}
    assert plan['evidence'] == {}
    assert not plan['context']['operating_envelope']['reviewed']
    assert 'antenna_selection' in plan['input_files']
    assert 'fabrication_selection' in plan['input_files']


@pytest.mark.skipif(not os.environ.get('COPPER_RF_REVIEW_ARTIFACTS'), reason='Explicit retained RF review artifacts required')
def test_retained_review_input_hashes_and_actual_source_checkpoint():
    review = json.loads((REVISION/'cellular-design-review.json').read_text())
    for name, item in review['inputs'].items():
        path = (REVISION/item['path']).resolve()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == item['sha256'], name
    inventory = json.loads((REVISION/review['inputs']['layout_inventory']['path']).read_text())
    assert inventory['source_checkpoint']['status'] == 'source_land_pose_and_immutable_copper_match'
    assert inventory['source_checkpoint']['lock_sha256'] == review['inputs']['source_lock']['sha256']
    assert inventory['inputs']['pcb_sha256'] == review['inputs']['pcb']['sha256']
    assert inventory['status'] == 'incomplete' and not inventory['qualified_release']
