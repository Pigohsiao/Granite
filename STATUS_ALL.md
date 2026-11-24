# STATUS_2026-09-17_add_v1_design

- What changes were made: Created the Pigo Notes App project repository, added the approved V1 design document and project ignore rules, then committed and pushed the design to the configured Pigo-granite remote.
- Whether verification succeeded or failed: Verification succeeded; the SSH remote authenticated as Pigohsiao, staged-file whitespace validation passed, and the initial commit was pushed to origin/main.
- If verification still failed, the failure reason and blocker: None.
- What the next step should be: Review the design document and approve it before creating the implementation plan and Python virtual environment.
# STATUS_2026-09-17_add_v1_implementation_plan

- What changes were made: Added and pushed the task-by-task Pigo Notes App V1 implementation plan after the approved design review.
- Whether verification succeeded or failed: Verification succeeded; the plan passed its placeholder scan and Git staged-content validation, then was committed and pushed to origin/main.
- If verification still failed, the failure reason and blocker: None.
- What the next step should be: Create the Python virtual environment and implement the plan with tests before each feature.
# STATUS_2026-09-17_bootstrap_project_and_config

- What changes were made: Created the Python project configuration, UTF-8 package skeleton, fixed VaultConfig, and the first test-driven configuration test; repaired the virtual environment dependency installation so pytest is available.
- Whether verification succeeded or failed: Verification succeeded; `tests/test_config.py` passed with 1 test after reproducing and resolving the missing-pytest environment issue.
- If verification still failed, the failure reason and blocker: None.
- What the next step should be: Implement safe UTF-8 Vault discovery, reading, writing, and daily-note creation with tests first.
# STATUS_2026-09-17_add_vault_service

- What changes were made: Added UTF-8 Vault note discovery, safe read/write, daily-note creation, and path-boundary protection with isolated tests. Added an ignored project-local pytest temp directory to avoid a Windows system-temp permission boundary.
- Whether verification succeeded or failed: Verification succeeded; all 3 VaultService tests passed using the project-local pytest temp directory.
- If verification still failed, the failure reason and blocker: None.
- What the next step should be: Add Markdown links, rendering, search, and checkbox task aggregation using tests first.
# STATUS_2026-09-17_add_markdown_search_and_tasks

- What changes were made: Added wiki-link/backlink parsing, safe Markdown rendering, case-insensitive search, and Vault-wide Markdown task aggregation with source-file checkbox writeback.
- Whether verification succeeded or failed: Verification succeeded; 4 focused service tests passed. A task checkbox formatting defect was reproduced by the test and fixed by replacing only the checkbox token.
- If verification still failed, the failure reason and blocker: None.
- What the next step should be: Implement the restricted PowerShell Git service for Pull, Commit, Merge, Push, and Branch.
# STATUS_2026-09-17_add_restricted_git_service

- What changes were made: Added a fixed-Vault PowerShell Git service that allows only Pull, Commit-all, Merge, Push, and Branch create/switch; it rejects unsafe branch names and empty commit messages before starting a subprocess.
- Whether verification succeeded or failed: Verification succeeded; 2 Git service safety tests passed and a real read-only status count against the configured Vault completed successfully without changing the Vault.
- If verification still failed, the failure reason and blocker: Editable package installation was not required for runtime because the project launcher will explicitly set the local src path; PySide6 and all test dependencies are installed.
- What the next step should be: Build the PySide6 main window with the default two-column layout and compact layout toggle.
# STATUS_2026-09-17_add_workspace_ui

- What changes were made: Added the PySide6 workspace with Vault navigation, Markdown editing and preview, backlinks, save action, default two-column layout, and the compact two/three-column toggle with persisted settings.
- Whether verification succeeded or failed: Verification succeeded; the offscreen Qt main-window layout test passed.
- If verification still failed, the failure reason and blocker: None.
- What the next step should be: Add Today and Tasks interactions, then compact Git action dialogs.
# STATUS_2026-09-17_add_daily_notes_and_task_panel

- What changes were made: Added Today and Tasks toolbar actions, daily-note creation/opening, a Vault-wide task panel, and direct checkbox writeback to source Markdown files.
- Whether verification succeeded or failed: Verification succeeded; all 3 relevant offscreen Qt tests passed after correcting the test fixture to use the required PySide6 checkbox enum.
- If verification still failed, the failure reason and blocker: None.
- What the next step should be: Add the compact Git menu and confirmation dialogs for Pull, Commit, Merge, Push, and Branch.
# STATUS_2026-09-17_add_quick_git_controls

- What changes were made: Added a compact Git toolbar icon with exactly Pull, Commit, Merge, Push, and Branch actions, each using confirmation dialogs; added the disabled AI placeholder panel.
- Whether verification succeeded or failed: Verification succeeded; 4 offscreen UI tests passed, including the exact five-item Git menu check.
- If verification still failed, the failure reason and blocker: None.
- What the next step should be: Add the Windows launcher, README, smoke test, then run the full test suite and launch the app for manual verification.
# STATUS_2026-09-17_add_quick_git_controls

- What changes were made: Added a compact Git toolbar icon with exactly Pull, Commit, Merge, Push, and Branch actions, each using confirmation dialogs; added the disabled AI placeholder panel.
- Whether verification succeeded or failed: Verification succeeded; 4 offscreen UI tests passed and staged-content validation passed after removing an extra end-of-file blank line.
- If verification still failed, the failure reason and blocker: None.
- What the next step should be: Add the Windows launcher, README, smoke test, then run the full test suite and launch the app for manual verification.
# STATUS_2026-09-17_complete_v1_and_verify

- What changes were made: Added the Windows launcher, README, configured-Vault smoke test, and local ignore rules required to run the completed Pigo Notes App V1.
- Whether verification succeeded or failed: Verification succeeded; the full suite passed with 16 tests, Python compileall passed, and the app can construct against the configured Vault without modifying notes.
- If verification still failed, the failure reason and blocker: None.
- What the next step should be: Launch the app with scripts/run_app.ps1 and perform the visible manual test of note editing, task toggle, layout toggle, and Git menu confirmations.

