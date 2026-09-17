# Pigo Notes App — 第一版設計

- 日期：2026-09-17
- 狀態：設計已確認，待使用者審閱文件後開始實作
- 平台：Windows 本機桌面程式
- 技術：Python、PySide6、PowerShell／Git 指令介面

## 1. 目標

建立一個直接操作既有 Vault 的簡化版 Obsidian 工具，整合個人知識筆記、工作／專案筆記、每日筆記、Markdown 任務與快速 Git 操作。第一版不包含雲端同步、多人協作、手機版、外掛系統或實際 AI 呼叫。

## 2. 固定路徑

- App 原始碼：`C:\Users\hsi67063\Documents\Pigo Notes App`
- Vault：`C:\Users\hsi67063\Documents\Pigo_Obsidian`
- App Git 遠端：`git@github-lumentum:Pigohsiao/Pigo-granite.git`
- Vault Git 操作範圍：僅限上述 Vault Repository。

## 3. 使用者介面

預設採用雙欄版面：左側是 Vault 導覽與功能捷徑，右側是 Markdown 編輯／閱讀工作區。左上工具列提供精簡圖示，可隨時切換成三欄版面；三欄時額外顯示預覽、反向連結與 Git 資訊側欄。App 會記住上次使用的版面。

## 4. 第一版功能

### 筆記與知識

- 顯示 Vault 資料夾與 Markdown 檔案。
- 建立、開啟、編輯、儲存 Markdown 筆記。
- Markdown 即時預覽。
- 依檔名及內容全文搜尋。
- 解析 `[[筆記連結]]`，提供可點擊連結與反向連結。
- 略過 `.git`、`.obsidian` 等系統資料夾。

### 每日筆記與任務

- 一鍵開啟或建立當日筆記。
- 讀取既有 Markdown 核取方塊：`- [ ]` 與 `- [x]`。
- 彙整 Vault 中的待辦，依完成狀態和來源筆記篩選。
- 在 App 勾選待辦時，回寫原始 Markdown 檔案。

### Git 快速操作

Git 區僅提供快速動作，不顯示完整差異內容：Pull、Commit、Merge、Push、Branch。

- Commit 對 Vault 內全部已變更檔案執行；執行前僅顯示變更檔案數量與提交訊息輸入欄。
- Branch 支援建立與切換分支。
- Pull、Merge、Push、Commit 均需明確確認。
- Python 只透過固定、參數化的 PowerShell／Git 指令模板操作固定 Vault 路徑；不提供任意 PowerShell 命令輸入。
- 失敗時顯示可理解的錯誤，不使用自動覆寫、強制推送或 `reset --hard`。

### AI 預留區

第一版顯示停用的 AI 助理面板與抽象服務介面，不設定 API Key，也不傳送 Vault 內容。

## 5. 架構

- `ui/`：主視窗、導覽、編輯器、預覽、任務、Git 快捷面板。
- `services/`：Vault 檔案存取、搜尋索引、Markdown／連結解析、任務解析、Git／PowerShell 指令介面。
- `models/`：筆記、任務、Git 結果等資料模型。
- `tests/`：不修改實際 Vault 的單元與整合測試；使用暫存測試 Vault。
- App 設定與可重建搜尋索引存放於專案自己的 `app_data/`，不污染 Vault。

## 6. 錯誤處理與驗證

- 儲存前偵測外部修改，提供重新載入或另存副本。
- Git 衝突或網路錯誤時停下來顯示原因與下一步，絕不自動覆寫。
- 測試涵蓋 Markdown 讀寫、任務回寫、連結解析、搜尋、Git 指令組裝與主要失敗情境。
- 第一版驗收：可在 Windows 本機啟動，讀取指定 Vault，完成筆記、任務與五個 Git 快捷操作的可測試流程。

## 7. 非目標

不建立資料雲端副本、不支援手機版或多人協作、不實作完整 Obsidian 外掛、Canvas、圖譜或真正 AI 模型整合。
