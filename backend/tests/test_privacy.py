import logging

from app.logging_privacy import StripQueryFilter, install


def test_access_log_drops_query_string():
    rec = logging.LogRecord("uvicorn.access", logging.INFO, __file__, 1, '%s - "%s %s HTTP/%s" %d',
                            ("1.2.3.4:5555", "GET", "/api/analyze?lat=37.6&lon=32.75", "1.1", 200), None)
    assert StripQueryFilter().filter(rec)
    msg = rec.getMessage()
    assert "/api/analyze" in msg and "lat=" not in msg and "37.6" not in msg


def test_install_is_idempotent():
    install()
    install()
    log = logging.getLogger("uvicorn.access")
    assert sum(isinstance(f, StripQueryFilter) for f in log.filters) == 1