# STATUS_2026-09-17_final_verification_and_launch
- What changes were made: 完成 Pigo Notes App 第一版最終驗證，並重新啟動本機桌面程式供 Pigo 測試。
- Whether verification succeeded or failed: 成功；pytest 16 項測試全數通過，`python -m compileall src` 成功，Git `main` 與 `origin/main` 同步。
- If verification still failed, the failure reason and blocker: 無。
- What the next step should be: Pigo 可在已開啟的桌面程式中測試筆記、每日筆記、任務、兩／三欄切換與 Git 快捷操作。

# STATUS_2026-09-17_open_app
- What changes were made: 依 Pigo 指示開啟 Pigo Notes App。
- Whether verification succeeded or failed: 成功；啟動程序仍在執行。
- If verification still failed, the failure reason and blocker: 無。
- What the next step should be: Pigo 可直接在桌面視窗操作程式。

# STATUS_2026-09-17_open_app_verified
- What changes were made: 重新確認 Pigo Notes App 的 Windows 啟動程序狀態。
- Whether verification succeeded or failed: 成功；啟動程序仍在執行。
- If verification still failed, the failure reason and blocker: 無。
- What the next step should be: Pigo 可直接在桌面視窗操作程式。

# STATUS_2026-09-17_open_app_success
- What changes were made: 以編碼 PowerShell 命令重新啟動 Pigo Notes App，避免含空白路徑被錯誤拆解。
- Whether verification succeeded or failed: 成功；Python 應用程式程序已建立且無錯誤輸出。
- If verification still failed, the failure reason and blocker: 無。
- What the next step should be: Pigo 請在 Windows 桌面查看 Pigo Notes App 視窗；若仍未出現，回覆我，我會繼續檢查視窗層級與焦點狀態。

# STATUS_2026-09-17_preview_performance_diagnosis
- What changes were made: 完成唯讀預覽效能診斷；確認選取筆記時會讀取約 9,243 篇 Markdown 以計算反向連結，造成明顯延遲。
- Whether verification succeeded or failed: 成功；Vault 掃描約 5.82 秒，已定位為主要效能瓶頸。
- If verification still failed, the failure reason and blocker: 程式尚未調整；等待 Pigo 確認採用唯讀快速預覽設計。
- What the next step should be: 取得確認後，移除編輯器與即時反向連結掃描，改為單一檔案唯讀預覽。

# STATUS_2026-09-17_readonly_preview_plan
- What changes were made: 建立唯讀快速預覽的設計與實作計畫；已指定移除開檔時的全 Vault 反向連結掃描。
- Whether verification succeeded or failed: 成功；計畫已依目前 UI 與測試結構建立。
- If verification still failed, the failure reason and blocker: 無。
- What the next step should be: 先加入預期失敗的 UI 測試，再最小化實作唯讀預覽。

# STATUS_2026-09-17_readonly_preview_completed
- What changes were made: Pigo Notes App 已改為唯讀快速預覽；移除內文編輯、儲存按鈕與選檔時的全 Vault 反向連結掃描。新增 UI 回歸測試與使用說明，並取得反向連結 SQLite 索引研究建議。
- Whether verification succeeded or failed: 成功；17 項 pytest 全數通過、`python -m compileall src` 成功。實際 Vault 單檔讀取與渲染量測約 0.31 秒。
- If verification still failed, the failure reason and blocker: 無。反向連結索引尚未實作，已規劃為下一個獨立功能。
- What the next step should be: 提交唯讀預覽優化；待 Pigo 確認後，再實作 SQLite 增量反向連結索引。

# STATUS_2026-09-17_readonly_preview_pushed
- What changes were made: 唯讀快速預覽優化已提交並推送至 GitHub main（9b43f74）。
- Whether verification succeeded or failed: 成功；17 項 pytest 測試全數通過、`python -m compileall src` 成功、Git main 已與 origin/main 同步。
- If verification still failed, the failure reason and blocker: 無。
- What the next step should be: 重新啟動 App 以載入唯讀快速預覽版本；如要加入反向連結，再實作 SQLite 持久化增量索引。

# STATUS_2026-09-17_open_latest_app
- What changes were made: 依 Pigo 指示關閉舊版 Pigo Notes App 程序，並啟動目前已完成的最新版。
- Whether verification succeeded or failed: 成功；新版 Python 應用程式程序已建立。
- If verification still failed, the failure reason and blocker: 無。
- What the next step should be: Pigo 可在 Windows 桌面確認唯讀快速預覽版的介面與選取文件速度。

# STATUS_2026-09-17_obsidian_two_pane_design
- What changes were made: 依 Pigo 選擇建立 Obsidian 風格雙欄專注模式設計；視覺線框稿資料已排除於 Git 之外。
- Whether verification succeeded or failed: 成功；規格已明確定義階層檔案樹、預設收合與唯讀單檔預覽。
- If verification still failed, the failure reason and blocker: 無；等待 Pigo 審閱正式設計後才改動程式。
- What the next step should be: Pigo 確認規格，接著建立實作計畫並以測試驅動完成 UI 改版。

# STATUS_2026-09-17_two_pane_font_plan
- What changes were made: 將預覽字型大小調整加入已確認的雙欄專注模式規格，並建立測試驅動實作計畫。
- Whether verification succeeded or failed: 成功；規格與計畫均明確定義 12–28 px、預設 16 px、持久化與按鈕界限。
- If verification still failed, the failure reason and blocker: 無。
- What the next step should be: 寫入預期失敗的階層檔案樹與字型大小測試，開始最小化 UI 實作。

# STATUS_2026-09-18_obsidian_two_pane_completed
- What changes were made: 完成 Obsidian 風格雙欄專注模式：階層檔案樹預設收合、深色閱讀介面、唯讀單檔預覽，並移除任務、Git、AI、Today、儲存與第三欄。新增 A−／A＋ 預覽字型大小調整，範圍 12–28 px 並持久化設定。
- Whether verification succeeded or failed: 成功；16 項 pytest 測試全數通過、`python -m compileall src` 成功，提交 e9de01f 已推送到 origin/main，最新版程序已啟動。
- If verification still failed, the failure reason and blocker: 無。
- What the next step should be: Pigo 在桌面確認階層收合、選取文件速度與字型大小；下一項可考慮實作 SQLite 反向連結索引。

