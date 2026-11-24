"""Bounded parser for the safe YAML subset and Obsidian-style reader syntax."""

from __future__ import annotations

import json
import re
from typing import Any

from pigo_notes.index_models import ParsedNote, WikiLink


class _InvalidFrontmatter(ValueError):
    pass


class NoteParser:
    MAX_FRONTMATTER_BYTES = 64 * 1024
    MAX_NESTING = 12
    _KEY = re.compile(r"^[A-Za-z0-9_.-]+$")
    _FENCE = re.compile(r"(?ms)^[ \t]{0,3}(`{3,}|~{3,})[^\n]*\n.*?^[ \t]{0,3}\1[ \t]*$")
    _COMMENT = re.compile(r"(?s)<!--.*?-->")
    _INLINE_CODE = re.compile(r"(`+).*?\1")
    _WIKILINK = re.compile(r"\[\[([^\]|#]+?)(?:#([^\]|]+))?(?:\|([^\]]+))?\]\]")
    _TAG = re.compile(r"(?<![\w#])#([\w][\w/-]*)", re.UNICODE)
    _UNSAFE_YAML_MARKER = re.compile(
        r"(?:^|[\s:{,\[])(?:&[A-Za-z0-9_.-]+|\*[A-Za-z0-9_.-]+|!(?:![A-Za-z0-9_./:-]*|[A-Za-z0-9_./:-]+))"
    )

    @classmethod
    def parse(cls, source: str) -> ParsedNote:
        body, properties, warnings = cls._frontmatter(source)
        visible = cls._mask_non_prose(body)
        links = [
            WikiLink(
                target=match.group(1).strip(),
                fragment=match.group(2).strip() if match.group(2) else None,
                label=match.group(3).strip() if match.group(3) else None,
            )
            for match in cls._WIKILINK.finditer(visible)
            if match.group(1).strip()
        ]
        tags: list[str] = []
        frontmatter_tags = properties.get("tags", [])
        if isinstance(frontmatter_tags, str):
            frontmatter_tags = [frontmatter_tags]
        if isinstance(frontmatter_tags, list):
            for tag in frontmatter_tags:
                if isinstance(tag, (str, int, float)):
                    cls._append_tag(tags, str(tag))
        for line in visible.splitlines():
            prose_line = re.sub(r"^ {0,3}#{1,6}[ \t]+", lambda match: " " * len(match.group()), line)
            for match in cls._TAG.finditer(prose_line):
                cls._append_tag(tags, match.group(1))
        return ParsedNote(body=body, properties=properties, tags=tags, wikilinks=links, warnings=warnings)

    @classmethod
    def _frontmatter(cls, source: str) -> tuple[str, dict[str, Any], list[str]]:
        lines = source.splitlines(keepends=True)
        if not lines or lines[0].rstrip("\r\n") != "---":
            return source, {}, []
        closing = next((i for i in range(1, len(lines)) if lines[i].rstrip("\r\n") == "---"), None)
        if closing is None:
            return source, {}, ["Frontmatter closing delimiter is missing; original text was preserved."]
        raw = "".join(lines[1:closing])
        if len(raw.encode("utf-8")) > cls.MAX_FRONTMATTER_BYTES:
            return source, {}, ["Frontmatter exceeds the 64 KiB safety limit; original text was preserved."]
        try:
            properties = cls._parse_yaml_subset(raw.splitlines())
        except (ValueError, UnicodeError) as error:
            return source, {}, [f"Frontmatter was not parsed: {error}; original text was preserved."]
        return "".join(lines[closing + 1:]), properties, []

    @classmethod
    def _parse_yaml_subset(cls, source_lines: list[str]) -> dict[str, Any]:
        tokens: list[tuple[int, str]] = []
        for line in source_lines:
            if "\t" in line[: len(line) - len(line.lstrip())]:
                raise _InvalidFrontmatter("tabs are not supported for indentation")
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if cls._UNSAFE_YAML_MARKER.search(stripped):
                raise _InvalidFrontmatter("YAML tags, anchors, and aliases are not supported")
            indent = len(line) - len(line.lstrip(" "))
            if indent > cls.MAX_NESTING * 2:
                raise _InvalidFrontmatter("maximum indentation exceeded")
            tokens.append((indent, stripped))
        if not tokens:
            return {}
        value, next_index = cls._parse_block(tokens, 0, tokens[0][0], 1)
        if next_index != len(tokens) or not isinstance(value, dict):
            raise _InvalidFrontmatter("frontmatter must be a mapping")
        return value

    @classmethod
    def _parse_block(cls, tokens: list[tuple[int, str]], index: int, indent: int, depth: int) -> tuple[Any, int]:
        if depth > cls.MAX_NESTING:
            raise _InvalidFrontmatter("maximum nesting depth exceeded")
        if index >= len(tokens) or tokens[index][0] != indent:
            raise _InvalidFrontmatter("invalid indentation")
        is_list = tokens[index][1] == "-" or tokens[index][1].startswith("- ")
        container: Any = [] if is_list else {}
        while index < len(tokens):
            current_indent, text = tokens[index]
            if current_indent < indent:
                break
            if current_indent > indent:
                raise _InvalidFrontmatter("unexpected indentation")
            if is_list:
                if not (text == "-" or text.startswith("- ")):
                    raise _InvalidFrontmatter("mixed list and mapping values")
                item_text = text[1:].strip()
                index += 1
                if item_text:
                    container.append(cls._parse_scalar(item_text))
                elif index < len(tokens) and tokens[index][0] > indent:
                    child_indent = tokens[index][0]
                    child, index = cls._parse_block(tokens, index, child_indent, depth + 1)
                    container.append(child)
                else:
                    container.append(None)
                continue
            match = re.fullmatch(r"([^:]+):(?:\s*(.*))?", text)
            if not match:
                raise _InvalidFrontmatter(f"invalid mapping entry: {text[:80]}")
            key, raw_value = match.group(1).strip(), (match.group(2) or "").strip()
            if not cls._KEY.fullmatch(key) or key in container:
                raise _InvalidFrontmatter(f"invalid or duplicate key: {key}")
            index += 1
            if raw_value:
                container[key] = cls._parse_scalar(raw_value)
            elif index < len(tokens) and tokens[index][0] > indent:
                child_indent = tokens[index][0]
                child, index = cls._parse_block(tokens, index, child_indent, depth + 1)
                container[key] = child
            else:
                container[key] = {}
        return container, index

    @classmethod
    def _parse_scalar(cls, value: str) -> Any:
        if value.startswith("["):
            if not value.endswith("]"):
                raise _InvalidFrontmatter("unterminated flow sequence")
            inner = value[1:-1].strip()
            return [] if not inner else [cls._parse_scalar(part.strip()) for part in cls._split_flow(inner)]
        if value.startswith("{") or value.endswith("}"):
            raise _InvalidFrontmatter("flow mappings are not supported")
        if value.startswith('"'):
            try:
                parsed = json.loads(value)
            except json.JSONDecodeError as error:
                raise _InvalidFrontmatter("invalid quoted scalar") from error
            if not isinstance(parsed, str):
                raise _InvalidFrontmatter("only string double-quoted scalars are supported")
            return parsed
        if value.startswith("'"):
            if len(value) < 2 or not value.endswith("'"):
                raise _InvalidFrontmatter("invalid single-quoted scalar")
            return value[1:-1].replace("''", "'")
        lowered = value.casefold()
        if lowered in {"null", "~"}:
            return None
        if lowered in {"true", "false"}:
            return lowered == "true"
        if re.fullmatch(r"[-+]?\d+", value):
            try:
                return int(value)
            except ValueError:
                return value
        return value

    @staticmethod
    def _split_flow(value: str) -> list[str]:
        parts: list[str] = []
        start = 0
        quote: str | None = None
        for index, char in enumerate(value):
            if quote:
                if char == quote and (quote != "'" or index + 1 >= len(value) or value[index + 1] != "'"):
                    quote = None
            elif char in {"'", '"'}:
                quote = char
            elif char == ",":
                parts.append(value[start:index])
                start = index + 1
        if quote:
            raise _InvalidFrontmatter("unterminated quoted flow value")
        parts.append(value[start:])
        return parts

    @classmethod
    def _mask_non_prose(cls, source: str) -> str:
        def mask(match: re.Match[str]) -> str:
            return re.sub(r"[^\n]", " ", match.group(0))

        source = cls._FENCE.sub(mask, source)
        source = cls._COMMENT.sub(mask, source)
        return cls._INLINE_CODE.sub(mask, source)

    @staticmethod
    def _append_tag(tags: list[str], value: str) -> None:
        normalized = value.strip().lstrip("#").rstrip(".,;:!?)]}")
        if normalized and normalized not in tags:
            tags.append(normalized)
