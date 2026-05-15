"""
Nexlog – Event Parser
Normalises raw OpenZiti audit events into JSON or CEF format.
"""

import json
from datetime import datetime, timezone
from typing import Literal

OutputFormat = Literal["json", "cef", "json_pretty"]

CEF_VENDOR  = "Nexlog"
CEF_PRODUCT = "ZitiAudit"
CEF_VERSION = "1.0"

EVENT_MAP = {
    "EdgeRouterCreate":    ("100", "Edge Router Created",    3),
    "EdgeRouterDelete":    ("101", "Edge Router Deleted",    5),
    "ServiceCreate":       ("200", "Service Created",        3),
    "ServiceDelete":       ("201", "Service Deleted",        5),
    "ServicePolicyCreate": ("210", "Service Policy Created", 3),
    "ServicePolicyDelete": ("211", "Service Policy Deleted", 5),
    "IdentityCreate":      ("300", "Identity Created",       3),
    "IdentityDelete":      ("301", "Identity Deleted",       7),
    "AuthSuccess":         ("400", "Authentication Success", 2),
    "AuthFail":            ("401", "Authentication Failed",  8),
    "SessionCreate":       ("500", "Session Created",        2),
    "SessionDelete":       ("501", "Session Deleted",        2),
    "ApiSessionCreate":    ("510", "API Session Created",    2),
    "ApiSessionDelete":    ("511", "API Session Deleted",    2),
    "PostureCheckCreate":  ("600", "Posture Check Created",  3),
    "PostureCheckFail":    ("601", "Posture Check Failed",   8),
    "EnrollmentCreate":    ("700", "Enrollment Created",     3),
    "EnrollmentDelete":    ("701", "Enrollment Deleted",     5),
}

def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _cef_escape(value: str) -> str:
    return str(value).replace("\\", "\\\\").replace("|", "\\|").replace("=", "\\=")

class EventParser:
    def __init__(self, fmt: OutputFormat = "json"):
        self.fmt = fmt

    def parse(self, raw: dict) -> str:
        normalized = self._normalize(raw)
        if self.fmt == "cef":
            return self._to_cef(normalized)
        if self.fmt == "json_pretty":
            return json.dumps(normalized, indent=2)
        return json.dumps(normalized)

    def _normalize(self, raw: dict) -> dict:
        event_type = raw.get("type", "Unknown")
        sig_id, sig_name, severity = EVENT_MAP.get(event_type, ("999", event_type, 5))
        return {
            "nexlog_version": "1",
            "timestamp":      raw.get("createdAt", _iso_now()),
            "event_id":       raw.get("id", ""),
            "event_type":     event_type,
            "severity":       severity,
            "sig_id":         sig_id,
            "sig_name":       sig_name,
            "actor_id":       raw.get("actorId", ""),
            "actor_type":     raw.get("actorType", ""),
            "entity_id":      raw.get("entityId", ""),
            "entity_type":    raw.get("entityType", ""),
            "entity_name":    raw.get("entityName", ""),
            "change_summary": raw.get("changeDetails", {}),
            "source_ip":      raw.get("sourceIp", ""),
            "controller":     raw.get("controllerId", ""),
            "tags":           raw.get("tags", {}),
        }

    def _to_cef(self, n: dict) -> str:
        header = "|".join([
            "CEF:0",
            _cef_escape(CEF_VENDOR),
            _cef_escape(CEF_PRODUCT),
            _cef_escape(CEF_VERSION),
            _cef_escape(n["sig_id"]),
            _cef_escape(n["sig_name"]),
            str(n["severity"]),
        ])
        ext_pairs = {
            "rt":      n["timestamp"],
            "suser":   n["actor_id"],
            "stype":   n["actor_type"],
            "dvchost": n["controller"],
            "src":     n["source_ip"],
            "cs1":     n["entity_id"],
            "cs1Label":"entityId",
            "cs2":     n["entity_type"],
            "cs2Label":"entityType",
            "cs3":     n["entity_name"],
            "cs3Label":"entityName",
            "msg":     json.dumps(n["change_summary"]),
        }
        extension = " ".join(
            f"{k}={_cef_escape(v)}" for k, v in ext_pairs.items() if v
        )
        return f"{header} {extension}"