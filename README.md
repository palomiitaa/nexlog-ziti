# Nexlog

> OpenZiti audit log collector & SIEM forwarder

Nexlog bridges your [OpenZiti](https://openziti.io) zero-trust network and your SIEM.
It continuously polls the Ziti Management API, normalises every audit event into
structured **JSON** or **CEF**, and forwards the stream to your log pipeline.

```
OpenZiti Controller  →  Nexlog  →  stdout / file / syslog / Elastic / Splunk
```

![License](https://img.shields.io/badge/license-Apache%202.0-green)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Version](https://img.shields.io/badge/version-0.1.0-teal)

---

## Why Nexlog?

OpenZiti generates rich audit events — identity changes, auth failures, service
policy updates, posture check results — but ships no built-in SIEM integration.
Nexlog fills that gap.

| Without Nexlog | With Nexlog |
|---|---|
| Raw JSON buried in controller logs | Structured, normalised events |
| No SIEM visibility | Works with Elastic, Splunk, Wazuh, Sentinel |
| Manual log scraping | Continuous, low-latency polling |
| No severity scoring | Every event carries a severity 1–10 |

---

## Quick start

### Install

```bash
pip install nexlog
```

Or from source:

```bash
git clone https://github.com/palomiitaa/nexlog
cd nexlog
pip install -e .
```

### Configure

```bash
cp nexlog.example.json nexlog.json
```

Edit `nexlog.json`:

```json
{
  "ziti_url":      "https://your-controller:1280",
  "username":      "admin",
  "password":      "your-password",
  "verify_tls":    false,
  "poll_interval": 5,
  "format":        "json",
  "output":        "stdout"
}
```

### Run

```bash
nexlog start -c nexlog.json
```

Test with a sample event:

```bash
nexlog test --format json_pretty
```

---

## Output formats

### JSON

```json
{
  "nexlog_version": "1",
  "timestamp":      "2025-01-15T10:30:00Z",
  "event_type":     "AuthFail",
  "severity":       8,
  "sig_name":       "Authentication Failed",
  "actor_id":       "user-xyz",
  "entity_name":    "alice@example.com",
  "source_ip":      "192.168.1.42",
  "controller":     "ctrl-01"
}
```

### CEF (Common Event Format)

```
CEF:0|Nexlog|ZitiAudit|1.0|401|Authentication Failed|8 rt=2025-01-15T10:30:00Z suser=user-xyz src=192.168.1.42
```

CEF works out-of-the-box with Splunk, ArcSight, Wazuh, QRadar, and any syslog pipeline.

---

## Supported event types

| Category | Events |
|---|---|
| Auth | AuthSuccess, AuthFail |
| Session | SessionCreate, SessionDelete, ApiSessionCreate, ApiSessionDelete |
| Identity | IdentityCreate, IdentityDelete |
| Service | ServiceCreate, ServiceDelete |
| Service Policy | ServicePolicyCreate, ServicePolicyDelete |
| Edge Router | EdgeRouterCreate, EdgeRouterDelete |
| Posture Check | PostureCheckCreate, PostureCheckFail |
| Enrollment | EnrollmentCreate, EnrollmentDelete |

---

## Output destinations

| Destination | Community | Enterprise |
|---|---|---|
| stdout | ✅ | ✅ |
| File (JSONL) | ✅ | ✅ |
| Syslog (UDP) | ✅ | ✅ |
| Elastic / OpenSearch | — | ✅ |
| Splunk HEC | — | ✅ |
| Microsoft Sentinel | — | ✅ |
| Webhook / HTTP | — | ✅ |
| Multi-controller | — | ✅ |

---

## SIEM integration examples

### Wazuh

```xml
<localfile>
  <log_format>syslog</log_format>
  <location>/var/log/nexlog/events.jsonl</location>
</localfile>
```

### Filebeat / Elastic Agent

```yaml
filebeat.inputs:
  - type: log
    paths:
      - /var/log/nexlog/events.jsonl
    json.keys_under_root: true
```

### Splunk (file monitor)

```ini
[monitor:///var/log/nexlog/events.jsonl]
sourcetype = nexlog:ziti
index      = security
```

---

## Configuration reference

| Key | Default | Description |
|---|---|---|
| `ziti_url` | — | Controller URL e.g. `https://ctrl:1280` |
| `username` | — | Admin username |
| `password` | — | Admin password |
| `api_token` | — | Static session token (alternative to user/pass) |
| `verify_tls` | `true` | Set `false` for self-signed certs |
| `poll_interval` | `5` | Seconds between API polls |
| `format` | `json` | `json`, `json_pretty`, or `cef` |
| `output` | `stdout` | `stdout`, `file`, or `syslog` |
| `output_file` | — | Path for file output |
| `syslog_host` | `127.0.0.1` | Syslog destination host |
| `syslog_port` | `514` | Syslog destination port |

---

## Project structure

```
nexlog/
├── nexlog/
│   ├── collector/
│   │   └── ziti.py          # OpenZiti Management API client
│   ├── parser/
│   │   └── parser.py        # JSON + CEF normalisation
│   ├── output/
│   │   └── handlers.py      # stdout / file / syslog
│   └── cli/
│       └── main.py          # nexlog CLI
├── site/
│   └── index.html           # Landing page
├── nexlog.example.json
├── pyproject.toml
├── LICENSE                  # Apache 2.0
└── LICENSE-ENTERPRISE       # Commercial license
```

---

## Enterprise

**Nexlog Enterprise** adds:

- Native Elastic / OpenSearch output (index templates included)
- Splunk HEC output
- Microsoft Sentinel output
- HTTP / Webhook output
- Multi-controller support
- Alerting engine (threshold-based rules)
- Docker image + Helm chart
- Priority support & SLA

Contact: **admin@cyberfox-swiss.ch**

---

## Contributing

Pull requests are welcome. Please open an issue first for larger changes.

---

## License

Community edition: [Apache 2.0](LICENSE)

Enterprise edition: Commercial license — see [LICENSE-ENTERPRISE](LICENSE-ENTERPRISE) or contact admin@cyberfox-swiss.ch