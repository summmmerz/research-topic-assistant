# Deployment Notes

This directory contains the Linux deployment artifacts referenced by the thesis:

- `nginx.conf`: reverse proxy for the Flask API and static files.
- `systemd/research-assistant.service`: Gunicorn service definition.
- Performance verification can be run with:

```bash
locust -f tests/performance/locustfile.py --host http://127.0.0.1:5000
```

Neo4j and Redis remain optional at application startup. If they are not
configured or unavailable, the app reports degraded/fallback status and uses
local JSON/SQLite stores.
