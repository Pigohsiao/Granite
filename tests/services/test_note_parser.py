import pigo_notes.services as services


def parse(source: str):
    parser_type = getattr(services, "NoteParser", None)
    assert parser_type is not None, "NoteParser.parse(source) is not implemented yet"
    return parser_type.parse(source)


def test_frontmatter_is_parsed_only_at_document_start() -> None:
    parsed = parse("---\ntitle: Title\ntags:\n  - work\n---\nBody\n---\nnot metadata")

    assert parsed.properties["title"] == "Title"
    assert parsed.body == "Body\n---\nnot metadata"


def test_invalid_frontmatter_is_preserved() -> None:
    source = "---\ntags: [unfinished\n---\nReadable body"

    parsed = parse(source)

    assert parsed.body == source
    assert parsed.properties == {}
    assert parsed.warnings


def test_frontmatter_rejects_object_construction_and_aliases() -> None:
    source = "---\npayload: !!python/object/apply:os.system ['echo unsafe']\n---\nBody"

    parsed = parse(source)

    assert parsed.body == source
    assert parsed.properties == {}
    assert parsed.warnings


def test_links_and_tags_inside_code_and_comments_are_ignored() -> None:
    parsed = parse("""Text [[Real]] #work
`[[Inline]] #inline`
```md
[[Fenced]] #fenced
```
<!-- [[Comment]] #comment -->
""")

    assert [link.target for link in parsed.wikilinks] == ["Real"]
    assert parsed.tags == ["work"]


def test_frontmatter_and_inline_tags_merge_without_heading_false_positive() -> None:
    parsed = parse("---\ntags: [work, project/a]\n---\n# Heading\n\nSee #work and #next-step.")

    assert parsed.tags == ["work", "project/a", "next-step"]


def test_wikilink_alias_and_fragment_are_preserved() -> None:
    parsed = parse("[[資料/筆記#段落|顯示名稱]]")

    assert [(link.target, link.fragment, link.label) for link in parsed.wikilinks] == [
        ("資料/筆記", "段落", "顯示名稱")
    ]


def test_frontmatter_size_and_nesting_are_bounded() -> None:
    oversized = "---\nvalue: " + ("x" * 70_000) + "\n---\nBody"
    parsed = parse(oversized)
    assert parsed.body == oversized
    assert parsed.warnings

    too_deep = "---\na:\n" + "  " * 14 + "b: value\n---\nBody"
    parsed = parse(too_deep)
    assert parsed.body == too_deep
    assert parsed.warnings
