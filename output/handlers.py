"""
Nexlog – Output Handlers
stdout, file, syslog (Community)
Elastic, Splunk, Sentinel (Enterprise)
"""

import logging
import socket
from pathlib import Path
from typing import Protocol

logger = logging.getLogger("nexlog.output")

class OutputHandler(Protocol):
    def write(self, line: str) -> None: ...
    def close(self) -> None: ...

class StdoutOutput:
    def write(self, line: str) -> None:
        print(line, flush=True)
    def close(self) -> None:
        pass

class FileOutput:
    def __init__(self, path: str):
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._fh = self._path.open("a", encoding="utf-8")
        logger.info("Writing to file: %s", self._path)
    def write(self, line: str) -> None:
        self._fh.write(line + "\n")
        self._fh.flush()
    def close(self) -> None:
        self._fh.close()

class SyslogOutput:
    FACILITY = 1
    SEVERITY = 6
    def __init__(self, host: str = "127.0.0.1", port: int = 514):
        self._host = host
        self._port = port
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        logger.info("Syslog output → %s:%d", host, port)
    def write(self, line: str) -> None:
        priority = (self.FACILITY * 8) + self.SEVERITY
        msg = f"<{priority}>{line}".encode("utf-8")
        self._sock.sendto(msg, (self._host, self._port))
    def close(self) -> None:
        self._sock.close()

def build_output(config: dict) -> OutputHandler:
    kind = config.get("output", "stdout")
    if kind == "stdout":
        return StdoutOutput()
    if kind == "file":
        return FileOutput(config["output_file"])
    if kind == "syslog":
        return SyslogOutput(
            host=config.get("syslog_host", "127.0.0.1"),
            port=int(config.get("syslog_port", 514)),
        )
    raise ValueError(f"Unknown output '{kind}'. Enterprise outputs require nexlog-enterprise.")