# Copy folder full path

## Goal

Extend the existing file-explorer copy-path action so folder items can copy their complete Windows path too.

## Scope

- Show `複製當前檔案完整路徑` for both Markdown note and folder items.
- Reuse the existing `_copy_note_full_path` helper because it accepts a Vault-relative `Path` and applies the same Vault-boundary check.
- Preserve the recycle-bin action for both item types.
- Keep the existing short clipboard confirmation message.

## Testing

- Add a UI test with a nested folder and note.
- Invoke the shared copy helper using the folder's relative path.
- Assert that Qt's clipboard contains the resolved full folder path under the configured test Vault.

## Non-goals

- Copying multiple selections.
- Opening the operating-system File Explorer.
- Changing how folders are expanded, deleted, or renamed.

