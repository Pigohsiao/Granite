# Preview Font Family Design

## Goal

讓使用者可選擇 Windows 已安裝的字型，且只改變 Pigo Notes App 右側 Markdown 預覽的文字。既有的檔案總管、工具列、主視窗與字級控制不受影響。

## User Experience

- 在主工具列的 `A−`、`A＋` 後方新增標示為「預覽字型」的原生字型下拉選單。
- 清單由 Windows 可用字型提供，使用者選取後，右側預覽立即更新，不需要重新開啟筆記。
- `A−`、`A＋` 仍只控制右側預覽字級，並保留現有 12–28px 範圍。
- App 第一次啟動時沿用目前應用程式的預設字型；若先前有保存選擇，則還原該字型。
- 所有設定持久化至既有 `app_data/settings.json`；無效或遺失的設定安全回退到應用程式預設字型。

## Architecture

`MainWindow` 維持為唯一的 UI 協調者。它新增 `preview_font_family` 狀態與 `QFontComboBox` 控制項；字型變更透過 `set_preview_font_family()` 同步設定 `QTextBrowser` 的字型，並沿用 `_save_settings()` 儲存。`set_preview_font_size()` 繼續負責字級，兩者共同套用至同一個右側預覽元件。

## Components

### `src/pigo_notes/ui/main_window.py`

- 匯入 `QFontComboBox` 與必要的 `QFont` 型別。
- 在建構期間讀取 `preview_font_family`，回退值為 `QApplication.font().family()`。
- 在工具列建立字型下拉選單、設定工具提示與合理固定寬度，並把選擇事件連至 setter。
- 新增 `set_preview_font_family(family, persist=True)`：空值或不可用字型回退；設定預覽控制項；需要時保存設定。
- 讓字級與字型 setter 都不會覆蓋另一方目前設定。
- `_save_settings()` 寫入字型名稱，`_load_settings()` 保持對損壞或非物件 JSON 的既有容錯行為。

### `tests/ui/test_main_window.py`

- 驗證工具列包含 `QFontComboBox`。
- 驗證選擇一個已安裝字型後，右側預覽套用該字型且寫入設定。
- 建立新視窗後驗證保存的字型會還原，並驗證字級仍保持原本行為。

## Error Handling

- JSON 內無字型設定、空白字串或指定字型不在目前系統：回退應用程式預設字型，不中斷 App 啟動。
- 使用者的字型清單由 Qt 原生元件提供，避免自行維護 Windows 字型清單。

## Testing

使用主版本既有虛擬環境在隔離工作區執行 pytest。先新增會失敗的 UI 測試，再做最小實作，最後執行完整 27 項以上測試。完成後手動啟動 Windows App，確認選字、預覽即時變化與重啟後保留設定。

## Scope Boundaries

- 不改變左側檔案樹、工具列其他元件或 App 整體 UI 字型。
- 不新增雲端同步、字型檔上傳或自訂 CSS 編輯器。
- 不變更 Vault 內容。
