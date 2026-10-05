# -*- coding: utf-8 -*-
"""Optional Neo4j driver wrapper with graceful fallback semantics."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional


class Neo4jClient:
    """Small wrapper around the official Neo4j driver.

    The project must still run on machines without Neo4j or the driver
    installed, so import and connection failures are stored in ``last_error``
    instead of being raised during application startup.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.driver = None
        self.last_error: Optional[str] = None
        self.database = self.config.get("database") or "neo4j"
        self._connect()

    @property
    def available(self) -> bool:
        return self.driver is not None

    def _connect(self) -> None:
        uri = self.config.get("uri")
        username = self.config.get("username")
        password = self.config.get("password")
        if not uri or not username or not password or str(password).startswith("your_"):
            self.last_error = "neo4j_not_configured"
            return

        try:
            from neo4j import GraphDatabase

            self.driver = GraphDatabase.driver(uri, auth=(username, password))
            with self.driver.session(database=self.database) as session:
                session.run("RETURN 1 AS ok").single()
            self.last_error = None
        except Exception as exc:  # pragma: no cover - depends on local service
            self.driver = None
            self.last_error = str(exc)

    def close(self) -> None:
        if self.driver:
            self.driver.close()
            self.driver = None

    def run_read(
        self, cypher: str, params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        if not self.driver:
            raise RuntimeError(self.last_error or "neo4j_unavailable")
        with self.driver.session(database=self.database, default_access_mode="READ") as session:
            result = session.run(cypher, params or {})
            return [dict(record) for record in result]

    def run_write(
        self, cypher: str, params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        if not self.driver:
            raise RuntimeError(self.last_error or "neo4j_unavailable")
        with self.driver.session(database=self.database, default_access_mode="WRITE") as session:
            result = session.run(cypher, params or {})
            return [dict(record) for record in result]

    def write_batch(self, statements: Iterable[Dict[str, Any]]) -> int:
        count = 0
        for statement in statements:
            self.run_write(statement["cypher"], statement.get("params"))
            count += 1
        return count