# STATUS_2026-09-18_movable_window_fix_completed
- What changes were made: 修正 Pigo Notes App 啟動時可能被最大化而無法拖動的問題；新增 `show_for_user()`，強制以一般視窗狀態顯示並帶到前景。
- Whether verification succeeded or failed: 成功；17 項 pytest 全數通過、編譯成功。最新版可見視窗的 Windows ShowCommand=1（Normal），已確認不是最大化且可拖動。
- If verification still failed, the failure reason and blocker: 無。
- What the next step should be: Pigo 可直接拖動目前視窗並確認操作；若要繼續開發，可進入 SQLite 反向連結索引功能。

# STATUS_2026-09-18_drag_theme_completed
- What changes were made: 新增可拖曳整個視窗的系統拖曳列，以及可持久化的明亮／黑暗模式切換。
- Whether verification succeeded or failed: 成功；19 項 pytest 全數通過、`python -m compileall src` 成功，提交 4b3016d 已推送 origin/main。
- If verification still failed, the failure reason and blocker: 無。
- What the next step should be: 待 Pigo 確認後，新增檔案總管右鍵「移到資源回收桶」刪除功能與二次確認。

# STATUS_2026-09-18_recycle_bin_delete_plan
- What changes were made: 建立 Vault 檔案總管資源回收桶刪除功能的安全規格與實作計畫；確認 Windows 內建回收桶 API 可用。
- Whether verification succeeded or failed: 成功；Microsoft.VisualBasic 的 FileSystem 與 RecycleOption API 均可用。
- If verification still failed, the failure reason and blocker: 無。
- What the next step should be: 以失敗測試建立限定 Vault 路徑的 RecycleBinService，再接上右鍵二次確認操作。

# STATUS_2026-09-18_recycle_bin_delete_completed
- What changes were made: 檔案總管新增檔案與資料夾右鍵「移到資源回收桶」功能；限制於 Vault 內，顯示完整相對路徑二次確認，不提供永久刪除。
- Whether verification succeeded or failed: 成功；22 項 pytest 全數通過、`python -m compileall src` 成功，提交 37f7761 已推送 origin/main。最新版可見視窗已建立。
- If verification still failed, the failure reason and blocker: 無。
- What the next step should be: Pigo 可在檔案總管對測試檔案或資料夾按右鍵確認資源回收桶操作；需要時可再加入還原提示或 SQLite 反向連結索引。
# STATUS_2026-09-18_recycle_bin_and_tree_state_fix
- What changes were made: 修正 Windows 資源回收桶呼叫在路徑含空白時的參數傳遞，並在刪除後還原原本展開的資料夾狀態。
- Whether verification succeeded or failed: 專項自動測試 10/10 通過；Python 編譯與 Git 差異格式檢查通過。
- If verification still failed, the failure reason and blocker: 無。
- What the next step should be: 提交、推送並重新啟動程式供 Pigo 驗證。
# STATUS_2026-09-18_recycle_bin_fix_launched
- What changes were made: 已重新啟動包含資源回收桶參數修正與資料夾展開狀態保留功能的最新版桌面程式。
- Whether verification succeeded or failed: 成功；Windows 已偵測到可操作的 Pigo Notes App 視窗。
- If verification still failed, the failure reason and blocker: 無。
- What the next step should be: Pigo 可對 Vault 中的測試檔案或資料夾按右鍵，選擇「移到資源回收桶」驗證。
# STATUS_2026-09-18_desktop_launcher_created
- What changes were made: 在桌面建立「啟動 Pigo Notes App.bat」，以專案虛擬環境的 pythonw.exe 啟動桌面程式。
- Whether verification succeeded or failed: 成功；BAT 與虛擬環境啟動檔皆已確認存在。
- If verification still failed, the failure reason and blocker: 無。
- What the next step should be: Pigo 可雙擊桌面的 BAT 檔直接開啟 Pigo Notes App。
# STATUS_2026-09-18_desktop_launcher_verified
- What changes were made: 已實際執行桌面的「啟動 Pigo Notes App.bat」。
- Whether verification succeeded or failed: 成功；Windows 已偵測到可操作的 Pigo Notes App 視窗。
- If verification still failed, the failure reason and blocker: 無。
- What the next step should be: Pigo 日後可直接雙擊桌面的 BAT 檔啟動程式。
# STATUS_2026-09-22_copy_note_path_design
- What changes were made: 建立「複製當前檔案完整路徑」功能設計，範圍限定為左側檔案總管的 Markdown 檔案右鍵選單。
- Whether verification succeeded or failed: 成功；設計文件完成完整性、自我審查與 Git 差異格式檢查。
- If verification still failed, the failure reason and blocker: 無。
- What the next step should be: Pigo 審閱設計文件後，建立實作計畫與測試。
# STATUS_2026-09-22_copy_note_path_plan
- What changes were made: 建立「複製當前檔案完整路徑」的測試先行實作計畫。
- Whether verification succeeded or failed: 成功；計畫完成需求覆蓋、命名一致性與無 placeholder 自我審查。
- If verification still failed, the failure reason and blocker: 無。
- What the next step should be: Pigo 選擇由子代理分工執行或在目前對話直接執行計畫。
# STATUS_2026-09-22_copy_path_worktree_setup
- What changes were made: 將 .worktrees/ 加入 Git 忽略規則，準備建立隔離功能分支。
- Whether verification succeeded or failed: 成功；Git 已確認 .worktrees 會被忽略。
- If verification still failed, the failure reason and blocker: 無。
- What the next step should be: 建立隔離工作區並跑基線測試。
# STATUS_2026-09-22_copy_note_path_merged
- What changes were made: 已將「複製當前檔案完整路徑」功能合併回 main，並清理隔離功能分支與工作區。
- Whether verification succeeded or failed: 成功；合併後 24 項 pytest 全數通過。
- If verification still failed, the failure reason and blocker: 無。
- What the next step should be: 重新啟動 Pigo Notes App，讓 Pigo 以右鍵選取 Markdown note 驗證新功能。
# STATUS_2026-09-22_copy_note_path_launched
- What changes were made: 已重新啟動包含「複製當前檔案完整路徑」功能的 Pigo Notes App。
- Whether verification succeeded or failed: 成功；Windows 已偵測到可操作的 Pigo Notes App 視窗。
- If verification still failed, the failure reason and blocker: 無。
- What the next step should be: Pigo 可在左側檔案總管對任一 Markdown note 按右鍵，選擇「複製當前檔案完整路徑」。
# STATUS_2026-09-22_copy_folder_path_design
- What changes were made: 建立資料夾複製完整路徑功能的設計，重用既有 Vault 邊界檢查與剪貼簿邏輯。
- Whether verification succeeded or failed: 成功；設計完成需求覆蓋與無 placeholder 自我審查。
- If verification still failed, the failure reason and blocker: 無。
- What the next step should be: Pigo 審閱設計文件後，建立測試先行實作計畫。
# STATUS_2026-09-22_copy_folder_path_plan
- What changes were made: 建立資料夾完整路徑右鍵功能的測試先行實作計畫。
- Whether verification succeeded or failed: 成功；計畫完成需求覆蓋、型別命名一致性與無 placeholder 自我審查。
- If verification still failed, the failure reason and blocker: 無。
- What the next step should be: 依 Pigo 指示在目前對話直接執行計畫。
# STATUS_2026-09-22_standard_markdown_preview_design
- What changes were made: 建立標準 Markdown 預覽擴充設計，涵蓋標題、表格、清單、引用、分隔線與程式碼區塊的渲染及樣式。
- Whether verification succeeded or failed: 成功；設計完成需求覆蓋與無 placeholder 自我審查。
- If verification still failed, the failure reason and blocker: 無。
- What the next step should be: Pigo 審閱設計後，建立測試先行實作計畫。
# STATUS_2026-09-22_standard_markdown_preview_plan
- What changes were made: 建立標準 Markdown 預覽的測試先行實作計畫，包含渲染擴充與主題感知樣式。
- Whether verification succeeded or failed: 成功；計畫完成需求覆蓋與無 placeholder 自我審查。
- If verification still failed, the failure reason and blocker: 無。
- What the next step should be: 依 Pigo 指示在既有隔離功能分支直接執行計畫。
# STATUS_2026-09-23_folder_path_and_markdown_preview_merged
- What changes were made: 已合併資料夾複製完整路徑與 Markdown 預覽強化功能至 main，並清理隔離功能分支與工作區。
- Whether verification succeeded or failed: 成功；在正確專案目錄執行完整 pytest，27 項全數通過。
- If verification still failed, the failure reason and blocker: 無；曾誤從 Documents 根目錄執行 pytest 而掃到 Agent 的相依套件缺失，已於正確專案目錄重跑通過。
- What the next step should be: 重新啟動 Pigo Notes App，並進行右側預覽字型選擇功能設計。

