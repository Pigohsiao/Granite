# Markdown Table Preview 修正計畫

> **交接狀態：** GPT-6-Sol 計畫稿，由主代理依 Sol 的調查結果整理成可執行文件；交給 GPT-6-Luna 審讀。此文件目前是計畫，不代表已核准實作。

## 目標與問題定義

修復 Pigo Notes App 右側 Markdown 預覽中的表格顯示問題，讓真正的 Markdown 表格以表格呈現，同時不把一般包含 `|` 的文字、程式碼或其他 Markdown 誤判成表格。已知使用者提供的案例是一段實際上被壓在同一個物理行的文字：

```text
**行動要求列表** | 行動 | 負責人 | 期限 | 狀態 | |---|---|---|---|---| | 參閱兩份 VCSEL IE/daily report 附件 | 收件者（未逐一指定） | 未提供 | 郵件請求 |
```

先驗證這份原文經目前資料流是否仍保有行分隔，以及現有 renderer 產生了什麼 HTML。不能預設是缺少 Markdown 表格套件：`MarkdownService.render()` 已使用 Python-Markdown 的 `extra` extension（含表格支援）。修正要以最小範圍落在實際根因。

## 架構與技術範圍

- UI：PySide6 `QTextBrowser` 預覽，`MainWindow` 將 Markdown 服務輸出的 HTML 設入預覽元件。
- Markdown：Python-Markdown `extra`；服務位於 `src/pigo_notes/services/markdown_service.py`。
- 測試：pytest；主要既有測試位於 `tests/services/test_markdown_service.py`，視根因補 `tests/ui/test_main_window.py`。
- 本次優先只允許修改上述服務與相應測試。只有證據證明 HTML 正確、而 `QTextBrowser` 呈現錯誤時，才可修改 `src/pigo_notes/ui/main_window.py`，並在交接結果解釋證據。
- 不引入依賴、不重寫解析器、不複製 Zettlr 程式碼。Zettlr 的共享 parser/AST 僅是未來架構參考。

## 全域限制與安全邊界

1. 所有新增或修改的含中文檔案均以 UTF-8 讀寫。
2. 只用合成 Markdown 與 pytest 暫存目錄／暫存 Vault 驗證；不得讀寫真實 Vault `C:\Users\hsi67063\Documents\Pigo_Obsidian`。
3. 不修改使用者 Markdown 筆記，不新增任何會批次改寫 Vault 筆記的流程。
4. 保留工作樹既有 dirty/untracked 變更；不得 reset、checkout、清理暫存資料、stage、commit 或 push。
5. 不改變一般段落、標題、wikilink、frontmatter、程式碼區塊與既有預覽行為；避免超出表格修復範圍。
6. 本文件完成後先交 Pigo 確認內容；在 Pigo 明確同意前，Luna 僅審讀本文件，不改程式碼。

## 實作步驟（Luna 執行時遵循 TDD）

### 0. 開始前的工作樹保護與基線

- [ ] 在 `C:\Users\hsi67063\Documents\Pigo Notes App` 檢查 `git status --short`，記錄既有修改；不得把既有 reader/index 變更算成本次內容。
- [ ] 閱讀 `MarkdownService.render()`、`NoteParser.parse()` 對 body 的處理、`MainWindow` 呼叫 `setHtml` 的路徑，以及預覽的 table CSS。
- [ ] 使用專案既有 `.venv` 和 pytest；先確認命令不會碰真實 Vault。
- [ ] 建立最小診斷測試/腳本或直接以既有服務呼叫，分別取得：原始輸入、frontmatter 後 body、`render()` HTML、UI 預覽收到的 HTML。診斷輸出只用合成字串，不輸出 Vault 私人筆記。

**完成條件：**能指出故障位於輸入行分隔、Markdown 轉 HTML、或 UI 顯示中的哪一層；不得只根據畫面猜測。

### 1. 先為標準多行表格建立服務層回歸測試（預期 RED）

