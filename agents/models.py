"""
Pydantic v2 schemas and data definitions for Privacy Budget Accountant Laplace.
Domain: Privacy-Preserving Federated Healthcare & FHE
Standard: HIPAA Safe Harbor §164.514 / Google SecAgg Standards
"""
import datetime
import re
import math
from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, field_validator


class UrgencyLevel(str, Enum):
    ROUTINE = "ROUTINE"
    ELEVATED = "ELEVATED_RISK"
    CRITICAL_STAT = "CRITICAL_STAT_PANIC"


class SystemIntegrityStatus(str, Enum):
    VALIDATED = "VALIDATED_OPTIMAL"
    DISCORDANT = "DISCORDANT_ANOMALY"
    RECALIBRATION_REQUIRED = "RECALIBRATION_REQUIRED"


# Maximum lengths for input validation to prevent abuse
MAX_ID_LENGTH = 128
MAX_DESCRIPTOR_LENGTH = 64
MAX_ATTRIBUTE_KEY_LENGTH = 64
MAX_ATTRIBUTE_VALUE_LENGTH = 512
MAX_METRIC_VALUE = 1e9


class SystemTaskPayload(BaseModel):
    task_id: str = Field(..., description="Unique task / case identifier")
    target_identifier: str = Field(..., description="Entity, patient key, or genomic/cryptographic target")
    primary_metric: float = Field(..., description="Primary domain measurement or score")
    secondary_metric: float = Field(default=0.0, description="Secondary kinetic or confidence score")
    status_descriptor: str = Field(default="NOMINAL", description="Status code or phenotype descriptor")
    is_critical_flag: bool = Field(default=False, description="Emergency escalation or high priority trigger")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Metadata key-value pairs")
    timestamp: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())

    @field_validator("task_id", "target_identifier")
    @classmethod
    def validate_identifier(cls, v, info):
        if not v or not v.strip():
            raise ValueError(f"{info.field_name} must not be empty")
        if len(v) > MAX_ID_LENGTH:
            raise ValueError(f"{info.field_name} exceeds maximum length of {MAX_ID_LENGTH}")
        # Allow only safe characters: alphanumeric, hyphen, underscore, dot
        if not re.match(r'^[A-Za-z0-9_\-\.]+$', v):
            raise ValueError(f"{info.field_name} contains invalid characters")
        return v.strip()

    @field_validator("status_descriptor")
    @classmethod
    def validate_descriptor(cls, v):
        if len(v) > MAX_DESCRIPTOR_LENGTH:
            raise ValueError(f"status_descriptor exceeds maximum length of {MAX_DESCRIPTOR_LENGTH}")
        return v.strip()

    @field_validator("primary_metric", "secondary_metric")
    @classmethod
    def validate_metric(cls, v, info):
        if not isinstance(v, (int, float)):
            raise ValueError(f"{info.field_name} must be a number")
        if abs(v) > MAX_METRIC_VALUE:
            raise ValueError(f"{info.field_name} exceeds maximum allowed magnitude")
        if math.isnan(v) or math.isinf(v):
            raise ValueError(f"{info.field_name} must be finite")
        return float(v)

    @field_validator("attributes")
    @classmethod
    def validate_attributes(cls, v):
        for key, val in v.items():
            if len(str(key)) > MAX_ATTRIBUTE_KEY_LENGTH:
                raise ValueError(f"Attribute key exceeds maximum length of {MAX_ATTRIBUTE_KEY_LENGTH}")
            if len(str(val)) > MAX_ATTRIBUTE_VALUE_LENGTH:
                raise ValueError(f"Attribute value exceeds maximum length of {MAX_ATTRIBUTE_VALUE_LENGTH}")
        return v


class AgentAlert(BaseModel):
    alert_id: str
    origin_worker: str
    urgency: UrgencyLevel
    summary: str
    technical_details: str
    actionable_remediation: str
    standard_reference: str = "HIPAA Safe Harbor §164.514 / Google SecAgg Standards"
    timestamp: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


class ConsensusDossier(BaseModel):
    dossier_id: str
    system_slug: str = "privacy-budget-accountant-laplace"
    domain: str = "Privacy-Preserving Federated Healthcare & FHE"
    task_id: str
    target_identifier: str
    overall_urgency: UrgencyLevel
    integrity_status: SystemIntegrityStatus
    total_alerts: int
    critical_alerts_count: int
    alerts: List[AgentAlert]
    standard_reference: str = "HIPAA Safe Harbor §164.514 / Google SecAgg Standards"
    consensus_summary: str
    audit_hash: str
    timestamp: str = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()