# STATUS_2026-09-23_preview_font_family_merged
- What changes were made: 已新增工具列的原生字型下拉選單，可選擇且保存右側 Markdown 預覽文字字型；左側檔案總管與其他介面字型不變。
- Whether verification succeeded or failed: 成功；在 main 執行完整 pytest，28 項全數通過。
- If verification still failed, the failure reason and blocker: 無。
- What the next step should be: 使用桌面啟動檔重新開啟 App，從 A＋ 後方的字型選單選擇預覽字型。

# STATUS_2026-09-23_preview_font_family_launch_verified
- What changes were made: 已以桌面「啟動 Pigo Notes App」啟動檔重新開啟合併後的 main 版本。
- Whether verification succeeded or failed: 成功；Windows 已偵測到標題為「Pigo Notes App」的執行中視窗。
- If verification still failed, the failure reason and blocker: 無。
- What the next step should be: 從工具列 A＋ 後方的字型下拉選單選擇你要的右側預覽字型。

# STATUS_2026-10-12_single_app_instance_guard
- What changes were made: 在 App 啟動時加入跨程序鎖；第一個實例持鎖執行，之後的啟動會直接結束，避免再開一個視窗。
- Whether verification succeeded or failed: 成功；完整 pytest 29 項通過。從桌面 BAT 重複啟動後，系統只顯示一個 Pigo Notes App 視窗及一個實際 Python App 程序。
- If verification still failed, the failure reason and blocker: 無；Windows 虛擬環境會呈現啟動器與實際解譯器兩個程序，已依視窗標題與實際解譯器路徑確認只有一個 App 實例。
- What the next step should be: 繼續使用桌面「啟動 Pigo Notes App.bat」；重複點擊不會新增視窗。

# STATUS_2026-10-14_app_opened
- What changes were made: 透過桌面啟動 BAT 重新開啟 Pigo Notes App。
- Whether verification succeeded or failed: 成功；確認一個實際 Python App 視窗標題為「Pigo Notes App」。
- If verification still failed, the failure reason and blocker: 無；首次視窗查詢早於 UI 建立完成，稍後重新確認成功。
- What the next step should be: 可直接使用目前開啟的 Pigo Notes App。

# STATUS_2026-10-14_multi_select_delete_and_position
- What changes were made: 檔案總管支援 Ctrl/Shift 多選；按 Delete 顯示確認清單後，可一次將選取項目送入資源回收筒。若同時選到資料夾及其子項，只處理資料夾；刪除批次只呼叫一次 PowerShell、只刷新一次，並盡量保留原資料夾展開狀態及刪除列附近的捲動位置。
- Whether verification succeeded or failed: 成功；完整 pytest 35 項通過，compileall 與 git diff --check 通過。pytest 有一則既有快取目錄權限警告，不影響測試結果。已透過桌面 BAT 啟動 App，確認僅一個實際 Python App 程序並有主視窗 handle。
- If verification still failed, the failure reason and blocker: 無；未對正式 Vault 實際執行刪除，以免測試期間改動使用者資料。
- What the next step should be: 在檔案總管用 Ctrl/Shift 選取測試項目，按 Delete 檢查確認視窗；取消應不變更資料，確認後項目送入資源回收筒且位置留在原資料夾附近。

# STATUS_2026-10-19_app_and_entrypoint_opened
- What changes were made: 透過桌面 BAT 啟動 Pigo Notes App，並將 Python 主程式入口 app.py 開啟於 Codex 編輯面板。
- Whether verification succeeded or failed: 部分成功；BAT 已執行且看到虛擬環境啟動器與一個 Python 解譯器程序；app.py 開啟請求已排入 Codex 面板。但本次查詢時主視窗 handle 為 0，無法確認 App 視窗已顯示。
- If verification still failed, the failure reason and blocker: App 視窗可見狀態未能驗證；程序存在但沒有可讀取的主視窗 handle。
- What the next step should be: 若畫面仍未顯示，請回覆「程式沒出現」，我會繼續檢查啟動狀態；主程式碼可在 Codex 面板查看。