在 `tests/services/test_markdown_service.py` 新增測試，使用獨立的 MarkdownService 測試實例：

- [ ] `test_markdown_preview_renders_standard_multiline_table`：輸入含表頭、`| --- | --- |` 分隔列和至少兩筆資料的標準多行表格。驗證 HTML 有 `<table>`、`<thead>`、正確數量的 `<th>`、`<tbody>`、正確數量的 `<td>`，並確認中文文字保留。
- [ ] 在測試失敗訊息中保留實際 HTML 片段以便定位，但避免以易碎的完整 HTML 字串做唯一斷言。
- [ ] 執行目標測試並記錄 RED 的原因。若標準表格已經通過，不得為了「製造 RED」修改正常行為；轉而將 RED 聚焦在確實失敗的使用者單行案例。

**指定測試命令：**

```powershell
$env:QT_QPA_PLATFORM='offscreen'; $env:PYTHONDONTWRITEBYTECODE='1'; .\.venv\Scripts\python.exe -m pytest tests\services\test_markdown_service.py -q -p no:cacheprovider
```

**預期：**診斷用新案例若暴露缺陷則先失敗；其餘既有服務測試狀態清楚可見。不能因既有測試已失敗就略過比對基線。

### 2. 為使用者提供的壓縮單行案例建精確測試（預期 RED）

- [ ] 新增 `test_markdown_preview_renders_compact_four_column_table`：以欄數一致的四欄壓縮格式為正向案例，表頭及資料格精確符合使用者指定內容。
- [ ] 新增 `test_markdown_preview_normalizes_user_example_to_four_columns`：以使用者貼上的完整原文（粗體標題、四個表頭、五段 delimiter、四個資料格）為輸入，驗證預覽輸出是一個四欄 table，且標題與所有儲存格文字都保留。
- [ ] Pigo 已確認預期表格為四欄，欄名依序為「行動、負責人、期限、狀態」，資料列為「參閱兩份 VCSEL IE/daily report 附件、收件者（未逐一指定）、未提供、郵件請求」。粗體「行動要求列表」是表格外標題，應保留為粗體文字，不能吞入第一個欄位。

四欄測試請使用此完整壓縮字串（標題在表格外；四個 header、五段 delimiter、四個 data cell）：

```text
**行動要求列表** | 行動 | 負責人 | 期限 | 狀態 | |---|---|---|---| | 參閱兩份 VCSEL IE/daily report 附件 | 收件者（未逐一指定） | 未提供 | 郵件請求 |
```

注意：Pigo 已確認語義上需要四欄。渲染器應只在 Markdown render 的記憶體輸入中，將此可辨識格式的多一段 delimiter 正規化為四欄；不可寫回或改動 Markdown 筆記原文。標題必須作為表格外粗體標題保留。
- [ ] 由測試明確表達預期 DOM 結構和每格文字，而非只測 `<table>` 子字串。
- [ ] 執行目標測試，確認使用者原文在現況下的實際行為；若 renderer 目前已可正確呈現，將本項作為防回歸測試，不增加不必要的正規化。

**欄位數與原始分隔列：**Pigo 已確認預期為四欄。使用者貼上的格式可由粗體標題、四個 header cell、五段純 `---` delimiter、四個 data cell 唯一辨識；僅對這種結構，在 render-time 將 delimiter 行正規化成四欄。原始檔案內容必須不變。若表頭或資料列不是四格、分隔列不是純合法 delimiter、或含有不明確額外文字，則不得修補或猜測，應保留原文並由保護測試驗證。

### 3. 先決定根因，再選擇唯一必要修正分支

按以下順序比較步驟 0 的資料：

