"""Markdown rendering and wiki-link relationships."""

import re
from html import escape
from pathlib import Path
from urllib.parse import quote

import markdown

from pigo_notes.services.note_parser import NoteParser


class MarkdownService:
    _WIKILINK = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")
    _SCRIPT = re.compile(r"<script\b[^>]*>.*?</script\s*>", re.IGNORECASE | re.DOTALL)
    _BOLD_PREFIX = re.compile(r"^(?P<prefix>[ \t]*\*\*[^*\r\n]+\*\*)[ \t]*")
    _FENCE_MARKER = re.compile(r"^[ \t]{0,3}(?P<marker>`{3,}|~{3,})")
    _TABLE_DELIMITER = re.compile(r":?-{3,}:?")

    def extract_wikilinks(self, source: str) -> set[str]:
        return {link.target for link in NoteParser.parse(source).wikilinks}

    def find_backlinks(self, notes: dict[Path, str], target: str) -> list[Path]:
        return sorted(
            (path for path, source in notes.items() if target in self.extract_wikilinks(source)),
            key=lambda path: path.as_posix().lower(),
        )

    def render(self, source: str) -> str:
        body = NoteParser.parse(source).body
        body = self._normalize_compact_tables(body)
        visible = NoteParser._mask_non_prose(body)
        replacements: list[tuple[int, int, str]] = []
        for match in NoteParser._WIKILINK.finditer(visible):
            raw = body[match.start():match.end()]
            parts = re.fullmatch(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|([^\]]+))?\]\]", raw)
            if not parts:
                continue
            target = parts.group(1).strip()
            label = (parts.group(2) or target).strip()
            href = "pigo-note://open/" + quote(raw[2:-2], safe="")
            replacements.append((match.start(), match.end(), f'<a href="{href}">{escape(label)}</a>'))
        for start, end, replacement in reversed(replacements):
            body = body[:start] + replacement + body[end:]
        safe_source = self._SCRIPT.sub("", body)
        return markdown.markdown(safe_source, extensions=["extra"])

    @classmethod
    def _normalize_compact_tables(cls, source: str) -> str:
        """Expand only unambiguous one-line tables in render-time memory."""
        normalized_lines: list[str] = []
        fence_character: str | None = None
        fence_length = 0
        inside_comment = False

        lines = source.splitlines(keepends=True)
        for index, line in enumerate(lines):
            text = line.rstrip("\r\n")
            marker = cls._FENCE_MARKER.match(text)
            if fence_character is not None:
                if marker and marker.group("marker")[0] == fence_character and len(marker.group("marker")) >= fence_length:
                    fence_character = None
                    fence_length = 0
                normalized_lines.append(line)
                continue
            if marker:
                fence_character = marker.group("marker")[0]
                fence_length = len(marker.group("marker"))
                normalized_lines.append(line)
                continue
            if inside_comment:
                if "-->" in text:
                    inside_comment = False
                normalized_lines.append(line)
                continue
            if "<!--" in text:
                inside_comment = "-->" not in text.split("<!--", 1)[1]
                normalized_lines.append(line)
                continue

            previous_line = normalized_lines[-1].rstrip("\r\n") if normalized_lines else ""
            if (
                cls._is_plain_paragraph_line(previous_line)
                and cls._is_multiline_table_start(lines, index)
            ):
                normalized_lines.append("\r\n" if line.endswith("\r\n") else "\n")

            replacement = cls._normalize_compact_table_line(text)
            if replacement is None:
                normalized_lines.append(line)
            else:
                ending = line[len(text):]
                normalized_lines.append(replacement + ending)

        return "".join(normalized_lines)

    @classmethod
    def _is_plain_paragraph_line(cls, line: str) -> bool:
        if not line or line != line.lstrip(" \t"):
            return False
        return not re.match(r"(?:#{1,6}\s|>|(?:[-+*]|\d+[.)])\s|`{3,}|~{3,}|\||<!--|<)", line)

    @classmethod
    def _is_multiline_table_start(cls, lines: list[str], index: int) -> bool:
        if index + 2 >= len(lines) or lines[index] != lines[index].lstrip(" \t"):
            return False

        headers = cls._split_pipe_row(lines[index])
        delimiters = cls._split_pipe_row(lines[index + 1])
        if (
            headers is None
            or delimiters is None
            or not headers
            or len(headers) != len(delimiters)
            or any(not cls._TABLE_DELIMITER.fullmatch(cell) for cell in delimiters)
        ):
            return False

        data_rows = 0
        for line in lines[index + 2:]:
            cells = cls._split_pipe_row(line)
            if cells is None:
                break
            if len(cells) != len(headers):
                return False
            data_rows += 1
        return data_rows > 0

    @staticmethod
    def _split_pipe_row(line: str) -> list[str] | None:
        text = line.strip()
        if not text.startswith("|") or not text.endswith("|"):
            return None

        cells: list[str] = []
        current: list[str] = []
        content = text[1:-1]
        code_ticks = 0
        index = 0
        while index < len(content):
            character = content[index]
            if character == "\\" and index + 1 < len(content):
                current.extend(content[index:index + 2])
                index += 2
                continue
            if character == "`":
                end = index + 1
                while end < len(content) and content[end] == "`":
                    end += 1
                tick_count = end - index
                current.extend(content[index:end])
                if code_ticks == 0:
                    code_ticks = tick_count
                elif code_ticks == tick_count:
                    code_ticks = 0
                index = end
                continue
            if character == "|" and code_ticks == 0:
                cells.append("".join(current).strip())
                current = []
            else:
                current.append(character)
            index += 1
        if code_ticks:
            return None
        cells.append("".join(current).strip())
        return cells

    @classmethod
    def _normalize_compact_table_line(cls, line: str) -> str | None:
        if not line or "`" in line or "<!--" in line or "-->" in line or re.search(r"\\\\*\\\|", line):
            return None

        prefix_match = cls._BOLD_PREFIX.match(line)
        prefix = prefix_match.group("prefix").strip() if prefix_match else ""
        table_text = line[prefix_match.end():] if prefix_match else line
        if not table_text.startswith("|") or not table_text.rstrip().endswith("|"):
            return None

        segments = table_text.split("|")
        if segments[0].strip() or segments[-1].strip():
            return None
        segments = segments[1:-1]

        delimiter_start = next(
            (index for index, segment in enumerate(segments) if cls._TABLE_DELIMITER.fullmatch(segment.strip())),
            None,
        )
        if delimiter_start is None:
            return None

        headers = [segment.strip() for segment in segments[:delimiter_start]]
        while headers and not headers[-1]:
            headers.pop()
        if not headers or any(not cell for cell in headers):
            return None

        delimiter_end = delimiter_start
        while delimiter_end < len(segments) and cls._TABLE_DELIMITER.fullmatch(segments[delimiter_end].strip()):
            delimiter_end += 1
        delimiters = [segment.strip() for segment in segments[delimiter_start:delimiter_end]]

        data = [segment.strip() for segment in segments[delimiter_end:]]
        while data and not data[0]:
            data.pop(0)
        while data and not data[-1]:
            data.pop()
        if not data or any(not cell for cell in data):
            return None

        exact_user_shape = (
            bool(prefix)
            and len(headers) == 4
            and len(delimiters) == 5
            and all(cell == "---" for cell in delimiters)
            and len(data) == 4
        )
        if exact_user_shape:
            delimiters = delimiters[:4]
        elif not (len(headers) == len(delimiters) == len(data)):
            return None

        def format_row(cells: list[str]) -> str:
            return "| " + " | ".join(cells) + " |"

        rows = [format_row(headers), format_row(delimiters), format_row(data)]
        return (prefix + "\n\n" if prefix else "") + "\n".join(rows)