# STATUS_2026-10-19_app_window_activated
- What changes were made: 依 Pigo 回報進行唯讀啟動診斷，確認 Pigo Notes App 的 Qt 主視窗已建立且可見，並透過 Windows AppActivate 將其重新啟用；未修改程式碼或 BAT。
- Whether verification succeeded or failed: 成功；找到標題為「Pigo Notes App」的可見主視窗，尺寸約 1194×818，AppActivate 回報成功。Get-Process 回報的主視窗 handle 實際指向 50×50 輸入法浮層，因此之前的視窗檢查方式不可靠。
- If verification still failed, the failure reason and blocker: 無；此環境無法直接擷取使用者桌面畫面，因此仍需 Pigo 確認視窗是否已出現在前景。
- What the next step should be: 請確認畫面上是否已看到 Pigo Notes App；若仍沒有，提供目前桌面截圖或回覆「仍沒出現」，再調查視窗所屬桌面／顯示器狀態。

# STATUS_2026-10-19_app_activation_root_cause
- What changes were made: 依 Pigo 回報繼續唯讀診斷。確認主視窗已存在，但單一實例鎖定失敗時 app.py 直接結束，沒有通知既有實例喚回；此外 Codex 終端使用不同 Windows 帳號，無法可靠控制 Pigo 的桌面前景視窗。
- Whether verification succeeded or failed: 根因調查完成；程序與 Qt 視窗存在、視窗位置在主螢幕範圍內。未修改程式碼或啟動檔。
- If verification still failed, the failure reason and blocker: 視窗仍未能在 Pigo 畫面上確認；可靠修復需要新增單一實例間的喚回通知，等待 Pigo 核准計畫。
- What the next step should be: Pigo 確認後，先寫喚回行為測試，再實作單一實例 IPC 喚回與完整測試；不更動 Vault 或 BAT。

# STATUS_2026-10-19_app_window_brought_forward
- What changes were made: 依 Pigo 要求操作現有 App 視窗：還原視窗並呼叫 SetWindowPos/BringWindowToTop 將其移至 Z-order 前方；未修改檔案或程式碼。
- Whether verification succeeded or failed: 部分成功；Windows 回報視窗可見、尺寸 1194×818，還原與移至前方呼叫成功。
- If verification still failed, the failure reason and blocker: Windows 拒絕 SetForegroundWindow，且 Codex 與 App 使用不同 Windows 帳號，無法驗證 Pigo 桌面上是否真的顯示於最前方。
- What the next step should be: 請 Pigo 確認目前畫面是否看得到 App；若仍看不到，需改由 Pigo 帳號互動式桌面重新啟動或核准新增單一實例喚回機制。

# STATUS_2026-10-19_app_closed_for_manual_launch
- What changes were made: 依 Pigo 要求，對已識別的 Pigo Notes App 主視窗送出正常關閉訊息。
- Whether verification succeeded or failed: 成功；Windows 接受關閉訊息，並確認 App 的實際 Python 程序已結束。
- If verification still failed, the failure reason and blocker: 無。
- What the next step should be: Pigo 可從自己的 Windows 桌面手動啟動 BAT；若仍無法開啟，回報錯誤訊息或截圖以便追查。

# STATUS_2026-10-20_vault_folder_selection_and_granite_review
- What changes were made: 新增工具列 Vault 資料夾選擇；選擇有效資料夾後立即切換檔案樹、清除舊筆記預覽、替換 Vault 與資源回收服務，並保存路徑供下次啟動還原。啟動時若已存 Vault 路徑有效便載入；失效時保留預設 Vault。確認 Granite 為公開空 repo，保留現有 origin，並新增 granite remote。
- Whether verification succeeded or failed: 成功；新增測試先按測試邊界確認紅燈，再實作；完整 pytest 39 項通過，compileall 與 git diff --check 通過。
- If verification still failed, the failure reason and blocker: 未發現程式測試失敗。尚未推送至 Granite：目前本機提交歷史含有 Windows 使用者目錄與 Vault 絕對路徑，推送到公開 repo 會一併公開；需先由 Pigo 選擇接受現有歷史公開，或改採不帶舊歷史的乾淨初始提交。
- What the next step should be: Pigo 確認公開歷史處理方式後，再檢查明確上傳清單、提交並推送；STATUS_ALL.md、Vault 資料、執行環境及快取不應上傳。

# STATUS_2026-10-20_granite_commit_created_push_blocked
- What changes were made: 將已核對的 9 個程式與測試檔案提交為 0a910b0；新增 granite remote，保留 origin。STATUS_ALL.md 與三份內部計畫文件未加入提交。
- Whether verification succeeded or failed: 程式驗證成功；完整 pytest 39 項通過，commit 前檢查差異無空白錯誤。推送驗證失敗，GitHub 未收到提交。
- If verification still failed, the failure reason and blocker: 此環境目前可見的 SSH 身份只有 Lumentum 專用別名，沒有 Granite 帳號身份；GitHub CLI 的現有登入憑證亦已失效，SSH 回覆 Permission denied (publickey)。未讀取或輸出任何私密金鑰，亦未跳過主機驗證。
- What the next step should be: Pigo 在 Windows 使用 Granite 帳號配置並驗證專用 SSH key（或重新登入 GitHub CLI）；之後以同一提交重試推送到 granite/main，不需重新提交。

# STATUS_2026-10-20_granite_main_pushed
- What changes were made: 使用已驗證登入 Pigohsiao 的 id_ed25519_pigohsiao_lumentum key（僅限本次命令指定，未修改 SSH 設定），將 main 與完整既有提交歷史推送至 git@github.com:Pigohsiao/Granite.git；保留舊 origin。提交 0a910b05d24a53890689285f88c00a03073f6254 已同步至 granite/main。
- Whether verification succeeded or failed: 成功；遠端 refs/heads/main SHA 與本機 main 相同。推送內容包含 9 個程式與測試檔案；STATUS_ALL.md、Vault 資料、虛擬環境、快取與三份內部計畫文件未上傳。推送前完整 pytest 39 項通過。
- If verification still failed, the failure reason and blocker: 無推送阻礙。工作目錄仍有先前 pytest 臨時資料夾與三份內部計畫文件未追蹤，均保留在本機且不影響遠端同步。
- What the next step should be: 可從 https://github.com/Pigohsiao/Granite 查看程式；若要讓未來 push 自動採用這把 key，可另行設定 Granite SSH host alias，本次沒有變更使用者 SSH 設定。
# STATUS_2026-11-10_indexed_reader_plan

