"""
Nexlog CLI – nexlog start / test / version
"""

import argparse
import json
import logging
import signal
import sys
from pathlib import Path

from nexlog.collector.ziti import ZitiCollector
from nexlog.parser.parser import EventParser
from nexlog.output.handlers import build_output

__version__ = "0.1.0"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger("nexlog")

def load_config(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        logger.error("Config file not found: %s", path)
        sys.exit(1)
    with p.open() as fh:
        return json.load(fh)

def cmd_start(args):
    cfg = load_config(args.config)
    collector = ZitiCollector(cfg)
    parser    = EventParser(fmt=cfg.get("format", "json"))
    output    = build_output(cfg)

    def _shutdown(sig, frame):
        logger.info("Shutting down…")
        output.close()
        sys.exit(0)

    signal.signal(signal.SIGINT,  _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)
    logger.info("Nexlog %s started", __version__)

    for raw_event in collector.stream():
        try:
            line = parser.parse(raw_event)
            output.write(line)
        except Exception as exc:
            logger.warning("Parse error: %s", exc)

def cmd_test(args):
    sample = {
        "id":           "abc-123",
        "type":         "AuthFail",
        "createdAt":    "2025-01-15T10:30:00Z",
        "actorId":      "user-xyz",
        "actorType":    "identity",
        "entityId":     "identity-xyz",
        "entityType":   "identity",
        "entityName":   "alice@example.com",
        "sourceIp":     "192.168.1.42",
        "controllerId": "ctrl-01",
        "changeDetails": {"reason": "invalid credentials"},
    }
    fmt = args.format or "json_pretty"
    p = EventParser(fmt=fmt)
    print(p.parse(sample))

def cmd_version(_args):
    print(f"Nexlog {__version__}")

def main():
    parser = argparse.ArgumentParser(
        prog="nexlog",
        description="Nexlog – OpenZiti audit log collector & SIEM forwarder",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_start = sub.add_parser("start", help="Start the collector")
    p_start.add_argument("-c", "--config", default="nexlog.json")
    p_start.set_defaults(func=cmd_start)

    p_test = sub.add_parser("test", help="Print a sample parsed event")
    p_test.add_argument("-f", "--format", choices=["json", "json_pretty", "cef"], default="json_pretty")
    p_test.set_defaults(func=cmd_test)

    p_ver = sub.add_parser("version", help="Print version")
    p_ver.set_defaults(func=cmd_version)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()