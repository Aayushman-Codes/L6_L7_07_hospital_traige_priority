"""Consolidated tests for hospital_triage_priority.py.

Combines the code coverage and branch coverage suites (28 tests).

Run from the 'Lab 6' folder:
    coverage run --branch -m pytest test_hospital_triage.py
    coverage report -m
"""
import pytest
from hospital_triage_priority import process_triage_wards, monitor_oxygen_manifolds


def make_ward(patients, accepting=True, tier="general", icu=False):
    return {
        "is_accepting": accepting,
        "tier": tier,
        "icu_standby": icu,
        "patients": patients,
    }


# ---------- process_triage_wards ----------

def test_single_normal_patient():
    wards = [make_ward([{"spo2": 98, "hr": 72, "unconscious": False}])]
    result = process_triage_wards(wards, 10)
    assert result == {"acuity_score": 10, "status": "TRIAGE_STABLE"}


def test_invalid_wards_type_raises():
    with pytest.raises(ValueError):
        process_triage_wards("not a list", 10)


def test_ward_not_accepting_is_skipped():
    wards = [make_ward([{"spo2": 98, "hr": 72}], accepting=False)]
    result = process_triage_wards(wards, 10)
    assert result["acuity_score"] == 0


def test_unconscious_patient_adds_100():
    wards = [make_ward([{"spo2": 98, "hr": 72, "unconscious": True}])]
    result = process_triage_wards(wards, 10)
    assert result == {"acuity_score": 100, "status": "TRIAGE_STABLE"}


def test_low_spo2_adds_60():
    wards = [make_ward([{"spo2": 85, "hr": 80}])]
    assert process_triage_wards(wards, 10)["acuity_score"] == 60


def test_high_heart_rate_adds_60():
    wards = [make_ward([{"spo2": 97, "hr": 130}])]
    assert process_triage_wards(wards, 10)["acuity_score"] == 60


def test_icu_standby_adds_25():
    wards = [make_ward([{"spo2": 98, "hr": 72}], icu=True)]
    assert process_triage_wards(wards, 10)["acuity_score"] == 35


def test_invalid_sensor_reading_is_flagged_and_skipped():
    wards = [make_ward([{"spo2": 0, "hr": 72}, {"spo2": 98, "hr": 72}])]
    assert process_triage_wards(wards, 10)["acuity_score"] == 10


def test_more_than_four_flagged_entries_raises_ward_alert():
    patients = [{"spo2": 0, "hr": 72}] * 5
    result = process_triage_wards([make_ward(patients)], 10)
    assert result == {"acuity_score": 0, "status": "WARD_ALERT"}


# ---------- monitor_oxygen_manifolds ----------

def test_oxygen_pressure_failure():
    assert monitor_oxygen_manifolds([[5.0, 3.5, 3.0]]) == "PRESSURE_FAILURE"


def test_oxygen_pressure_normal():
    assert monitor_oxygen_manifolds([[5.0, 4.5], [6.0]]) == "PRESSURE_NORMAL"


# ---------- extra tests for branch coverage ----------

def test_negative_default_acuity_raises():
    # isinstance() is True but default_acuity_score < 0 -> second half of the OR
    with pytest.raises(ValueError):
        process_triage_wards([make_ward([])], -1)


def test_invalid_heart_rate_is_flagged():
    wards = [make_ward([{"spo2": 98, "hr": 0}])]
    assert process_triage_wards(wards, 10)["acuity_score"] == 0


def test_ward_with_no_patients_key_and_defaults():
    # missing "tier", "patients", "icu_standby" fall back to defaults
    result = process_triage_wards([{"is_accepting": True}], 10)
    assert result == {"acuity_score": 0, "status": "NO_URGENT_CASES"}


def test_ward_missing_is_accepting_key_is_skipped():
    assert process_triage_wards([{"patients": [{"spo2": 98}]}], 10)["acuity_score"] == 0


def test_patient_defaults_used_when_vitals_missing():
    # defaults spo2=95, hr=75, unconscious=False -> stable, default score
    result = process_triage_wards([make_ward([{}])], 7)
    assert result["acuity_score"] == 7


def test_unconscious_outpatient_resets_score_and_breaks():
    patients = [
        {"spo2": 98, "hr": 72},                      # +10
        {"spo2": 98, "hr": 72, "unconscious": True}, # reset to 0 and break
        {"spo2": 98, "hr": 72},                      # never reached
    ]
    result = process_triage_wards([make_ward(patients, tier="outpatient")], 10)
    assert result == {"acuity_score": 0, "status": "NO_URGENT_CASES"}


def test_unconscious_in_non_outpatient_tier_does_not_break():
    patients = [
        {"spo2": 98, "hr": 72, "unconscious": True},
        {"spo2": 98, "hr": 72},
    ]
    result = process_triage_wards([make_ward(patients, tier="icu")], 10)
    assert result["acuity_score"] == 110


def test_spo2_boundary_90_is_normal():
    wards = [make_ward([{"spo2": 90, "hr": 120}])]  # neither < 90 nor > 120
    assert process_triage_wards(wards, 10)["acuity_score"] == 10


def test_exactly_four_flagged_entries_is_not_alert():
    patients = [{"spo2": 0, "hr": 72}] * 4 + [{"spo2": 98, "hr": 72}]
    result = process_triage_wards([make_ward(patients)], 10)
    assert result["status"] == "TRIAGE_STABLE"


def test_zero_default_score_gives_no_urgent_cases():
    result = process_triage_wards([make_ward([{"spo2": 98, "hr": 72}])], 0)
    assert result == {"acuity_score": 0, "status": "NO_URGENT_CASES"}


def test_empty_ward_list_is_no_urgent_cases():
    assert process_triage_wards([], 10)["status"] == "NO_URGENT_CASES"


def test_multiple_wards_accumulate():
    wards = [
        make_ward([{"spo2": 85, "hr": 80}], icu=True),           # 60 + 25
        make_ward([{"spo2": 98, "hr": 72}], accepting=False),    # skipped
        make_ward([{"spo2": 98, "hr": 130, "unconscious": False}]),  # 60
    ]
    assert process_triage_wards(wards, 10)["acuity_score"] == 145


# ---------- extra oxygen manifold tests ----------

def test_oxygen_no_data_none_and_empty():
    assert monitor_oxygen_manifolds([]) == "NO_DATA"
    assert monitor_oxygen_manifolds(None) == "NO_DATA"


def test_oxygen_single_drop_resets_streak():
    # low, normal, low -> never two consecutive lows
    assert monitor_oxygen_manifolds([[3.0, 5.0, 3.0]]) == "PRESSURE_NORMAL"


def test_oxygen_boundary_4_0_is_normal():
    assert monitor_oxygen_manifolds([[4.0, 4.0]]) == "PRESSURE_NORMAL"


def test_oxygen_empty_manifold_then_failure_in_second():
    assert monitor_oxygen_manifolds([[], [3.9, 3.9]]) == "PRESSURE_FAILURE"


def test_oxygen_streak_does_not_carry_across_manifolds():
    assert monitor_oxygen_manifolds([[3.0], [3.0]]) == "PRESSURE_NORMAL"
