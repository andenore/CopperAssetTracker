import hashlib
import json
import os
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
REVISION = ROOT/'revisions/rf-layout-v1'


def test_gnss_candidate_is_passive_external_and_not_retroactive_approval():
    choice = json.loads((REVISION/'gnss-antenna-recommendation.json').read_text())
    assert choice['mpn'] == 'FXP611.07.0092C'
    assert choice['receiver_mpn'] == 'MAX-M10S-00B'
    assert choice['connector'] == 'J_GNSS'
    assert choice['status'] == 'recommended_prototype_candidate_not_release_selection'
    assert not choice['board_supplied_bias']
    assert not choice['external_antenna_power_required']
    assert not choice['qualified_release']
    assert not choice['changes_to_previous_source_board_or_release_locks']
    assert choice['previous_review_snapshot_preserved']
    assert not choice['installation']['verified_fit']
    assert choice['installation']['required_space_um'] == [40000, 40000, 200]
    assert choice['installation']['manufacturer_minimum_metal_or_main_ground_plane_clearance_um'] == 10000
    assert not choice['procurement']['norway_delivery_confirmed']
    assert not choice['procurement']['purchase_authorized']


@pytest.mark.skipif(not os.environ.get('COPPERLIB_REVIEW_ROOT'), reason='Explicit local library review root required')
def test_gnss_library_fact_and_contract_bindings():
    library = Path(os.environ['COPPERLIB_REVIEW_ROOT']).resolve()
    choice = json.loads((REVISION/'gnss-antenna-recommendation.json').read_text())
    for key in ('library_specification', 'library_contract'):
        path = (library/choice[key]).resolve()
        path.relative_to(library)
        assert hashlib.sha256(path.read_bytes()).hexdigest() == choice[key+'_sha256']
    facts = json.loads((library/choice['library_specification']).read_text())
    assert facts['mpn'] == choice['mpn']
    assert choice['band_compatibility']['antenna_range_mhz'] == [facts['frequency_min_mhz'], facts['frequency_max_mhz']]
    assert choice['installation']['manufacturer_minimum_metal_or_main_ground_plane_clearance_um'] == facts['minimum_metal_or_main_ground_plane_clearance_um']
