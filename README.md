# Pigo Notes App

Windows 本機版 Markdown Vault 唯讀工具，直接操作 `C:\Users\hsi67063\Documents\Pigo_Obsidian`，不複製、搬移或修改筆記。

## 啟動

在 PowerShell 執行：

```powershell
& "C:\Users\hsi67063\Documents\Pigo Notes App\scripts\run_app.ps1"
```

## 目前功能

- Obsidian 風格雙欄專注模式：左側檔案總管、右側 Markdown 唯讀預覽。
- 依 Vault 資料夾結構縮排顯示；所有資料夾預設收合。
- 點選檔案時只讀取目前檔案，避免全 Vault 掃描造成延遲。
- 工具列提供重新掃描、`A−` 與 `A＋`；閱讀字型大小可調整為 12–28 px，並記住最後設定。`n- 檔案總管可對檔案或資料夾按右鍵，選擇「移到資源回收桶」；顯示完整路徑二次確認，不提供永久刪除。

## 測試

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
& ".\.venv\Scripts\python.exe" -m pytest -v --basetemp .tmp_pytest
```