1. **標準多行 Markdown 在 service HTML 已沒有 table：**檢查 `MarkdownService` 傳入 Python-Markdown 的文字、extension 設定、frontmatter/body 切分。修正最小的 renderer 設定或輸入轉換，禁止同時加入另一個 Markdown library。
2. **service HTML 有 table，但 `QTextBrowser` 仍顯示原始管線文字或 table 樣式錯誤：**在實際預覽元件路徑檢查 `setHtml`、字型/樣式表覆寫與 table CSS；僅對已證實的 UI 根因修改 `main_window.py`，並新增 UI 測試。
3. **標準多行通過，而使用者壓縮案例失敗：**依四個 header cell 與四個 data cell 的明確語義，在 Markdown render 前只正規化 delimiter 的多餘一段；不要改動原文，也不能把所有 `|` 強行拆行。
4. **其他欄數不一致或分隔邊界不明：**不猜、不補格、不刪格；保留原文語義並由負向測試確認沒有錯誤 table。

### 4. 若需單行表格正規化，加入防誤判的明確規則

只有步驟 3 證明其必要，才允許本項：

- [ ] 先在 service 測試補完整的誤判保護案例，再實作。
- [ ] 支援一般明確欄數一致的壓縮表格；另對本次確認的特例，只有在粗體標題 + 四個 header cells + 五段僅由 `-` 組成的 delimiter + 四個 data cells 連續同一物理行出現時，將 delimiter 多出的第五段在記憶體內正規化為四欄，再交給 Python-Markdown。
- [ ] 保留前綴粗體標題、所有單元格原始文字、Unicode/中文、對齊標記和周邊空白；不改寫來源檔、不重排欄位、不增刪資料格。
- [ ] 不處理下列情形：一般含 pipe 的段落、欄數不一致、缺少 delimiter row、escaped pipe (`\|`)、行內 code、fenced code、HTML comment，以及不能明確判定的相鄰文字。
- [ ] 若可靠保護 fenced/inline code 和 escaped pipe 需要變成第二套 Markdown parser，停止這條方案，回報 Pigo 改採多行表格語法提示或其他方案；不要做脆弱的通用 Regex 改寫。
- [ ] 完成最小變更後重跑精確使用者案例與所有保護測試，確認 RED→GREEN。

### 5. 防止誤判的服務層測試

在 `tests/services/test_markdown_service.py` 覆蓋：

- [ ] `test_pipe_prose_is_not_promoted_to_table`：例如一段只有 pipe 分隔、沒有合法 delimiter row 的文字，不得出現 `<table>`。
- [ ] `test_inline_code_pipe_is_preserved`：行內 code 的 `|` 不應被拆解或改成表格。
- [ ] `test_fenced_code_pipe_is_preserved`：fenced code 中的表格樣式文字仍是 code block，不生成 table。
- [ ] `test_escaped_pipe_is_preserved_in_cell`：有效表格儲存格中的 `\|` 保留為同一格文字，不額外創造欄位。
- [ ] `test_mismatched_table_column_count_is_not_guessed`：表頭、delimiter、資料欄數不一致時，不應透過自動補格或刪格產生誤導性表格。
- [ ] 既有 headings、frontmatter、wikilinks、code 的測試全數仍通過。

**預期：**正常多行表格轉換成功；只有規格明確的壓縮格式在需要時被轉換；其餘文字原義保留。

### 6. 若根因在 UI，使用合成資料做預覽整合測試

只有步驟 3 判定 root cause 位於 UI 才執行本階段：

- [ ] 在 `tests/ui/test_main_window.py` 新增一個以 `tmp_path` 建立空白測試 Vault 的測試；放入合成 Markdown table，不參照真實 Vault 路徑。
- [ ] 使用既有 fixture 建立 MainWindow，選取合成 note，觸發真正的預覽路徑。
- [ ] 驗證預覽顯示中實際存在 table（以 Qt DOM/text browser API 能可靠觀察的 table 結構或呈現結果斷言），而非只直接測 service 回傳 HTML。
- [ ] 若 Qt 測試需 offscreen，沿用專案既有 pytest fixture/環境設定；不能為這個單一功能更換全域測試執行方式。
- [ ] 確認視窗關閉時清理測試資源，不留下 process 或臨時 Vault。