- What changes were made: GPT-6-ASTRA reviewed the Granite/Pigo Notes App design and produced a staged implementation plan for indexed search, wikilink/backlink navigation, recent reading, read-only Properties, and tag filtering. The plan specifies a separate GPT-6-Luna QA subagent and a 96/100 minimum score with mandatory safety gates.
- Whether verification succeeded or failed: Documentation-only plan was reviewed for scope, file ownership, testable behaviors, and acceptance criteria; no application tests were run because no application code changed.
- If verification still failed, the failure reason and blocker: None for planning. Implementation and QA are pending.
- What the next step should be: Give the plan to GPT-6-Luna to implement test-first, then assign a fresh GPT-6-Luna subagent to independently verify the result and score it.

# STATUS_2026-11-10_reader_test_isolation

- What changes were made: Changed the application smoke test to use a tmp_path-only synthetic Vault and added shared Qt/test Vault fixtures plus read-only preview contract tests. Fixed failed note opens so a missing file leaves the current note and preview unchanged.
- Whether verification succeeded or failed: TDD red/green verified. The real-default-Vault guard failed as intended before the smoke test was isolated; the failure-preservation test failed because current_note changed before read, then passed after the minimal fix. Smoke, reader contract, and main-window regression tests passed: 24 passed.
- If verification still failed, the failure reason and blocker: None in this stage. Full-suite baseline has not yet been run; tests/test_config.py compares the default path as a string only and does not access the Vault.
- What the next step should be: Continue Task 1 with metadata/link parser tests first, then implement the parser using only stdlib YAML-safe parsing unless a reviewed dependency is necessary.

# STATUS_2026-11-10_safe_note_parser

- What changes were made: Added typed reader/index records and a standard-library-only NoteParser for bounded frontmatter, properties, tags, and wikilinks. Markdown preview now hides valid frontmatter and relationship extraction ignores code and HTML comments. No dependency was added.
- Whether verification succeeded or failed: TDD red/green verified. Parser suite: 7 passed. Markdown parser/rendering, preview contract, smoke, and existing main-window tests: 36 passed. Invalid YAML, object tags/aliases, excessive frontmatter size/indentation, and metadata-in-code cases are covered.
- If verification still failed, the failure reason and blocker: None for Task 1. Parser intentionally supports a documented safe YAML subset rather than the full YAML specification; unsupported syntax remains visible and reports a warning.
- What the next step should be: Implement the per-Vault SQLite index and deterministic safe link resolver, beginning with tests for incremental refresh, isolation, ambiguity, and unsafe targets.

# STATUS_2026-11-10_vault_index_and_link_resolver

- What changes were made: Added a per-canonical-Vault SQLite cache for searchable text, content fingerprints, Properties, tags, and resolved wikilinks; incremental refresh avoids rereading unchanged notes, and safe resolver outcomes distinguish resolved, missing, ambiguous, and rejected links. Hidden/system folders and symlink/junction directories are excluded. Index database paths inside a Vault are rejected.
- Whether verification succeeded or failed: TDD red/green verified. Resolver and index tests plus all existing service tests, smoke, preview-contract, and main-window tests passed: 56 passed. Coverage includes literal SQL metacharacters, Chinese, no-change refresh read count, changed-file-only reads, removal, unreadable-file retention, cancellation rollback, Vault identity, and path escape rejection.
- If verification still failed, the failure reason and blocker: No test failures remain in this stage. Ruling: full refresh uses one SQLite transaction with rollback instead of building a second temporary database and replacing the live file; this preserves the last committed index on cancellation/failure and avoids Windows open-file replacement races. Cost if wrong: a rebuild holds a write transaction for its duration.
- What the next step should be: Add background controller tests first, then wire asynchronous indexing, search/context responses, session/request IDs, cancellation, coalescing, and orderly shutdown.

# STATUS_2026-11-10_background_index_controller

- What changes were made: Added a Qt background controller using worker-pool jobs and per-job SQLite services, per-Vault hashed app-data index paths, session/request filtering, refresh coalescing, Vault-switch cancellation, selected-note upsert from already-read content, visible index status, and orderly worker joining when the window closes. Vault switches now start a new index session.
- Whether verification succeeded or failed: TDD red/green verified for background UI responsiveness, stale response rejection across Vault switches and newer queries, refresh coalescing, worker shutdown, window startup/switch session wiring, and all associated UI/read-only contracts. Targeted controller, main-window, smoke, and reader-contract tests passed: 30 passed.
- If verification still failed, the failure reason and blocker: None for this stage. Full end-to-end UI features remain in Tasks 4–6.
- What the next step should be: Build the left-pane file/search/recent/tag navigation and debounced indexed search, keeping result activation from changing the file tree's expansion or scroll state.

# STATUS_2026-11-11_luna_qa_review

- What changes were made: GPT-6-Luna completed an independent, read-only QA review of the current Granite worktree against the indexed-reader plan. No source files were modified. QA score: 47/100; result: FAIL (required 96/100 and all hard gates).
- Whether verification succeeded or failed: Verification failed. Full suite: 76 tests, 72 passed and 4 failed, exit code 1. Precision rerun: the same 4 failures. Failed behaviors cover wikilink preview routing, missing safe route handler, and two initial-index refresh timeouts. The preview also permits unrestricted external-link opening, failing a security hard gate.
- If verification still failed, the failure reason and blocker: Safe wikilink routing/backlinks are incomplete; initial refresh wait is unstable; URL schemes are not restricted; tag filter, recent-reading/Properties UI, performance evidence, and README documentation remain incomplete. These prevent passing the safety gates and 96-point threshold.
- What the next step should be: Have the implementation agent address URL scheme restrictions and wikilink/backlink routing first, diagnose refresh timeouts, complete deferred reader UI/docs/performance tests, then rerun the complete test suite and request a fresh independent Luna QA review.

