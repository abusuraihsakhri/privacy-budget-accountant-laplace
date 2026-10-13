"""
Security & Input Validation Tests for Privacy Budget Accountant Laplace.
Tests for PHI guard, input validation, audit trail security, and error handling.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import os
import warnings
import pytest
from agents.base import PHIGuard, AuditLogger, AuditTrail, SecurityException
from agents.models import SystemTaskPayload, UrgencyLevel, SystemIntegrityStatus
from agents.supervisor import SystemSupervisor


class TestPHIGuard:
    """Tests for PHI outbound guard enforcement."""

    def test_mrn_pattern_blocked(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Patient MRN-994827 blood culture positive")

    def test_ssn_pattern_blocked(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("SSN: 123-45-6789")

    def test_phone_pattern_blocked(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Call patient at 555-123-4567")

    def test_email_pattern_blocked(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Email: patient@example.com")

    def test_dob_pattern_blocked(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("DOB: 01/15/1985")

    def test_patient_name_blocked(self):
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Patient Name: John Doe")

    def test_clean_text_passes(self):
        PHIGuard.assert_no_phi("Analytical assay specimen KEY-001 optimal")
        PHIGuard.assert_no_phi("Target identifier: TARGET-ALPHA-01")

    def test_empty_text_passes(self):
        PHIGuard.assert_no_phi("")

    def test_none_text_passes(self):
        PHIGuard.assert_no_phi(None)

    def test_redact_phi(self):
        result = PHIGuard.redact_phi("Patient MRN-12345 needs follow-up")
        assert "[REDACTED_IDENTIFIER]" in result
        assert "MRN-12345" not in result


class TestInputValidation:
    """Tests for SystemTaskPayload input validation."""

    def test_valid_payload(self):
        payload = SystemTaskPayload(
            task_id="TASK-001",
            target_identifier="TARGET-01",
            primary_metric=15.0,
            secondary_metric=5.0,
        )
        assert payload.task_id == "TASK-001"
        assert payload.primary_metric == 15.0

    def test_empty_task_id_rejected(self):
        with pytest.raises(ValueError, match="must not be empty"):
            SystemTaskPayload(
                task_id="",
                target_identifier="TARGET-01",
                primary_metric=15.0,
            )

    def test_invalid_characters_in_task_id(self):
        with pytest.raises(ValueError, match="invalid characters"):
            SystemTaskPayload(
                task_id="TASK 001; DROP TABLE",
                target_identifier="TARGET-01",
                primary_metric=15.0,
            )

    def test_task_id_too_long(self):
        with pytest.raises(ValueError, match="exceeds maximum length"):
            SystemTaskPayload(
                task_id="A" * 200,
                target_identifier="TARGET-01",
                primary_metric=15.0,
            )

    def test_path_traversal_in_task_id(self):
        with pytest.raises(ValueError, match="invalid characters"):
            SystemTaskPayload(
                task_id="../../../etc/passwd",
                target_identifier="TARGET-01",
                primary_metric=15.0,
            )

    def test_nan_metric_rejected(self):
        with pytest.raises(ValueError, match="must be finite"):
            SystemTaskPayload(
                task_id="TASK-001",
                target_identifier="TARGET-01",
                primary_metric=float("nan"),
            )

    def test_inf_metric_rejected(self):
        with pytest.raises(ValueError, match="must be finite|exceeds maximum"):
            SystemTaskPayload(
                task_id="TASK-001",
                target_identifier="TARGET-01",
                primary_metric=float("inf"),
            )

    def test_metric_too_large(self):
        with pytest.raises(ValueError, match="exceeds maximum"):
            SystemTaskPayload(
                task_id="TASK-001",
                target_identifier="TARGET-01",
                primary_metric=1e10,
            )


class TestAuditTrailSecurity:
    """Tests for HMAC audit trail security."""

    def test_audit_trail_integrity(self):
        trail = AuditTrail(secret_key="test-key-123")
        trail.log("test-actor", "tier-1", "TEST_EVENT", {"data": "value1"})
        trail.log("test-actor", "tier-1", "TEST_EVENT", {"data": "value2"})
        assert trail.verify_integrity() is True

    def test_audit_trail_tamper_detection(self):
        trail = AuditTrail(secret_key="test-key-123")
        trail.log("test-actor", "tier-1", "TEST_EVENT", {"data": "value1"})
        trail.log("test-actor", "tier-1", "TEST_EVENT", {"data": "value2"})
        # Tamper with the chain by modifying prev_hash of second entry
        trail.logs[1]["prev_hash"] = "tampered_chain_hash"
        assert trail.verify_integrity() is False

    def test_content_tampering_with_same_chain_is_detected(self):
        trail = AuditTrail(secret_key="test-key-123")
        trail.log("actor", "tier", "EVENT", {"a": 1})
        trail.logs[0]["event_type"] = "FORGED_EVENT"
        assert trail.verify_integrity() is False

    def test_signature_tampering_is_detected(self):
        trail = AuditTrail(secret_key="test-key-123")
        trail.log("actor", "tier", "EVENT", {"a": 1})
        trail.logs[0]["current_hash"] = "0" * 64
        assert trail.verify_integrity() is False

    def test_get_trail_returns_snapshot(self):
        trail = AuditTrail(secret_key="test-key-123")
        trail.log("actor", "tier", "EVENT", {"a": 1})
        trail.get_trail()[0]["event_type"] = "FORGED_EVENT"
        assert trail.verify_integrity() is True

    def test_missing_secret_key_warns(self):
        # Clear env var if set
        original = os.environ.pop("AUDIT_SECRET_KEY", None)
        try:
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                trail = AuditTrail()
                assert len(w) == 1
                assert "AUDIT_SECRET_KEY not set" in str(w[0].message)
        finally:
            if original:
                os.environ["AUDIT_SECRET_KEY"] = original

    def test_custom_secret_key_no_warning(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            trail = AuditTrail(secret_key="my-custom-key")
            # Filter for our specific warning
            relevant = [x for x in w if "AUDIT_SECRET_KEY" in str(x.message)]
            assert len(relevant) == 0

    def test_audit_log_phi_blocked(self):
        trail = AuditTrail(secret_key="test-key-123")
        with pytest.raises(SecurityException):
            trail.log("test-actor", "tier-1", "TEST", {"data": "MRN-12345"})


class TestCLIBatchErrorHandling:
    """Tests for CLI batch mode error handling."""

    def test_missing_input_file_returns_error(self):
        from cli import main
        result = main(["batch", "-i", "nonexistent_file_xyz.csv"])
        assert result == 1

    def test_batch_with_valid_csv(self, tmp_path):
        from cli import main
        # Create a test CSV
        csv_file = tmp_path / "test_input.csv"
        csv_file.write_text(
            "task_id,target_identifier,primary_metric,secondary_metric,status_descriptor\n"
            "TASK-TEST-01,TARGET-01,15.0,5.0,NOMINAL\n"
        )
        output_file = tmp_path / "test_output.csv"
        result = main(["batch", "-i", str(csv_file), "-o", str(output_file)])
        assert result == 0
        assert output_file.exists()

    def test_batch_skips_invalid_rows(self, tmp_path, capsys):
        from cli import main
        # Create a test CSV with one invalid row
        csv_file = tmp_path / "test_invalid.csv"
        csv_file.write_text(
            "task_id,target_identifier,primary_metric,secondary_metric,status_descriptor\n"
            "TASK-TEST-01,TARGET-01,15.0,5.0,NOMINAL\n"
            "TASK-TEST-02,TARGET-02,invalid_metric,5.0,NOMINAL\n"
            "TASK-TEST-03,TARGET-03,20.0,8.0,DISCORDANT\n"
        )
        output_file = tmp_path / "test_output2.csv"
        result = main(["batch", "-i", str(csv_file), "-o", str(output_file)])
        assert result == 0
        # Check warning was printed
        captured = capsys.readouterr()
        assert "Skipping row" in captured.err
