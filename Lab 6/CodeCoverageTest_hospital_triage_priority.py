"""Code (line) coverage tests for hospital_triage_priority.py.

Run from the 'Lab 6' folder:
    coverage run -m pytest CodeCoverageTest_hospital_triage_priority.py
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