# STATUS_2026-11-11_reader_qa_fixes_and_features

- What changes were made: Completed the indexed reader work prompted by the failed independent QA: safely render and route wikilinks; reject unsupported/dangerous schemes and embedded resource loading; show indexed backlinks and read-only Properties; add tag browsing/filter clearing, recent notes, back/forward history, and debounced per-note scroll-position persistence. Fixed SQLite connection closure on Windows, indexed link candidate lookups to avoid O(n²) refresh behavior, indexed backlink queries and capped displayed backlinks at 100. Updated README and added a synthetic 10,000-note performance benchmark. Preserved existing untracked plans; did not stage, commit, or push.
- Whether verification succeeded or failed: Focused reader/index tests passed (33 passed); full suite passed (85 passed in 47.68s). 10,000-note synthetic benchmark passed: search p95 18.13 ms, backlinks p95 9.48 ms, note read+render p95 73.05 ms. Only temporary test Vaults were used.
- If verification still failed, the failure reason and blocker: None in automated checks. Manual Windows interaction checks and independent fresh GPT-6-Luna QA score are pending; the task is not declared successful until Luna returns at least 96/100 with all hard gates passed.
- What the next step should be: Run `git diff --check`, inspect the complete final diff, then request a fresh independent GPT-6-Luna QA review against `docs/superpowers/plans/2026-11-10-indexed-reader-workspace.md`; address any findings and rerun tests before handoff.

# STATUS_2026-11-11_reader_regression_and_scale_fixes

- What changes were made: Changed clicked-wikilink resolution to use the per-Vault SQLite index instead of enumerating Vault files. Recent reading/history/scroll entries now discard deleted or unsafe paths and recover from malformed history state. Added UI and service regressions for Properties, deletion cleanup, corrupt state, and back/forward navigation.
- Whether verification succeeded or failed: Full suite passed: 88 passed in 49.14s. Latest synthetic 10k benchmark passed: search p95 20.88 ms, backlinks p95 8.20 ms, note read+render p95 6.91 ms. `git diff --check` was clean before these latest small patches; rerun pending.
- If verification still failed, the failure reason and blocker: No automated failures. Fresh GPT-6-Luna QA is still in progress; the required score is at least 96/100 and every plan hard gate must pass.
- What the next step should be: Rerun diff validation, receive the independent Luna review of the latest worktree, then fix any findings and verify again before marking the work complete.

# STATUS_2026-11-10_core_reader_slice_in_progress

- What changes were made: Added the temporary-Vault smoke/test fixtures, safe metadata and wikilink parser, SQLite index and resolver, background controller, and file/search navigation with indexed search. Kept scope limited to core reader work; recent/Properties/tag UI is deferred. Added regression coverage for background refresh completion and began Task 5 link/backlink UI tests.
- Whether verification succeeded or failed: The latest complete search/navigation-panel regression run passed 33 tests. Parser/index/backend suites previously passed 56 tests. A real-index controller regression passed once in 6.12 seconds, but subsequent runs were intermittent/long-running; the new link navigation tests currently fail because the route/backlink UI is not implemented yet, and initial-index completion was not reliable in those runs.
- If verification still failed, the failure reason and blocker: Core slice is incomplete. A pytest rerun command was interrupted after the execution tool stopped responding; the tool later reported its exec cell was stale, so process termination could not be confirmed from that handle.
- What the next step should be: Confirm no pytest process remains, stabilize and test Qt background refresh completion, then finish safe wikilink routing/backlinks, run the synthetic-Vault regression suite, document deferred scope and actual results, and request independent Luna QA separately.

# STATUS_2026-11-24_sol_detailed_markdown_table_plan

- What changes were made: 建立 Markdown 表格預覽修正的詳細計畫文件，交接範圍包含根因定位、RED/GREEN 測試、單行表格誤判防護、UI 條件分支、合成 Vault 驗證、完整回歸與獨立 Luna QA。未修改程式碼、測試或真實 Vault。
- Whether verification succeeded or failed: 計畫文件已寫入；已檢查目標專案存在及原有工作樹狀態，確認既有大量 dirty/untracked 變更並將其列為保護項目。尚未執行程式測試，因本階段只交付計畫。
- If verification still failed, the failure reason and blocker: 無測試失敗；計畫文件仍待 Pigo 核准，Luna 尚未開始實作。
- What the next step should be: 將計畫文件交給 GPT-6-Luna 審讀待命；Pigo 確認計畫後再授權 Luna 修改，完成後交獨立 GPT-6-Luna QA。

# STATUS_2026-11-24_luna_plan_handoff

- What changes were made: 將詳細修正計畫文件交給 GPT-6-Luna 只讀審閱，明確要求在 Pigo 核准前不得修改程式或其他檔案。
- Whether verification succeeded or failed: Handoff 已送出；Luna 審閱回覆尚未完成。程式碼保持未修改。
- If verification still failed, the failure reason and blocker: 無；目前等待 Luna 審閱與 Pigo 對計畫文件的核准。
- What the next step should be: 收到 Luna 審閱後提供計畫文件給 Pigo 確認；確認前不開始實作。

# STATUS_2026-11-24_plan_column_count_clarification

- What changes were made: 依 Pigo 確認的四欄規格，修正計畫文件欄數描述；將欄數一致的四欄格式列為正向測試，將原始五欄 delimiter 範例列為不得猜測或自動修復的保護測試。未修改程式碼或測試。
- Whether verification succeeded or failed: 文件已更新；尚未執行程式測試（本次為計畫文件調整），待 GPT-6-Luna 複核更新版本。
- If verification still failed, the failure reason and blocker: 無；實作仍待 Luna 複核及 Pigo 明確核准。
- What the next step should be: 請 Luna 只讀複核更新後的計畫；之後由 Pigo 核准再開始實作。

# STATUS_2026-11-24_plan_fixture_precision