**預期：**UI 整合測試可從載入合成 note 到預覽顯示表格完整通過，且不存取使用者真實資料。

### 7. 驗證、回歸與 Luna QA 交接

依序執行，任一失敗先修復並重跑相關測試：

```powershell
$env:QT_QPA_PLATFORM='offscreen'; $env:PYTHONDONTWRITEBYTECODE='1'; .\.venv\Scripts\python.exe -m pytest tests\services\test_markdown_service.py -q -p no:cacheprovider
```

若修改 UI，再執行：

```powershell
$env:QT_QPA_PLATFORM='offscreen'; $env:PYTHONDONTWRITEBYTECODE='1'; .\.venv\Scripts\python.exe -m pytest tests\ui\test_main_window.py -q -p no:cacheprovider
```

最後執行完整套件：

```powershell
$env:QT_QPA_PLATFORM='offscreen'; $env:PYTHONDONTWRITEBYTECODE='1'; .\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
```

另檢查 `git diff --check`，並逐一檢視本次 diff，確認沒有混入既有 reader/index dirty changes、沒有 Vault 資料、沒有產生依賴/鎖檔的非預期變更。回報每條命令的 exit code、通過/失敗測試數和任何環境限制。

Luna 完成後，另由一個新的 GPT-6-Luna QA 任務獨立審查：

- [ ] 對照本文件每條驗收標準，核對實際 diff、測試結果與渲染輸出。
- [ ] 對案例欄數、code/escaped pipe 防護、沒有猜測補格/刪格，列為 hard gates。
- [ ] 確認使用者真實 Vault 未被碰觸、無 stage/commit/push。
- [ ] QA 需給分與 PASS/FAIL；沿用專案既有品質門檻至少 96/100（若使用者另行指定，以最新要求為準）。任何 hard gate 失敗即 FAIL，不得以平均分掩蓋。
- [ ] QA 有發現時，由 Luna 依 findings 修正，重跑測試，再請獨立 QA 複查；不得由實作者自行宣稱 QA 通過。

## 驗收清單

- [ ] 有效標準多行 Markdown 表格在服務與實際 UI 預覽都正確呈現表頭、資料列、中文和欄位內容。
- [ ] 使用者原始案例在預覽中正確呈現為四欄 table；正規化只作用於 render-time，來源 Markdown 保持原樣。其他不規則欄數不被猜測轉換或丟資料。
- [ ] 普通 pipe prose、行內/圍欄 code、escaped pipe 與不規則欄數未被誤轉或破壞。
- [ ] 完整 pytest suite 與 `git diff --check` 通過。
- [ ] 新 GPT-6-Luna 獨立 QA 通過所有 hard gates 並達到至少 96/100。

## 給 Luna 的工作指示

收到 Pigo 對本文件的明確實作核准後，再依上述順序修改；第一步先回報工作樹狀態和已證實的故障層級。嚴格使用 RED→GREEN 測試驅動，只修改已證實需要的服務/UI 路徑。不得碰本文件以外的功能、真實 Vault 或其他既有 dirty files。實作完成先提供精確 diff/測試摘要，再停止，由獨立 Luna QA 審查。

## Review Focus

1. 原案例欄位數是否被正確讀取，是否有任何未經授權的補欄、刪欄、吞掉標題或文字改寫。
2. 新增的單行處理是否足夠嚴格，且 code/comment/escaped-pipe/prose 防護有測試證明。
3. 是否從實際資料流證明根因，而非只是看到 `extra` 就假定表格已支援或假定 UI 有錯。
4. 是否只改了最小必要檔案，並完整保留原有 dirty work 與 Vault 隔離。
5. 是否使用行為測試驗證 service 與（適用時）真實 UI preview，並完成完整套件與獨立 QA。
