# Pigo Notes App

Windows 本機版 Markdown Vault 工具，直接操作 `C:\Users\hsi67063\Documents\Pigo_Obsidian`，不複製或搬移筆記。

## 啟動

在 PowerShell 執行：

```powershell
& "C:\Users\hsi67063\Documents\Pigo Notes App\scripts\run_app.ps1"
```

## 第一版功能

- Vault Markdown 瀏覽、編輯、儲存與預覽
- `[[筆記連結]]` 與反向連結
- 全文搜尋服務
- 每日筆記與 Vault 全域 Markdown 待辦清單
- 雙欄預設與精簡圖示三欄切換
- Git 快速選單：Pull、Commit、Merge、Push、Branch
- 停用中的 AI 預留面板；V1 不傳送任何資料

## 安全規則

- Git 僅操作固定 Vault。
- Commit 一次提交 Vault 所有變更，但會先顯示變更數量和確認視窗。
- App 不執行任意 PowerShell 指令，不使用強制推送或 `reset --hard`。

## 測試

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
& ".\.venv\Scripts\python.exe" -m pytest -v --basetemp .tmp_pytest
```
