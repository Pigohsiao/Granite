# Copy note full path

## Goal

Add a right-click action for Markdown notes in the Pigo Notes App file explorer. The action copies the selected note's full Windows path to the clipboard.

## Scope

- Show `複製當前檔案完整路徑` only for file items.
- Build the path from the configured Vault root and the selected note's known relative path.
- Copy the resolved full path through Qt's clipboard API.
- Show a short status-bar confirmation after a successful copy.
- Do not add the action to folder menus and do not invoke PowerShell.

## Error handling

The file explorer only supplies paths already indexed from the Vault. The copy helper will still reject a path that resolves outside the Vault boundary and will show an error message instead of copying it.

## Testing

- Start with a failing UI test that selects a nested Markdown note.
- Assert that the clipboard contains the resolved full path under the test Vault.
- Assert that a folder is not treated as a copyable note.

## Non-goals

- Copying folder paths.
- Opening the Windows File Explorer.
- Editing, deleting, moving, or synchronizing files.
