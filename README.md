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
- 首次啟動／手動刷新會在背景建立本機 SQLite 索引；索引位於 app data，不寫入 Vault。一般開啟筆記只讀取所選檔案。
- 左側可切換檔案、全文搜尋、最近閱讀、標籤；搜尋支援中英文、字面子字串、分頁與標籤篩選。
- Markdown wikilink 可安全導覽，重名時先讓使用者選擇；右側有可收合的反向連結與唯讀 Properties。
- 最近閱讀最多 20 篇，支援返回／前進及每篇筆記的閱讀捲動位置，設定依 Vault 分開保存。
- 預覽不自動開啟外部連結，也不載入文件中的圖片或外部／本機嵌入資源；HTTP(S) 只會在使用者明確點擊連結時開啟。
- 工具列提供重新掃描、`A−` 與 `A＋`；閱讀字型大小可調整為 12–28 px，並記住最後設定。
- 檔案總管可對檔案或資料夾按右鍵，選擇「移到資源回收桶」；顯示完整路徑二次確認，不提供永久刪除。

## 索引與資料安全

- 索引及閱讀歷史只存在 `app_data`；可安全刪除索引資料夾並由 Vault 重建。
- 測試只使用 pytest 建立的暫存 Vault，不讀寫使用者的正式 Vault。
- 搜尋文字按字面比對；SQL 特殊字元不會被當成萬用字元。
- 目前 Markdown frontmatter 解析只支援文件中記錄的安全 YAML 子集；不支援的格式會保留可讀內容，不執行 YAML 物件建構。

## 測試

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
& ".\.venv\Scripts\python.exe" -m pytest -v --basetemp .tmp_pytest
```
