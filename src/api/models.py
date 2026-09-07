"""
Pydantic v2 data models for the NinjaOne API.

These models map 1-to-1 with NinjaOne API response shapes,
providing validated, typed access to all API data used by the dashboard.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class DeviceClass(str, Enum):
    WINDOWS_WORKSTATION = "WINDOWS_WORKSTATION"
    WINDOWS_SERVER = "WINDOWS_SERVER"
    MAC = "MAC"
    LINUX_WORKSTATION = "LINUX_WORKSTATION"
    LINUX_SERVER = "LINUX_SERVER"
    ANDROID = "ANDROID"
    APPLE_IOS = "APPLE_IOS"
    VMWARE_VM_HOST = "VMWARE_VM_HOST"
    VMWARE_VM_GUEST = "VMWARE_VM_GUEST"
    HYPER_V_VMM_HOST = "HYPER_V_VMM_HOST"
    HYPER_V_VMM_GUEST = "HYPER_V_VMM_GUEST"
    CLOUD_MONITOR_TARGET = "CLOUD_MONITOR_TARGET"
    NMS_SWITCH = "NMS_SWITCH"
    NMS_ROUTER = "NMS_ROUTER"
    NMS_FIREWALL = "NMS_FIREWALL"
    UNKNOWN = "UNKNOWN"


class NodeApproval(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


# ---------------------------------------------------------------------------
# Organization Models
# ---------------------------------------------------------------------------

class Organization(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    name: str
    description: Optional[str] = None
    plan_name: Optional[str] = None
    location_count: Optional[int] = 0
    locations: Optional[list[dict[str, Any]]] = Field(default_factory=list)
    node_count: Optional[int] = 0
    created: Optional[datetime] = None
    country: Optional[str] = "USA"
    country_code: Optional[str] = "USA"
    region: Optional[str] = "USA / North America"
    city: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class OrganizationSummary(BaseModel):
    """Lightweight org object returned by /v2/organizations."""
    model_config = ConfigDict(populate_by_name=True)

    id: int
    name: str
    description: Optional[str] = None


# ---------------------------------------------------------------------------
# Device / Node Models
# ---------------------------------------------------------------------------

class OSInfo(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    manufacturer: Optional[str] = None
    name: Optional[str] = None        # e.g. "Windows 10 Pro"
    architecture: Optional[str] = None
    service_pack: Optional[str] = None
    version: Optional[str] = None     # e.g. "10.0.19043"
    build_number: Optional[str] = None
    release_id: Optional[str] = None  # e.g. "21H2"


class SystemInfo(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    domain: Optional[str] = None
    chassis_type: Optional[str] = None
    virtual_machine: Optional[bool] = False
    bios_serial_number: Optional[str] = None
    dns_name: Optional[str] = None
    uptime_seconds: Optional[int] = None


class ProcessorInfo(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: Optional[str] = None
    num_cpus: Optional[int] = None
    clock_speed: Optional[float] = None    # MHz
    max_clock_speed: Optional[float] = None


class MemoryInfo(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    capacity: Optional[int] = None    # bytes
    num_slots: Optional[int] = None


class Device(BaseModel):
    """Core device object returned by GET /v2/devices."""
    model_config = ConfigDict(populate_by_name=True)

    id: int
    parent_device_id: Optional[int] = None
    organization_id: int = Field(alias="organizationId")
    location_id: Optional[int] = Field(default=None, alias="locationId")
    node_class: Optional[str] = Field(default=None, alias="nodeClass")
    node_role_id: Optional[int] = Field(default=None, alias="nodeRoleId")
    approval_status: Optional[NodeApproval] = Field(default=None, alias="approvalStatus")
    offline: Optional[bool] = False
    display_name: Optional[str] = Field(default=None, alias="displayName")
    system_name: Optional[str] = Field(default=None, alias="systemName")
    dns_name: Optional[str] = Field(default=None, alias="dnsName")
    ip_address: Optional[str] = Field(default=None, alias="ipAddress")
    public_ip: Optional[str] = Field(default=None, alias="publicIp")
    last_contact: Optional[datetime] = Field(default=None, alias="lastContact")
    last_update: Optional[datetime] = Field(default=None, alias="lastUpdate")
    last_seen: Optional[datetime] = Field(default=None, alias="lastSeen")
    created: Optional[datetime] = None
    os: Optional[OSInfo] = None
    system_info: Optional[SystemInfo] = Field(default=None, alias="systemInfo")
    processor_info: Optional[ProcessorInfo] = Field(default=None, alias="processorInfo")
    memory: Optional[MemoryInfo] = None
    tags: Optional[list[str]] = Field(default_factory=list)
    custom_fields: Optional[dict[str, Any]] = Field(default_factory=dict)
    references: Optional[dict[str, Any]] = Field(default_factory=dict)

    # Inferred regional & infrastructure metadata
    region: Optional[str] = None
    country: Optional[str] = None
    location_name: Optional[str] = None
    hosting_type: Optional[str] = None
    approved_patch_count: Optional[int] = 0

    @model_validator(mode="before")
    @classmethod
    def preprocess_device_dict(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Map 'system' to 'systemInfo' if present
            if "system" in data and "systemInfo" not in data and "system_info" not in data:
                data["systemInfo"] = data["system"]
            # Extract approved patch count if present
            cf = data.get("customFields") or data.get("custom_fields") or {}
            for k in ["approvedPatchCount", "approved_patch_count", "Approved Patch Count", "approvedPatches"]:
                if k in cf and cf[k] is not None:
                    try:
                        data["approved_patch_count"] = int(cf[k])
                        break
                    except (ValueError, TypeError):
                        pass
        return data

    @field_validator("approval_status", mode="before")
    @classmethod
    def coerce_approval(cls, v):
        if isinstance(v, str):
            try:
                return NodeApproval(v.upper())
            except ValueError:
                return NodeApproval.PENDING
        return v

    @property
    def is_server(self) -> bool:
        """True if the device is classified as a server node."""
        server_classes = {
            DeviceClass.WINDOWS_SERVER,
            DeviceClass.LINUX_SERVER,
            DeviceClass.VMWARE_VM_HOST,
            DeviceClass.HYPER_V_VMM_HOST,
        }
        try:
            return DeviceClass(self.node_class) in server_classes
        except (ValueError, TypeError):
            # Fallback: detect "Server" in OS name
            if self.os and self.os.name:
                return "Server" in self.os.name
            return False

    @property
    def os_display(self) -> str:
        """Human-friendly OS name."""
        if self.os:
            parts = [p for p in [self.os.name, self.os.release_id] if p]
            return " ".join(parts) if parts else "Unknown"
        return "Unknown"

    @property
    def is_online(self) -> bool:
        return not self.offline


# ---------------------------------------------------------------------------
# Activity / Patch Models
# ---------------------------------------------------------------------------

class Activity(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: Optional[int] = None
    activity_time: Optional[datetime] = Field(default=None, alias="activityTime")
    device_id: Optional[int] = Field(default=None, alias="deviceId")
    device_name: Optional[str] = Field(default=None, alias="deviceName")
    organization_id: Optional[int] = Field(default=None, alias="organizationId")
    type: Optional[str] = None
    status: Optional[str] = None
    status_code: Optional[str] = Field(default=None, alias="statusCode")
    subject: Optional[str] = None
    data: Optional[dict[str, Any]] = None
