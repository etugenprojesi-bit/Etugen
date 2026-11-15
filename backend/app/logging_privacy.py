"""Privacy for server logs (docs/PRIVACY.md).

Uvicorn's access log writes the client address together with the full
request path, which for GET /api/... includes lat/lon. This filter removes
the query string from access-log records, so coordinates and IP addresses are
never logged together.
"""

from __future__ import annotations

import logging


class StripQueryFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        args = record.args
        # uvicorn.access: (client_addr, method, full_path, http_version, status_code)
        if isinstance(args, tuple) and len(args) == 5 and isinstance(args[2], str):
            record.args = (args[0], args[1], args[2].split("?", 1)[0], args[3], args[4])
        return True


def install() -> None:
    log = logging.getLogger("uvicorn.access")
    if not any(isinstance(f, StripQueryFilter) for f in log.filters):
        log.addFilter(StripQueryFilter())
