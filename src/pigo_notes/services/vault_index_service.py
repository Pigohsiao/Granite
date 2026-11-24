"""Per-Vault transactional SQLite cache for search and note relationships."""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from contextlib import closing
from pathlib import Path
from threading import Event
from typing import Iterable

from pigo_notes.index_models import IndexUpdateReport, LinkResolution, SearchHit, TagCount
from pigo_notes.services.link_resolver import LinkResolver, LinkResolverIndex
from pigo_notes.services.note_parser import NoteParser
from pigo_notes.services.vault_service import VaultService


class VaultIndexService:
    SCHEMA_VERSION = "1"
    PARSER_VERSION = "1"

    def __init__(self, vault_root: Path, database_path: Path) -> None:
        self.vault_root = vault_root.resolve()
        self.database_path = database_path.resolve()
        if self._is_within(self.database_path, self.vault_root):
            raise ValueError("The index database must be stored outside the Vault")
        self._vault = VaultService(self.vault_root)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def refresh(self, *, full: bool = False, cancel: Event | None = None) -> IndexUpdateReport:
        cancel = cancel or Event()
        if cancel.is_set():
            return IndexUpdateReport(cancelled=True)
        files, scan_errors = self._scan_files()
        updated = removed = 0
        errors = list(scan_errors)
        with closing(self._connect()) as connection, connection:
            connection.execute("BEGIN IMMEDIATE")
            existing_rows = {
                Path(row[0]): (row[1], row[2])
                for row in connection.execute("SELECT relative_path, size, mtime_ns FROM notes")
            }
            for relative_path, (size, mtime_ns) in files.items():
                if cancel.is_set():
                    connection.rollback()
                    return IndexUpdateReport(len(files), updated, 0, tuple(errors), cancelled=True)
                if not full and existing_rows.get(relative_path) == (size, mtime_ns):
                    continue
                try:
                    source = self._vault.read_note(relative_path)
                    self._upsert(connection, relative_path, source, size=size, mtime_ns=mtime_ns)
                    updated += 1
                except (OSError, UnicodeError, ValueError) as error:
                    errors.append(f"{relative_path.as_posix()}: {error}")

            if not scan_errors:
                missing = set(existing_rows) - set(files)
                for relative_path in missing:
                    connection.execute("DELETE FROM notes WHERE relative_path = ?", (relative_path.as_posix(),))
                removed = len(missing)
            self._resolve_all_links(connection)
            connection.execute(
                "INSERT OR REPLACE INTO metadata(key, value) VALUES('last_updated', ?)",
                (str(__import__("time").time()),),
            )
            connection.commit()
        return IndexUpdateReport(scanned=len(files), updated=updated, removed=removed, errors=tuple(errors))

    def upsert(self, relative_path: Path, source: str) -> None:
        self._validate_relative_path(relative_path)
        try:
            stat = (self.vault_root / relative_path).stat()
            size, mtime_ns = stat.st_size, stat.st_mtime_ns
        except OSError:
            size, mtime_ns = len(source.encode("utf-8")), 0
        with closing(self._connect()) as connection, connection:
            connection.execute("BEGIN IMMEDIATE")
            self._upsert(connection, relative_path, source, size=size, mtime_ns=mtime_ns)
            self._resolve_all_links(connection)
            connection.commit()

    def remove(self, relative_paths: Iterable[Path]) -> None:
        with closing(self._connect()) as connection, connection:
            connection.execute("BEGIN IMMEDIATE")
            for relative_path in relative_paths:
                self._validate_relative_path(relative_path)
                connection.execute("DELETE FROM notes WHERE relative_path = ?", (relative_path.as_posix(),))
            self._resolve_all_links(connection)
            connection.commit()

    def search(
        self,
        query: str,
        tag: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[SearchHit]:
        needle = query.strip().casefold()
        normalized_tag = tag.strip().lstrip("#").casefold() if tag and tag.strip() else None
        if not needle and normalized_tag is None:
            return []
        clauses: list[str] = []
        parameters: list[object] = []
        if needle:
            clauses.append("instr(search_folded, ?) > 0")
            parameters.append(needle)
        if normalized_tag is not None:
            clauses.append("EXISTS (SELECT 1 FROM note_tags t WHERE t.path = notes.relative_path AND t.tag_folded = ?)")
            parameters.append(normalized_tag)
        parameters.extend((min(max(1, limit), 500), max(0, offset)))
        sql = (
            "SELECT relative_path, body_text, search_folded FROM notes WHERE "
            + " AND ".join(clauses)
            + " ORDER BY path_folded LIMIT ? OFFSET ?"
        )
        results: list[SearchHit] = []
        with closing(self._connect()) as connection, connection:
            for raw_path, body_text, _ in connection.execute(sql, parameters):
                snippet = self._snippet(body_text, needle) if needle else self._snippet(body_text, "")
                results.append(SearchHit(Path(raw_path), snippet))
        return results

    def backlinks(self, target: Path, limit: int = 100) -> list[Path]:
        self._validate_relative_path(target)
        with closing(self._connect()) as connection, connection:
            rows = connection.execute(
                "SELECT DISTINCT source_path FROM note_links WHERE status = 'resolved' AND resolved_path = ? ORDER BY source_folded LIMIT ?",
                (target.as_posix(), min(max(1, limit), 500)),
            )
            return [Path(row[0]) for row in rows]

    def properties(self, path: Path) -> dict[str, object]:
        self._validate_relative_path(path)
        with closing(self._connect()) as connection, connection:
            row = connection.execute("SELECT properties_json FROM notes WHERE relative_path = ?", (path.as_posix(),)).fetchone()
        if row is None:
            return {}
        value = json.loads(row[0])
        return value if isinstance(value, dict) else {}

    def tags(self) -> list[TagCount]:
        with closing(self._connect()) as connection, connection:
            return [
                TagCount(tag=row[0], count=row[1])
                for row in connection.execute(
                    "SELECT tag, COUNT(DISTINCT path) AS count FROM note_tags GROUP BY tag_folded ORDER BY tag_folded"
                )
            ]

    def resolve(self, source_path: Path, target: str) -> LinkResolution:
        self._validate_relative_path(source_path)
        with closing(self._connect()) as connection, connection:
            candidates = [Path(row[0]) for row in connection.execute("SELECT relative_path FROM notes")]
        return LinkResolver.resolve(source_path, target, candidates)

    @staticmethod
    def _snippet(body: str, query: str) -> str:
        if query:
            for line in body.splitlines():
                if query in line.casefold():
                    return line.strip()[:160]
        return next((line.strip()[:160] for line in body.splitlines() if line.strip()), "")

    @staticmethod
    def _is_within(path: Path, root: Path) -> bool:
        try:
            path.relative_to(root)
            return True
        except ValueError:
            return False

    def _validate_relative_path(self, relative_path: Path) -> None:
        if relative_path.is_absolute() or ".." in relative_path.parts or relative_path.suffix.casefold() != ".md":
            raise ValueError("Only Vault-relative Markdown paths are allowed")
        candidate = (self.vault_root / relative_path).resolve()
        if not self._is_within(candidate, self.vault_root):
            raise ValueError("Path is outside the Vault")

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path, timeout=10)
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    def _initialize(self) -> None:
        with closing(self._connect()) as connection, connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS notes (
                    relative_path TEXT PRIMARY KEY,
                    path_folded TEXT NOT NULL,
                    size INTEGER NOT NULL,
                    mtime_ns INTEGER NOT NULL,
                    fingerprint TEXT NOT NULL,
                    search_folded TEXT NOT NULL,
                    body_text TEXT NOT NULL,
                    properties_json TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS note_tags (
                    path TEXT NOT NULL REFERENCES notes(relative_path) ON DELETE CASCADE,
                    tag TEXT NOT NULL,
                    tag_folded TEXT NOT NULL,
                    PRIMARY KEY(path, tag_folded)
                );
                CREATE TABLE IF NOT EXISTS note_links (
                    source_path TEXT NOT NULL REFERENCES notes(relative_path) ON DELETE CASCADE,
                    link_index INTEGER NOT NULL,
                    target TEXT NOT NULL,
                    fragment TEXT,
                    status TEXT NOT NULL,
                    resolved_path TEXT,
                    candidates_json TEXT NOT NULL,
                    source_folded TEXT NOT NULL,
                    PRIMARY KEY(source_path, link_index)
                );
                CREATE INDEX IF NOT EXISTS note_links_resolved_idx
                    ON note_links(resolved_path, source_folded);
                """
            )
            rows = dict(connection.execute("SELECT key, value FROM metadata"))
            expected_identity = str(self.vault_root).casefold()
            if rows.get("vault_identity") not in (None, expected_identity):
                raise ValueError("Index database belongs to a different Vault")
            if rows.get("schema_version") not in (None, self.SCHEMA_VERSION):
                raise ValueError("Index database schema version is unsupported")
            connection.executemany(
                "INSERT OR REPLACE INTO metadata(key, value) VALUES(?, ?)",
                (("vault_identity", expected_identity), ("schema_version", self.SCHEMA_VERSION), ("parser_version", self.PARSER_VERSION)),
            )

    def _scan_files(self) -> tuple[dict[Path, tuple[int, int]], list[str]]:
        files: dict[Path, tuple[int, int]] = {}
        errors: list[str] = []

        def on_error(error: OSError) -> None:
            errors.append(f"scan: {error}")

        for current, directories, filenames in os.walk(self.vault_root, topdown=True, followlinks=False, onerror=on_error):
            current_path = Path(current)
            kept: list[str] = []
            for name in directories:
                candidate = current_path / name
                if name.startswith(".") or name.casefold() in {".git", ".obsidian"}:
                    continue
                if candidate.is_symlink() or (hasattr(candidate, "is_junction") and candidate.is_junction()):
                    continue
                kept.append(name)
            directories[:] = kept
            for name in filenames:
                if not name.casefold().endswith(".md"):
                    continue
                candidate = current_path / name
                if candidate.is_symlink():
                    continue
                try:
                    relative = candidate.relative_to(self.vault_root)
                    stat = candidate.stat()
                    files[relative] = (stat.st_size, stat.st_mtime_ns)
                except OSError as error:
                    errors.append(f"{candidate}: {error}")
        return files, errors

    def _upsert(self, connection: sqlite3.Connection, path: Path, source: str, *, size: int, mtime_ns: int) -> None:
        self._validate_relative_path(path)
        parsed = NoteParser.parse(source)
        path_text = path.as_posix()
        body = parsed.body
        searchable = f"{path.stem}\n{body}"
        fingerprint = hashlib.sha256(source.encode("utf-8")).hexdigest()
        connection.execute(
            """INSERT OR REPLACE INTO notes
            (relative_path, path_folded, size, mtime_ns, fingerprint, search_folded, body_text, properties_json)
            VALUES(?, ?, ?, ?, ?, ?, ?, ?)""",
            (path_text, path_text.casefold(), size, mtime_ns, fingerprint, searchable.casefold(), body,
             json.dumps(parsed.properties, ensure_ascii=False, separators=(",", ":"))),
        )
        connection.execute("DELETE FROM note_tags WHERE path = ?", (path_text,))
        connection.executemany(
            "INSERT OR IGNORE INTO note_tags(path, tag, tag_folded) VALUES(?, ?, ?)",
            ((path_text, tag, tag.casefold()) for tag in parsed.tags),
        )
        connection.execute("DELETE FROM note_links WHERE source_path = ?", (path_text,))
        connection.executemany(
            """INSERT INTO note_links
            (source_path, link_index, target, fragment, status, resolved_path, candidates_json, source_folded)
            VALUES(?, ?, ?, ?, 'missing', NULL, '[]', ?)""",
            ((path_text, index, link.target, link.fragment, path_text.casefold()) for index, link in enumerate(parsed.wikilinks)),
        )

    def _resolve_all_links(self, connection: sqlite3.Connection) -> None:
        candidates = [Path(row[0]) for row in connection.execute("SELECT relative_path FROM notes")]
        resolver = LinkResolverIndex(candidates)
        for source_path, link_index, target, fragment in connection.execute(
            "SELECT source_path, link_index, target, fragment FROM note_links"
        ).fetchall():
            target_with_fragment = f"{target}#{fragment}" if fragment else target
            result = resolver.resolve(Path(source_path), target_with_fragment)
            connection.execute(
                """UPDATE note_links SET status = ?, resolved_path = ?, candidates_json = ?
                WHERE source_path = ? AND link_index = ?""",
                (result.status, result.candidates[0].as_posix() if result.status == "resolved" else None,
                 json.dumps([path.as_posix() for path in result.candidates]), source_path, link_index),
            )