- What changes were made: 依 Luna 複核意見，在計畫中補上欄數一致的四欄完整壓縮測試字串，明確區分正向 fixture 與原始五欄分隔列負向保護案例。未修改程式碼或測試。
- Whether verification succeeded or failed: 文件補充完成，待 Luna 快速只讀確認；未執行程式測試（目前仍是計畫階段）。
- If verification still failed, the failure reason and blocker: 無；實作仍待計畫最終確認及 Pigo 核准。
- What the next step should be: 請 Luna 確認 fixture 欄數明確且其餘計畫可執行，再交 Pigo 核准後才進入實作。

# STATUS_2026-11-24_markdown_table_fix_started

- What changes were made: Pigo 確認預期四欄，並將目標更新為完成程式修正與 QA 至少 90 分；已把更新後計畫交 GPT-6-Luna 開始依 TDD 實作。未由主代理修改程式碼。
- Whether verification succeeded or failed: 實作已派出，尚無測試結果；已知目標服務、UI 與測試檔在本任務開始前即存在 dirty changes，已要求 Luna 保護既有差異並只做最小修正。
- If verification still failed, the failure reason and blocker: 尚無測試失敗資料；等待 Luna 的實作與驗證結果。
- What the next step should be: 收到 Luna 實作結果後檢視變更與完整測試，再由獨立 GPT-6-Luna QA 評分；若低於 90，最多要求 Luna 修正並重測三輪。

# STATUS_2026-11-24_render_only_four_column_ruling

- What changes were made: 根據 Pigo 確認的四欄語義修正計畫：精確的單行格式由粗體標題、四個表頭、五段 delimiter、四個資料格組成；允許只在 render-time 正規化多餘 delimiter，不修改來源 Markdown。已要求 Luna 暫停並保留當前工作樹，等待依修訂計畫繼續。
- Whether verification succeeded or failed: 修訂計畫已寫入；尚無程式測試結果。原始程式 dirty files 均要求保留。
- If verification still failed, the failure reason and blocker: 無；等待 Luna 回報暫停時已完成的工作，再按修訂計畫執行。
- What the next step should be: 確認 Luna 未覆蓋既有變更，重新派發精確四欄 render-time 正規化與回歸測試；完成後進入獨立 QA，至少 90 分，最多修正三輪。

# STATUS_2026-11-24_compact_table_implementation_qa_round1

- What changes were made: Luna 在 `MarkdownService` 增加只作用於 render-time 的單行表格正規化，並補服務層 table parsing 與誤判保護測試。保留來源 Markdown 與其他既有工作樹變更；沒有 stage/commit/push，沒有碰 Vault。
- Whether verification succeeded or failed: 實作者回報完整 pytest 96 passed、合成 UI 預覽呈現 2 列 4 欄、`git diff --check` exit code 0；獨立 GPT-6-Luna QA Round 1 已啟動，尚未完成。
- If verification still failed, the failure reason and blocker: 無已知測試失敗；尚待獨立 QA 驗證與評分。
- What the next step should be: 收到 QA 評分與 hard-gate 檢查；若低於 90 或任一硬門檻失敗，退回 Luna 修正後重跑測試並重新 QA，最多三輪。

# STATUS_2026-11-24_markdown_table_fix_qa_pass

- What changes were made: 完成 Markdown 預覽壓縮單行表格修正：`MarkdownService` 在記憶體渲染流程中將確認的四欄格式正規化，保留表外粗體標題及來源文字；加入標準多行、使用者案例、一般 pipe 文字、程式碼、escaped pipe 與欄數不合的服務測試。未修改真實 Vault，未 stage/commit/push。
- Whether verification succeeded or failed: GPT-6-Luna 獨立 QA Round 1 評分 94/100，PASS（門檻 90）。服務測試 15 passed、UI 測試 21 passed、完整 pytest 96 passed（exit 0）、QTextDocument 合成案例 2 列 4 欄斷言通過、`git diff --check` exit 0。
- If verification still failed, the failure reason and blocker: 無阻擋項。QA 次要建議是未來可補持續性的 QTextBrowser 表格 UI 回歸測試；本次根因位於 renderer，該項不阻擋通過。
- What the next step should be: 本次修正與 QA 達標；若未來要求更高的 UI 回歸覆蓋，再另案補上持續性預覽整合測試。保留既有未提交工作樹狀態，不推送或提交。

# STATUS_2026-11-24_commit_push_scope_pending

- What changes were made: 檢查 commit/push 前的工作樹與 Git 遠端；確認位於 main、origin 指向 Pigo-granite，且除表格修正外仍有 reader/index 功能、測試與文件等未提交變更。未暫存、提交或推送任何內容。
- Whether verification succeeded or failed: 分支與遠端資訊已確認；未執行 Git 寫入操作。
- If verification still failed, the failure reason and blocker: commit/push 範圍尚未確認；直接推送所有變更會包含先前未提交功能，而只推表格修正需採用精確部分暫存。
- What the next step should be: 等 Pigo 選擇只提交表格修正，或提交目前所有已完成的專案變更，再按指定範圍驗證並 push。

# STATUS_2026-11-24_full_project_commit_push_authorized

- What changes were made: Pigo 明確核准將目前專案所有實際變更一併 commit/push。預定納入程式碼、測試、計畫/專案文件及 STATUS_ALL.md；產生的測試暫存、快取與工具輸出仍排除。
- Whether verification succeeded or failed: 尚未暫存、提交或推送；正在進行提交前完整測試與內容清查。
- If verification still failed, the failure reason and blocker: 無；若完整測試失敗或發現敏感資料/非預期產物，先停止推送並回報。
- What the next step should be: 完整 pytest 與 diff/內容檢查通過後，納入所有已授權內容 commit 到 main 並 push origin，最後確認遠端 HEAD。

# STATUS_2026-11-24_precommit_performance_rerun

- What changes were made: 提交前全套測試首次執行為 95 passed、1 failed；唯一失敗是既有 10k synthetic backlinks p95 短暫量得 120.81 ms（門檻 100 ms）。未修改程式或測試門檻。
- Whether verification succeeded or failed: 單獨重跑 `tests/performance/test_reader_performance.py` 通過，backlinks p95 35.69 ms；完整套件仍需重跑一次確認。
- If verification still failed, the failure reason and blocker: 首次全套結果有一個效能波動失敗；尚未證明全套穩定通過。
- What the next step should be: 再跑完整 pytest；若全綠，再檢查 diff/提交清單並 commit/push；若再次超標，停止推送並調查效能波動。
