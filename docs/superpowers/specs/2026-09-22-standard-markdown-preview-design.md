# Standard Markdown preview

## Goal

Make the right-side preview consistently display standard Markdown as readable rich content instead of raw control characters.

## Scope

- Preserve existing support for headings, tables, fenced code blocks, lists, emphasis, links, and wiki-link text.
- Add standard Markdown extensions for blockquotes, horizontal rules, definition lists, abbreviations, footnotes, and Markdown inside safe HTML blocks through Python-Markdown's `extra` extension set.
- Add preview CSS for headings, tables, blockquotes, horizontal rules, inline code, and fenced code so the elements remain clear in both themes.
- Continue stripping script tags before rendering.

## Testing

- Add a Markdown service test that verifies headings, table markup, blockquotes, and fenced code are rendered to HTML.
- Keep the existing script-tag removal test.

## Non-goals

- Interactive task checkboxes.
- Math formulas, diagrams, embedded web content, or custom Obsidian plugins.

