from __future__ import annotations

import pytest

from expression_tomography.core.store import ExperimentStore
from expression_tomography.tasks.text_boundary.mock_provider import BoundaryMockProvider
from expression_tomography.tasks.text_boundary.task import (
    run_calibration,
    write_new_json,
)
from expression_tomography.tasks.text_boundary_targets.mock_provider import (
    TargetMockProvider,
)
from expression_tomography.tasks.text_boundary_targets.task import (
    file_sha,
    run_followups,
)
from scripts.analyze_text_boundary_targets_run import analyze


@pytest.fixture
def pair(tmp_path):
    source = tmp_path / "source.sqlite"
    db = tmp_path / "targets.sqlite"
    store = ExperimentStore(source)
    try:
        run_calibration(store, [BoundaryMockProvider()], repetitions=1)
    finally:
        store.close()
    return source, db


def test_complete_analysis_is_read_only_and_mock_comparison_is_null(pair):
    source, db = pair
    store = ExperimentStore(db)
    try:
        run_followups(store, source, [TargetMockProvider()])
    finally:
        store.close()
    hashes = (file_sha(source), file_sha(db))
    result = analyze(source, db)
    assert result["n_revalidated"] == 72
    assert not result["outside_source_quotes"]
    assert all(
        c["n_current_original_correct"] is None
        for c in result["historical_comparisons"]
    )
    assert result["sender_receiver_coordination"] == "UNIDENTIFIED"
    assert (file_sha(source), file_sha(db)) == hashes


def test_partial_and_uncertain_runs_cannot_be_reported_as_complete(pair):
    source, db = pair
    store = ExperimentStore(db)
    try:
        run_followups(store, source, [TargetMockProvider()], max_new_calls=1)
    finally:
        store.close()
    with pytest.raises(ValueError, match="complete target"):
        analyze(source, db)
    write_new_json(type(db)(str(db) + ".pending.json"), {"uncertain": True})
    with pytest.raises(ValueError, match="journal"):
        analyze(source, db)
