"""Deterministic, Vault-relative resolution for Markdown wikilinks."""

from __future__ import annotations

from pathlib import Path, PurePosixPath
from urllib.parse import unquote

from pigo_notes.index_models import LinkResolution


class LinkResolver:
    @classmethod
    def resolve(
        cls,
        source_path: Path | str,
        target: str,
        candidates: list[Path] | tuple[Path, ...],
    ) -> LinkResolution:
        return LinkResolverIndex(candidates).resolve(source_path, target)


class LinkResolverIndex:
    """Pre-index candidate paths so resolving many links is O(1) lookup per link."""

    def __init__(self, candidates: list[Path] | tuple[Path, ...]) -> None:
        self.candidates = tuple(sorted(set(candidates), key=lambda path: path.as_posix().casefold()))
        self._by_path = {path.as_posix().casefold(): path for path in self.candidates}
        self._by_stem: dict[str, list[Path]] = {}
        self._by_parent_stem: dict[tuple[str, str], list[Path]] = {}
        for path in self.candidates:
            self._by_stem.setdefault(path.stem.casefold(), []).append(path)
            key = (path.parent.as_posix().casefold(), path.stem.casefold())
            self._by_parent_stem.setdefault(key, []).append(path)

    def resolve(self, source_path: Path | str, target: str) -> LinkResolution:
        raw = target.strip()
        if not raw:
            return LinkResolution("missing", reason="The link target is empty.")
        fragment = None
        if "#" in raw:
            raw, fragment = raw.split("#", 1)
        decoded = raw
        for _ in range(6):
            next_value = unquote(decoded)
            if next_value == decoded:
                break
            decoded = next_value
        else:
            return LinkResolution("rejected", reason="The encoded target is too deeply nested.")
        if "%" in decoded and any(unquote(decoded) != decoded for _ in (0,)):
            return LinkResolution("rejected", reason="Nested percent encoding is not allowed.")
        if (
            not decoded
            or decoded.startswith(("/", "\\"))
            or "\\" in decoded
            or decoded.startswith("//")
            or ":" in decoded
            or "\x00" in decoded
        ):
            return LinkResolution("rejected", reason="Only safe Vault-relative note links are allowed.")

        normalized_target = decoded.removesuffix(".md")
        source = PurePosixPath(str(source_path).replace("\\", "/"))
        target_path = PurePosixPath(normalized_target)
        is_explicit_relative = normalized_target.startswith(("./", "../"))
        has_folder = "/" in normalized_target
        if is_explicit_relative:
            combined = source.parent.joinpath(target_path)
            parts: list[str] = []
            for part in combined.parts:
                if part in {"", "."}:
                    continue
                if part == "..":
                    if not parts:
                        return LinkResolution("rejected", fragment=fragment, reason="The link leaves the Vault.")
                    parts.pop()
                else:
                    parts.append(part)
            desired = "/".join(parts).casefold()
            match = self._by_path.get(desired + ".md")
            return self._result([match] if match else [], fragment)

        if has_folder:
            desired = target_path.as_posix().casefold() + ".md"
            match = self._by_path.get(desired)
            return self._result([match] if match else [], fragment)

        stem = target_path.name.casefold()
        same_folder = self._by_parent_stem.get((source.parent.as_posix().casefold(), stem), [])
        if same_folder:
            return self._result(same_folder, fragment)
        return self._result(self._by_stem.get(stem, []), fragment)

    @staticmethod
    def _result(matches: list[Path] | tuple[Path, ...], fragment: str | None) -> LinkResolution:
        ordered = tuple(sorted(set(matches), key=lambda path: path.as_posix().casefold()))
        if not ordered:
            return LinkResolution("missing", fragment=fragment)
        if len(ordered) > 1:
            return LinkResolution("ambiguous", candidates=ordered, fragment=fragment)
        return LinkResolution("resolved", candidates=ordered, fragment=fragment)
